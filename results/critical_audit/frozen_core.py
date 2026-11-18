from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import uniform_filter1d

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'Student folder'
FEATURES = ['distance_m', 'heading_cos', 'heading_abs_sin', 'log_length',
            'fraction', 'prev_distance_m', 'next_distance_m', 'speed_mps',
            'gap_s', 'distance_rank', 'distance_margin_m', 'heading_reliability',
            'source_degree', 'target_degree', 'endpoint_distance_m']

@dataclass
class Trip:
    id: str
    partition: str
    nodes: np.ndarray
    arcs: np.ndarray
    track: np.ndarray
    xy: np.ndarray
    gps: np.ndarray
    start: np.ndarray
    delta: np.ndarray
    length: np.ndarray
    graph: csr_matrix
    origin: np.ndarray
    scale: np.ndarray

    def unproject(self, xy):
        return np.asarray(xy) / self.scale + self.origin

def load_trip(path: Path) -> Trip:
    tid = path.name
    nodes = np.loadtxt(path / f'{tid}.nodes', ndmin=2)
    arcs = np.loadtxt(path / f'{tid}.arcs', dtype=np.int32, ndmin=2)
    track = np.loadtxt(path / f'{tid}.track', ndmin=2)
    if min(len(nodes),len(arcs),len(track))<1:
        raise ValueError('GPS and road files must not be empty')
    if nodes.shape[1] != 2 or arcs.shape[1] != 2 or track.shape[1] != 3:
        raise ValueError('Unexpected raw file columns')
    if not np.isfinite(nodes).all() or not np.isfinite(track).all():
        raise ValueError('Non-finite coordinates or timestamps')
    if np.any(np.abs(nodes)>[180,90]) or np.any(np.abs(track[:,:2])>[180,90]):
        raise ValueError('Longitude/latitude outside valid geographic ranges')
    if arcs.min() < 0 or arcs.max() >= len(nodes):
        raise ValueError('Invalid node index')
    if np.any(np.diff(track[:, 2]) <= 0):
        raise ValueError('GPS timestamps must be strictly increasing; resolve duplicates before inference')
    origin = nodes.mean(axis=0)
    scale = np.array([111195.08 * np.cos(np.deg2rad(origin[1])), 111195.08])
    xy = (nodes - origin) * scale
    gps = (track[:, :2] - origin) * scale
    start = xy[arcs[:, 0]]
    delta = xy[arcs[:, 1]] - start
    length = np.maximum(np.linalg.norm(delta, axis=1), 0.01)
    # Collapse parallel directed node pairs with MIN length, never sparse-matrix summation.
    pairs, ix = np.unique(arcs, axis=0, return_index=True)
    graph = csr_matrix((length[ix], (pairs[:, 0], pairs[:, 1])), shape=(len(nodes), len(nodes)))
    return Trip(tid, path.parent.name, nodes, arcs, track, xy, gps, start, delta, length, graph, origin, scale)

def motion(trip):
    smooth = uniform_filter1d(trip.gps, size=5, axis=0, mode='nearest')
    vector = np.gradient(smooth, axis=0) if len(smooth)>1 else np.zeros_like(smooth)
    norm = np.linalg.norm(vector, axis=1)
    heading = vector / np.maximum(norm[:, None], 1e-6)
    dt = np.r_[1., np.diff(trip.track[:, 2])]
    speed = np.r_[0., np.linalg.norm(np.diff(trip.gps, axis=0), axis=1)] / dt
    reliability = np.clip(norm / 4., 0, 1)
    return heading, dt, speed, reliability

def project(points, start, delta):
    fraction = np.clip(np.sum((points - start) * delta, axis=-1) / np.maximum(np.sum(delta * delta, axis=-1), 1e-8), 0, 1)
    foot = start + fraction[..., None] * delta
    return fraction, np.linalg.norm(points - foot, axis=-1), foot

def candidates(trip: Trip, k=8, strategy='nearest'):
    k=min(k,len(trip.arcs))
    if k<1:raise ValueError('Road network contains no usable segments')
    headings,_,_,reliable=motion(trip)
    # Densification avoids midpoint-only retrieval missing long road segments.
    count = np.maximum(1, np.ceil(trip.length / 25).astype(int))
    owners = np.repeat(np.arange(len(count)), count)
    offsets = np.arange(count.sum()) - np.repeat(np.cumsum(count) - count, count)
    alpha = (offsets + .5) / np.repeat(count, count)
    anchors = trip.start[owners] + alpha[:, None] * trip.delta[owners]
    tree = cKDTree(anchors)
    _, idx = tree.query(trip.gps, k=min(96, len(anchors)), workers=-1)
    proposal = owners[idx]
    ids = np.empty((len(trip.gps), k), dtype=np.int32)
    for i, row in enumerate(proposal):
        unique = np.unique(row)
        _, dist, _ = project(trip.gps[i], trip.start[unique], trip.delta[unique])
        if strategy=='adaptive':
            direction=trip.delta[unique]/trip.length[unique,None]
            score=dist+18*reliable[i]*(1-direction@headings[i])
            selected=unique[np.argsort(score,kind='stable')[:k]]
            _,chosen_distance,_=project(trip.gps[i],trip.start[selected],trip.delta[selected])
            selected=selected[np.argsort(chosen_distance,kind='stable')]
        elif strategy=='nearest':selected = unique[np.argsort(dist, kind='stable')[:k]]
        else:raise ValueError('Unknown candidate strategy')
        if len(selected) < k:
            # Expand retrieval rather than duplicating candidate identities.
            _, expanded = tree.query(trip.gps[i], k=min(len(anchors), 512))
            unique = np.unique(owners[np.atleast_1d(expanded)])
            _, dist, _ = project(trip.gps[i], trip.start[unique], trip.delta[unique])
            selected = unique[np.argsort(dist, kind='stable')[:k]]
        if len(selected) < k:
            raise ValueError('Road network has fewer distinct candidates than requested')
        ids[i] = selected
    start, delta = trip.start[ids], trip.delta[ids]
    fraction, dist, foot = project(trip.gps[:, None, :], start, delta)
    heading, dt, speed, reliability = motion(trip)
    direction = delta / trip.length[ids, None]
    cos = np.sum(direction * heading[:, None, :], axis=-1)
    prev = np.vstack([trip.gps[0], trip.gps[:-1]])
    nxt = np.vstack([trip.gps[1:], trip.gps[-1]])
    _, prev_dist, _ = project(prev[:, None, :], start, delta)
    _, next_dist, _ = project(nxt[:, None, :], start, delta)
    deg = np.bincount(trip.arcs.ravel(), minlength=len(trip.nodes))
    repeat = lambda a: np.broadcast_to(a[:, None], ids.shape)
    features = np.stack([dist, cos, np.sqrt(np.maximum(0, 1-cos*cos)),
                         np.log1p(trip.length[ids]), fraction, prev_dist, next_dist,
                         repeat(speed), repeat(dt), np.broadcast_to(np.arange(k), ids.shape),
                         dist-dist[:, :1], repeat(reliability),
                         deg[trip.arcs[ids, 0]], deg[trip.arcs[ids, 1]],
                         np.minimum(fraction, 1-fraction)*trip.length[ids]], axis=-1)
    return {'ids': ids, 'X': features.astype(np.float32), 'fraction': fraction.astype(np.float32),
            'distance': dist.astype(np.float32), 'foot': foot.astype(np.float32),
            'dt': dt, 'speed': speed, 'reliability': reliability}

def reference_labels(trip: Trip, path: Path):
    """Weak point labels from monotone alignment to the supplied route.

    These are derived references, NOT independent evaluator point labels.
    DP allows staying or advancing, penalizes forward distance, and uses geometry
    and directed heading. It never feeds route information into candidate features.
    """
    route = np.loadtxt(path / f'{trip.id}.route', dtype=int, ndmin=1)
    if route.min() < 0 or route.max() >= len(trip.arcs):
        raise ValueError('Invalid reference arc index')
    heading, _, _, reliability = motion(trip)
    direction = trip.delta[route] / trip.length[route, None]
    progress = np.r_[0, np.cumsum(trip.length[route])[:-1]]
    previous = progress * .002
    back = np.empty((len(trip.gps), len(route)), dtype=np.int32)
    indices = np.arange(len(route))
    distances = []
    for t, point in enumerate(trip.gps):
        _, dist, _ = project(point, trip.start[route], trip.delta[route])
        costs = np.minimum(dist, 300) + 8 * reliability[t] * (1-direction @ heading[t])
        adjusted = previous - .015*progress
        minimum = np.minimum.accumulate(adjusted)
        winner = np.maximum.accumulate(np.where(adjusted <= minimum, indices, 0))
        back[t] = winner
        previous = costs + minimum + .015*progress
    pos = int(np.argmin(previous))
    alignment = np.empty(len(trip.gps), dtype=np.int32)
    for t in range(len(trip.gps)-1, -1, -1):
        alignment[t] = pos
        pos = back[t, pos]
    labels = route[alignment]
    _, distance, _ = project(trip.gps, trip.start[labels], trip.delta[labels])
    return labels.astype(np.int32), distance.astype(np.float32), route

def inventory(trip, path):
    route = np.loadtxt(path/f'{trip.id}.route', dtype=int, ndmin=1)
    gaps = np.diff(trip.track[:, 2])
    components, _ = connected_components(trip.graph, directed=True, connection='weak')
    return {'trip_id':trip.id, 'partition':trip.partition, 'observations':len(trip.track),
            'nodes':len(trip.nodes), 'arcs':len(trip.arcs), 'route_arcs':len(route),
            'missing_values':int(np.isnan(trip.track).sum()), 'max_gap_s':float(gaps.max()),
            'irregular_steps':int(np.sum(gaps!=1)), 'weak_components':int(components),
            'isolated_nodes':int(np.sum((trip.graph.getnnz(axis=0)+trip.graph.getnnz(axis=1))==0)),
            'lon_min':float(trip.track[:,0].min()),'lon_max':float(trip.track[:,0].max()),
            'lat_min':float(trip.track[:,1].min()),'lat_max':float(trip.track[:,1].max()),
            'route_connected_fraction':float(np.mean(trip.arcs[route[:-1],1]==trip.arcs[route[1:],0])) if len(route)>1 else 1.}
