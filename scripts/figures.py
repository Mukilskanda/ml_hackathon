import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib,folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathsnap.core import ROOT,DATA,load_trip
from pathsnap.service import predict_trip,route_geometry

OUT=ROOT/'results'/'figures'
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,
 'axes.labelcolor':'#183936','text.color':'#183936','axes.titleweight':'bold','figure.facecolor':'#fffef9',
 'axes.facecolor':'#fffef9','savefig.facecolor':'#fffef9','font.size':10})

def save(name):
    plt.tight_layout();plt.savefig(OUT/f'{name}.png',dpi=160,bbox_inches='tight');plt.close()

def main():
    OUT.mkdir(parents=True,exist_ok=True);(ROOT/'results'/'maps').mkdir(exist_ok=True)
    inv=pd.read_csv(ROOT/'results'/'dataset_inventory.csv')
    fig,ax=plt.subplots(1,3,figsize=(11,3))
    ax[0].hist([inv[inv.partition=='train'].observations,inv[inv.partition=='student_test'].observations],bins=14,label=['Train','Student test'],color=['#176d56','#d68d53']);ax[0].set_title('Observations per trip');ax[0].legend(fontsize=8)
    ax[1].scatter(inv.observations,inv.max_gap_s,c=['#176d56' if x=='train' else '#d68d53' for x in inv.partition],s=20);ax[1].set_xlabel('GPS observations');ax[1].set_ylabel('Largest timestamp gap (s)');ax[1].set_title('Sampling anomalies')
    ax[2].hist(inv.reference_over_50m,bins=12,color='#176d56');ax[2].set_xlabel('Fraction of points >50 m from aligned reference');ax[2].set_title('Reference quality');save('dataset_overview')
    models=pd.read_csv(ROOT/'results'/'model_comparison.csv');names=models.model.str.replace('HistGradientBoosting','HistGB').str.replace('LogisticRegression','Logistic').str.replace('RandomForest','Random forest').str.replace('_tuned',' tuned')
    fig,ax=plt.subplots(1,2,figsize=(11,4.5));y=np.arange(len(models))
    ax[0].barh(y-.17,models.cv_macro_f1,.32,color='#a8bca1',label='Grouped CV Macro F1');ax[0].barh(y+.17,models.test_macro_f1,.32,color='#176d56',label='Student-test Macro F1');ax[0].set_yticks(y,names);ax[0].set_xlim(.7,1);ax[0].legend(fontsize=8);ax[0].set_title('Candidate classification')
    ax[1].barh(y,models.test_top1_accuracy,color='#d68d53');ax[1].set_yticks(y,names);ax[1].set_xlim(.7,1);ax[1].set_title('Student-test observation Top-1');save('model_comparison')
    fig,ax=plt.subplots(figsize=(9,3));ax.bar(names,models.test_log_loss,color='#176d56');ax.tick_params(axis='x',rotation=25,labelsize=8);ax.set_ylabel('Binary candidate log loss');ax.set_title('Probability quality (lower is better)');save('log_loss')
    trials=pd.read_csv(ROOT/'results'/'bayesian_trials.csv');fig,ax=plt.subplots(figsize=(9,3));ax.plot(trials.number,trials.value,'o-',color='#176d56',label='Trial objective');ax.plot(trials.number,trials.value.cummax(),'--',color='#d68d53',label='Best so far');ax.set_xlabel('Optuna TPE trial');ax.set_ylabel('Mean(CV Macro F1, CV Top-1)');ax.legend();ax.set_title('Actual Bayesian optimisation history');save('bayesian_history')
    route=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str});fig,ax=plt.subplots(1,2,figsize=(11,3.5))
    for method,color in [('classifier_only','#a8bca1'),('fixed_hmm','#d68d53'),('adaptive_hmm','#71a18a'),('audited_hmm','#176d56')]:
        data=route[route.method==method];ax[0].plot(data.trip_id.str[-2:],data.point_accuracy,'o-',label=method,color=color)
    ax[0].legend(fontsize=8);ax[0].set_xlabel('Student-test trip ID suffix');ax[0].set_ylabel('Derived-reference accuracy');ax[0].set_title('Decoding per trip')
    means=route.groupby('method').point_accuracy.mean();ax[1].barh(means.index,means.values,color='#176d56');ax[1].set_xlim(0,1);ax[1].set_title('Equal-trip mean accuracy');save('route_comparison')
    feature=pd.read_csv(ROOT/'results'/'feature_ablation.csv');fig,ax=plt.subplots(figsize=(9,3));ax.bar(feature.feature_set,feature.test_top1_accuracy,color='#176d56');ax.set_ylim(.4,1);ax.set_ylabel('Student-test Top-1');ax.set_title('Feature ablation, same tuned model configuration');save('feature_ablation')
    cov=pd.read_csv(ROOT/'results'/'candidate_coverage.csv');fig,ax=plt.subplots(figsize=(8,3))
    for part,color in [('train','#176d56'),('student_test','#d68d53')]:
        s=cov[cov.partition==part];ax.plot(s.k,1-s.candidate_miss_rate,'o-',label=part,color=color)
    ax.set_xlabel('Nearest distinct candidates retained');ax.set_ylabel('Derived reference present');ax.legend();ax.set_title('Candidate coverage, full dataset');save('candidate_coverage')
    bins=pd.read_csv(ROOT/'results'/'calibration_bins.csv');fig,ax=plt.subplots(figsize=(5,4))
    ax.plot([0,1],[0,1],'--',color='#bbc8b6')
    for method,color in [('uncalibrated','#176d56'),('calibrated_nested_cv','#d68d53')]:
        s=bins[(bins.method==method)&(bins['count']>0)];ax.plot(s.mean_probability,s.positive_fraction,'o-',label=method,color=color)
    ax.set_xlabel('Mean predicted probability');ax.set_ylabel('Observed candidate-positive fraction');ax.legend(fontsize=8);ax.set_title('Group-aware calibration diagnostic');save('calibration')
    robust=pd.read_csv(ROOT/'results'/'robustness.csv');noise=robust[robust.sample_stride==1].groupby('noise_sigma_m').mean(numeric_only=True);fig,ax=plt.subplots(1,2,figsize=(10,3.5));ax[0].plot(noise.index,noise.classifier_accuracy,'o-',color='#d68d53',label='Classifier');ax[0].plot(noise.index,noise.decoder_accuracy,'o-',color='#176d56',label='Decoded');ax[0].set_xlabel('Added GPS noise sigma (m)');ax[0].set_ylabel('Mean trip accuracy');ax[0].legend();ax[0].set_title('Noise stress test / 3 trips')
    drop=robust[robust.noise_sigma_m==0].groupby('sample_stride').mean(numeric_only=True);ax[1].plot(drop.index,drop.decoder_accuracy,'o-',color='#176d56');ax[1].set_xlabel('Keep every Nth observation');ax[1].set_title('Dropout stress test / 3 trips');save('robustness')
    mlp=joblib.load(ROOT/'artifacts'/'MLP.joblib')[-1];fig,ax=plt.subplots(figsize=(8,3));ax.plot(np.arange(1,len(mlp.loss_curve_)+1),mlp.loss_curve_,color='#176d56');ax.set_xlabel('Training epoch');ax.set_ylabel('Training log loss + regularisation');ax.set_title('Recorded MLP training loss (no validation-loss history)');save('mlp_loss')
    model=joblib.load(ROOT/'artifacts'/'model.joblib');config=json.loads((ROOT/'artifacts'/'decoder.json').read_text());tid='00000007'
    trip,c,p,d,timing=predict_trip(DATA/'student_test'/tid,model,config)
    ref=np.loadtxt(DATA/'student_test'/tid/f'{tid}.route',dtype=int)
    predicted,_=route_geometry(trip,d['arc_ids'],d['resets'])
    ll=lambda coords:np.asarray(coords)[:,::-1].tolist()
    m=folium.Map(location=trip.track[:,:2].mean(axis=0)[::-1],tiles=None,zoom_start=14,control_scale=True)
    folium.TileLayer('OpenStreetMap',name='Optional online basemap',show=False).add_to(m)
    road_layer=folium.FeatureGroup(name='Road network',show=True)
    mid=trip.start+trip.delta*.5
    lo=trip.gps.min(axis=0)-200;hi=trip.gps.max(axis=0)+200
    road_ids=np.flatnonzero(np.all((mid>=lo)&(mid<=hi),axis=1))
    for arc in road_ids:folium.PolyLine(ll(trip.nodes[trip.arcs[arc]]),color='#899589',weight=1,opacity=.5).add_to(road_layer)
    road_layer.add_to(m)
    reference=folium.FeatureGroup(name='Reference route (development only)',show=True)
    for arc in ref:folium.PolyLine(ll(trip.nodes[trip.arcs[arc]]),color='#9984bc',weight=7,opacity=.55).add_to(reference)
    reference.add_to(m)
    predicted_layer=folium.FeatureGroup(name='Predicted HMM route')
    for line in predicted:folium.PolyLine(ll(line),color='#176d56',weight=4).add_to(predicted_layer)
    predicted_layer.add_to(m)
    raw=folium.FeatureGroup(name='Raw GPS observations')
    for i,point in enumerate(trip.track[:,:2]):folium.CircleMarker(point[::-1],radius=2,color='#d68d53',weight=1,fill=True,fill_opacity=.7,tooltip=f'GPS observation {i}').add_to(raw)
    raw.add_to(m);folium.LayerControl(collapsed=False).add_to(m)
    extent=np.vstack([trip.track[:,:2],trip.nodes[trip.arcs[ref]].reshape(-1,2),
                      np.concatenate([np.asarray(line) for line in predicted])])
    m.fit_bounds([[float(extent[:,1].min()),float(extent[:,0].min())],
                  [float(extent[:,1].max()),float(extent[:,0].max())]],padding=(100,100))
    m.get_root().html.add_child(folium.Element('<style>.leaflet-container{background:#edf1e7!important}</style>'))
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:#fffef9;padding:18px;border:1px solid #cbd4c4;font:14px sans-serif"><b>PathSnap / student-test trip 00000007</b><br><span style="color:#d68d53">● Raw GPS</span> &nbsp; <span style="color:#176d56">━ Predicted</span> &nbsp; <span style="color:#9984bc">━ Reference (development)</span></div>'))
    m.save(str(ROOT/'results'/'maps'/'development_trip_00000007.html'))
    fig,ax=plt.subplots(figsize=(10,5.5))
    for arc in np.unique(c['ids']):
        pts=trip.nodes[trip.arcs[arc]];ax.plot(pts[:,0],pts[:,1],color='#d4ddce',linewidth=.5)
    for arc in ref:
        pts=trip.nodes[trip.arcs[arc]];ax.plot(pts[:,0],pts[:,1],color='#9984bc',linewidth=4,alpha=.5)
    for line in predicted:
        pts=np.asarray(line);ax.plot(pts[:,0],pts[:,1],color='#176d56',linewidth=1.8)
    ax.scatter(trip.track[:,0],trip.track[:,1],s=2,color='#d68d53',label='Raw GPS',zorder=4)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.set_aspect(1/np.cos(np.deg2rad(trip.origin[1])));ax.set_title('Trip 00000007 / observed, predicted and reference roads');save('geographic_comparison')
    print('Figures and Folium map generated from actual results.',flush=True)

if __name__=='__main__':main()
