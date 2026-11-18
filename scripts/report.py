"""Build the consolidated report only from saved experiment/evidence files."""
import sys,json,textwrap
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape
from pathsnap.core import ROOT

OUT=ROOT/'output'/'pdf';FIG=ROOT/'results'/'figures';SHOT=ROOT/'results'/'screenshots'
INK=colors.HexColor('#183936');GREEN=colors.HexColor('#176d56');MUTED=colors.HexColor('#64776d');PALE=colors.HexColor('#e9eee1')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitlePS',fontName='Helvetica-Bold',fontSize=42,leading=46,textColor=INK,spaceAfter=20))
styles.add(ParagraphStyle(name='SubPS',fontName='Helvetica',fontSize=16,leading=22,textColor=MUTED,spaceAfter=15))
styles.add(ParagraphStyle(name='H1PS',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=INK,spaceAfter=17))
styles.add(ParagraphStyle(name='H2PS',fontName='Helvetica-Bold',fontSize=12,leading=17,textColor=GREEN,spaceBefore=12,spaceAfter=7))
styles.add(ParagraphStyle(name='BodyPS',fontName='Helvetica',fontSize=9.5,leading=14,textColor=INK,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallPS',fontName='Helvetica',fontSize=8,leading=11,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle(name='CellPS',fontName='Helvetica',fontSize=7.2,leading=10,textColor=INK))
story=[]
def p(text,style='BodyPS'):story.append(Paragraph(text,styles[style]))
def h(text):p(text,'H1PS')
def sub(text):p(text,'H2PS')
def page():story.append(PageBreak())
def fig(name,caption,width=505,maxheight=260):
    path=FIG/name
    if not path.exists():raise FileNotFoundError(path)
    w,hh=ImageReader(str(path)).getSize();scale=min(width/w,maxheight/hh)
    story.append(Image(str(path),w*scale,hh*scale));p(caption,'SmallPS')
def shot(name,caption,maxheight=410):
    path=SHOT/name
    if not path.exists():raise FileNotFoundError(path)
    w,hh=ImageReader(str(path)).getSize();scale=min(505/w,maxheight/hh)
    story.append(KeepTogether([Image(str(path),w*scale,hh*scale),Paragraph(caption,styles['SmallPS'])]))
def table(headers,rows,widths=None):
    cell=lambda x:Paragraph(escape(str(x)),styles['CellPS'])
    data=[[cell(x) for x in headers]]+[[cell(x) for x in row] for row in rows]
    t=Table(data,colWidths=widths or [505/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#c6d4c1')),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#dce5dc')),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(t);story.append(Spacer(1,10))
def pct(x):return f'{100*float(x):.2f}%'
def short(name):return name.replace('HistGradientBoosting','HistGB').replace('LogisticRegression','Logistic').replace('_tuned',' tuned').replace('_adaptive_candidates',' + directional candidates')
def banner(canvas,doc):
    canvas.saveState();w,hh=doc.pagesize
    canvas.setFillColor(INK);canvas.rect(0,hh-7,w,7,fill=1,stroke=0)
    canvas.setFont('Helvetica',8);canvas.setFillColor(MUTED)
    canvas.drawString(43,hh-30,'PATHSNAP / TECHNICAL REPORT')
    canvas.drawRightString(w-43,hh-30,'18 NOVEMBER 2026 / AI-ASSISTED REVIEW DRAFT')
    canvas.setStrokeColor(colors.HexColor('#dce5dc'));canvas.line(43,40,w-43,40)
    canvas.drawString(43,26,'Derived-reference scores; official evaluator scoring not verified')
    canvas.drawRightString(w-43,26,str(doc.page));canvas.restoreState()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'artifacts'/'manifest.json').read_text());decoder=json.loads((ROOT/'artifacts'/'decoder.json').read_text())
    team=json.loads((ROOT/'team.json').read_text());models=pd.read_csv(ROOT/'results'/'model_comparison.csv')
    inventory=pd.read_csv(ROOT/'results'/'dataset_inventory.csv',dtype={'trip_id':str});routes=pd.read_csv(ROOT/'results'/'route_comparison.csv',dtype={'trip_id':str})
    means=routes.groupby('method').mean(numeric_only=True);final=manifest['final_metrics']
    selected_method='audited_hmm' if 'audited_hmm' in means.index else 'adaptive_hmm'
    trials=pd.read_csv(ROOT/'results'/'bayesian_trials.csv');cal=json.loads((ROOT/'results'/'calibration.json').read_text())
    adaptive=json.loads((ROOT/'results'/'adaptive_training.json').read_text());diagnostics=pd.read_json(ROOT/'results'/'training_diagnostics.json')
    api=json.loads((ROOT/'results'/'api_verification.json').read_text());browser=json.loads((ROOT/'results'/'browser_qa.json').read_text())
    modelroute=pd.read_csv(ROOT/'results'/'model_route_metrics.csv').groupby('model').mean(numeric_only=True)
    p('PATHSNAP','TitlePS');p('Recover the road<br/>behind the noise.','SubPS')
    p('Distributed map matching and route reconstruction','H2PS')
    p('UE24CS352A: Machine Learning | PES University, RR Campus')
    story.append(Spacer(1,20));p(escape(team['team_name']),'H1PS')
    table(['Member','USN','Suggested component ownership'],[[m['name'],m['usn'],m['ownership']] for m in team['members']],[150,100,255])
    p('Names and ownership are placeholders at the team\'s request. Replace with actual members and contributions before submission.','SmallPS')
    story.append(Spacer(1,18))
    p(f'<b>Measured development result:</b> {pct(means.loc[selected_method,"point_accuracy"])} equal-trip mean decoded point accuracy across ten student-test trips. The same candidate classifier averages {pct(means.loc["classifier_only","point_accuracy"])} before decoding.')
    p('<b>Scope of this evidence:</b> all point labels are derived from a monotone alignment to the supplied .route sequence. These are not independent pointwise truth or reserved evaluator scores. Decoder settings were selected using permitted student-test data.')
    p('<b>Release status:</b> implementation and local experiments are verifiable in the accompanying source/results. Physical two-laptop rehearsal, public GitHub publication, official scoring confirmation and team interpretation review remain outstanding.')
    p('AI assistance disclosure: source and documentation were developed with AI assistance. Executions, metrics, maps and screenshots are actual outputs. This draft requires team review and event-policy-compliant disclosure.','SmallPS')
    page();h('1 / System and evidence')
    p('PathSnap takes a complete GPS trajectory and its directed road graph, scores candidate road segments, and reconstructs a coherent segment sequence. Candidate classification is binary rather than global arc-ID classification because each trip has a separate road-ID namespace.')
    table(['Stage','Implementation','Evidence'],[
      ['Raw files to candidates','Validated parsers, local metric projection, densified cKDTree segment index','90-trip inventory and candidate coverage'],
      ['Candidate learning','Seven baseline algorithms, trip-grouped CV, 16 TPE trials','Saved configs, fold metrics, models and trial history'],
      ['Sequence inference','Hybrid emissions, directed paths, time-gap constraints, jitter tolerance, Viterbi','Per-trip fixed/adaptive/classifier comparisons'],
      ['Distributed application','FastAPI on model host; separate static browser UI','Ten live API requests and separate-origin browser QA'],
      ['Submission assets','One PDF plus organized Git-ready source and model artifacts','Audit, requirements checklist and handoff ZIPs']],[100,240,165])
    sub('Architecture and reference isolation')
    p('<b>Laptop 2 UI</b> sends a trip ID to <b>Laptop 1 FastAPI</b>. The server loads GPS and graph files, builds features, runs the saved model, decodes the route, then optionally computes metrics with its internal reference. It returns predicted geometry and aggregate metrics. Reference route labels never enter inference or the UI transfer package. A separate comparison endpoint can display the supplied reference geometry in blue after prediction; the predicted path remains green.')
    p('Every POST reruns inference and logs a request ID. No training or hardcoded prediction lookup occurs during a request. A unit test intercepts every inference load and fails if a .route file is opened.')
    sub('What is and is not independently established')
    p('Local geometry, candidate generation, grouped experiments, saved-artifact reload, decoding, HTTP requests and browser behavior have execution evidence. A second physical machine was not available to this run. The separately supplied evaluator files now have a frozen-model replay in the final appendix; no selection was performed on them. No remote public GitHub URL was created. Those items must not be inferred from local success.')
    page();h('2 / Dataset understanding and EDA')
    table(['Partition','Trips','GPS observations','Use'],[[part,len(s),int(s.observations.sum()),use] for part,use in [('train','Fit, CV, optimisation'),('student_test','Development comparison and decoder tuning')] for s in [inventory[inventory.partition==part]]],[110,55,110,230])
    table(['File','Columns / identifiers','Interpretation'],[
      ['.track','Longitude, latitude, timestamp seconds','GPS observations; not rows aligned to route segments'],
      ['.nodes','Longitude, latitude','Zero-based row index is node ID'],
      ['.arcs','Source node ID, target node ID','Directed arc; zero-based row index is arc ID'],
      ['.route','One arc ID per row','Chronological traversed segments; not per-observation truth']],[65,200,240])
    p(f'Total supplied observations: {int(inventory.observations.sum()):,}. Trip sizes range from {int(inventory.observations.min()):,} to {int(inventory.observations.max()):,} observations. The largest observed timestamp gap is {inventory.max_gap_s.max():.0f} seconds. The inventory records {int(inventory.missing_values.sum())} missing GPS values, per-trip graph components, isolated nodes, coordinate extents and reference connectivity. No rows are silently removed from student-test scoring.')
    fig('dataset_overview.png','Full supplied train/student-test partitions. Reference-distance outliers concern derived alignment quality, not proven GPS errors.',maxheight=210)
    page();h('2.1 / Preprocessing and label limitations')
    p('The parser validates dimensions, finite values, node-index bounds and strictly increasing timestamps. Distances use local equirectangular metric coordinates: 111195.08 m per latitude degree and its cosine-latitude-scaled value for longitude. This approximation is intended for local road networks, not global distances. Folium receives latitude/longitude in the correct order.')
    sub('Why .route cannot be used as direct GPS labels')
    p('Reference rows describe traversed segments while many GPS observations can belong to one segment. A monotone dynamic program aligns observations to the reference segment sequence using projected distance, smoothed heading and a small forward-progress penalty. Staying on a segment is permitted. This supplies consistent weak point labels for training and development scoring.')
    p('The alignment is not independent physical truth. It partly uses the same geometry/motion cues as the predictor, so agreement may be optimistic. Incorrect/incomplete references, loops and long gaps can corrupt labels. Ask organizers for their expected point-label or route-sequence scoring convention before treating the displayed accuracy as the official metric.')
    anomalies=inventory.sort_values('reference_over_50m',ascending=False).head(5)
    table(['Trip','Partition','Aligned reference >50 m','Median ref. distance'],[[r.trip_id,r.partition,pct(r.reference_over_50m),f'{r.reference_distance_median:.1f} m'] for r in anomalies.itertuples()],[90,100,165,150])
    p('Trips 00000033 and 00000054 are particularly problematic. Spot checks also found large distances to the nearest supplied route segment, so monotone alignment alone does not explain their disagreement. These are retained and documented; no evaluator reference is used to repair predictions.')
    sub('Leakage prevention')
    p('Whole trips define CV groups. Learned preprocessing is fitted only inside training folds. Reference IDs/membership are never features. Candidate scores use local geometry and motion, not numeric road identifiers. Experiment scripts explicitly target train/student-test folders and ignore reserved evaluator data.')
    page();h('2.2 / Candidates and features')
    p('Road segments are densified to anchor spacing at most 25 m before spatial indexing. Up to 96 nearby anchors propose distinct segments, followed by exact segment projection and a 512-anchor expansion fallback. Eight candidates are retained; the query remains approximate, so candidate coverage is measured rather than assumed.')
    p('The directional candidate variant ranks by distance plus 18 times heading reliability times one minus heading cosine, then retains eight and reorders them by distance. Its training-matched experiment holds observation IDs, folds and model hyperparameters fixed.')
    table(['Feature group','Features','Reason'],[
      ['Geometry','Point distance, segment log-length, projected fraction, nearest endpoint distance','Measure physical proximity and position'],
      ['Motion','Heading cosine/absolute sine, previous/next point distances, speed, time gap, heading reliability','Disambiguate direction and parallel roads'],
      ['Candidate context','Distance rank and margin','Distinguish locally competing segments'],
      ['Topology','Source and target graph degree','Describe junction structure without road IDs']],[95,255,155])
    p('The five-point motion smoother uses past and future observations. This is full-trip batch reconstruction, not online causal tracking. All 15 features and their order are stored in the manifest.')
    fig('candidate_coverage.png','Candidate coverage for the distance-only proposal baseline, using every supplied observation.',maxheight=190)
    page();h('3 / Model experimentation')
    p(f'Seven distinct baseline algorithms were trained. Up to 450 seeded observations per training trip yield {manifest["training_observations"]:,} sampled observations and {manifest["training_observations"]*8:,} candidate rows across all 80 training trips. All student-test observations are evaluated. Uniform sampling per trip bounds runtime and reduces domination by the longest trips.')
    p('Three-fold GroupKFold prevents within-trip leakage. The declared selection objective is the mean of candidate binary Macro F1 and observation Top-1 on grouped CV. Candidate Macro F1 averages the positive/negative class F1 at threshold 0.5. It is not macro F1 across trip-specific road IDs. Top-1 selects the highest-scoring road candidate per observation. Candidate misses count as Top-1 failures.')
    rows=[]
    for r in models.itertuples():rows.append([short(r.model),pct(r.cv_macro_f1),pct(r.cv_top1_accuracy),pct(r.test_macro_f1),pct(r.test_top1_accuracy),f'{r.test_log_loss:.4f}',f'{r.test_inference_s:.3f}s'])
    table(['Model','CV F1','CV Top-1','Test F1','Test Top-1','Log loss','Inference*'],rows,[139,59,59,59,65,59,65])
    p('*Inference is total classifier prediction time across all ten student-test trips; it excludes candidate generation, graph decoding, scoring and HTTP serialization. Complete precision/recall/accuracy and fold spread are in the model comparison CSV. The directional variant uses different candidate identities and is a separate experiment.','SmallPS')
    fig('model_comparison.png','Actual grouped-CV and student-test comparisons. All model histories and configurations are retained.',maxheight=240)
    page();h('3.1 / Model-specific findings')
    descriptions={
      'LogisticRegression':('Linear / probabilistic','Log loss with L2 regularisation; C=1, max_iter=300, standardized features.','A fast linear baseline for distance and direction features. It is interpretable but cannot represent all nonlinear geometry/topology interactions.'),
      'GaussianNB':('Probabilistic','Gaussian class likelihood; variance smoothing 1e-7; standardized features.','A low-cost probabilistic baseline. Correlated distance, heading and neighborhood features conflict with its conditional-independence assumption; its measured log loss is a direct probability-quality diagnostic.'),
      'DecisionTree':('Tree','Gini impurity; max_depth=12, min_samples_leaf=25.','Captures nonlinear distance/heading rules and is easy to inspect. A single tree is sensitive to sample variation and can produce coarse probabilities.'),
      'RandomForest':('Bagged ensemble','100 Gini trees; max_depth=18, min_samples_leaf=10, four workers.','Averages nonlinear rules for stability. More trees cost time and memory; uncalibrated leaf probabilities can remain imperfect.'),
      'ExtraTrees':('Randomized ensemble','100 randomized Gini trees; max_depth=20, min_samples_leaf=8, four workers.','Tests whether stronger split randomisation improves generalisation and efficiency. Random thresholds can underfit useful distance boundaries.'),
      'HistGradientBoosting':('Boosting','Binary log loss; 130 iterations, 23 leaves, learning_rate=0.09, L2=2; early stopping disabled.','Efficient nonlinear boosting for structured candidate features. Its strong grouped-CV result made it the promising Bayesian-search family.'),
      'MLP':('Neural network','Binary log loss with L2 regularisation; standardized inputs, hidden=(32,16), Adam, batch_size=1024, 45 epochs.','Tests learned nonlinear feature interactions. Scaling and optimization matter; the recorded fit hit its epoch cap, so convergence is not established.')}
    for index,(name,(family,configuration,rationale)) in enumerate(descriptions.items()):
        if index and index%2==0:page();h('3.1 / Model-specific findings (continued)')
        row=models[models.model==name].iloc[0];diag=diagnostics[diagnostics.model==name].iloc[0]
        sub(f'{name} / {family}')
        p(rationale);p('<b>Training and objective:</b> '+configuration)
        p(f'<b>Measured student-test result:</b> Top-1 {pct(row.test_top1_accuracy)}, Macro F1 {pct(row.test_macro_f1)}, precision {pct(row.test_precision)}, recall {pct(row.test_recall)}, log loss {row.test_log_loss:.4f}. Candidate miss rate is {pct(row.test_candidate_miss_rate)}.')
        continuity=modelroute.loc[name,'direct_arc_continuity']
        p(f'<b>Generalisation and efficiency:</b> training-sample Macro F1 {pct(diag.macro_f1)} versus grouped-CV {pct(row.cv_macro_f1)}; CV fold Top-1 standard deviation {row.cv_fold_top1_std:.4f}. Separate single-refit training time was {diag.single_refit_training_s:.2f} s. Classifier-only direct arc continuity averages {pct(continuity)} per trip.')
        p('The train/CV gap is evidence to discuss potential overfitting, not proof of a single cause. CV versus student-test differences also reflect trip difficulty and reference quality. No fabricated epoch-wise validation curve is supplied. Full parameters, confusion matrices and results are retained.','SmallPS')
    page();h('3.2 / Probability and feature diagnostics')
    fig('log_loss.png','Actual binary candidate log loss for all baseline and selected configurations.',maxheight=185)
    fig('feature_ablation.png','Controlled feature ablation on the tuned nearest-candidate model. Topology complements geometry and motion.',maxheight=185)
    feature=pd.read_csv(ROOT/'results'/'feature_ablation.csv')
    table(['Feature set','Grouped CV Macro F1','Student-test Top-1'],[[r.feature_set,pct(r.cv_macro_f1),pct(r.test_top1_accuracy)] for r in feature.itertuples()],[205,150,150])
    page();h('3.3 / Actual neural training history')
    fig('mlp_loss.png','Recorded final-fit MLP loss_curve_. No validation-loss history was collected; no validation curve is invented.',maxheight=260)
    p('The MLP reached max_iter=45 and emitted a convergence warning. Its trajectory and generalisation scores are evidence of the actual optimization run. More training might improve it, but that was not established by this run; it was not selected simply because it is a neural network.')
    sub('Metric limitations')
    p('Candidate negatives outnumber positives approximately seven to one, so raw binary accuracy can look high even when the wrong road wins. Top-1 and Macro F1 are therefore both used. Binary probability normalization for HMM emissions is a scoring conversion, not proof of a calibrated multiway posterior. Candidate miss rate is an independent ceiling diagnostic.')
    page();h('4 / Bayesian hyperparameter optimisation')
    p('Optuna TPE performed 16 real trials with seed 42 and five startup trials. The objective and three grouped folds match the baseline protocol. The ten student-test trips were evaluated after fitting; no evaluator outcomes were used. Trial configurations, durations, CV metrics and fold details are retained in CSV and SQLite.')
    table(['Hyperparameter','Search range'],[['max_iter','Integer 70-210'],['learning_rate','Log-uniform 0.025-0.2'],['max_leaf_nodes','Integer 10-45'],['min_samples_leaf','Integer 15-100'],['l2_regularization','Log-uniform 0.1-20']],[230,275])
    table(['Best parameter','Recorded value'],list(manifest['best_parameters'].items()),[230,275])
    fig('bayesian_history.png','Each point is an executed trial; dashed line is the best objective observed so far.',maxheight=185)
    page();h('4.1 / Tuned versus untuned')
    subset=models[models.model.isin(['HistGradientBoosting','HistGradientBoosting_tuned'])]
    table(['Configuration','CV F1','CV Top-1','Test F1','Test Top-1','Log loss'],[[short(r.model),pct(r.cv_macro_f1),pct(r.cv_top1_accuracy),pct(r.test_macro_f1),pct(r.test_top1_accuracy),f'{r.test_log_loss:.5f}'] for r in subset.itertuples()],[160,69,69,69,69,69])
    p('Both fits use the same sampled observations, preprocessing protocol and folds. The tuned configuration is selected on the declared grouped-CV objective, not on training accuracy alone. The score gains are small; the report does not imply that tuning created a dramatic new capability.')
    p(f'The recorded baseline/trial pipeline elapsed time was {manifest["elapsed_s"]:.1f} seconds on this machine. Separate per-model refit timings are in training_diagnostics.json. Runtime is hardware- and load-dependent. CV-based model/hyperparameter selection introduces selection optimism; no nested unbiased model-selection estimate is claimed.')
    sub('Final candidate-selection experiment')
    table(['Condition','CV F1','CV Top-1','Test Top-1'],[['Tuned nearest candidates',pct(models[models.model=='HistGradientBoosting_tuned'].iloc[0].cv_macro_f1),pct(models[models.model=='HistGradientBoosting_tuned'].iloc[0].cv_top1_accuracy),pct(models[models.model=='HistGradientBoosting_tuned'].iloc[0].test_top1_accuracy)],['Training-matched directional candidates',pct(adaptive['cv_metrics']['macro_f1']),pct(adaptive['cv_metrics']['top1_accuracy']),pct(adaptive['test_metrics']['top1_accuracy'])]],[200,100,100,105])
    p('Directional candidates slightly improve the declared combined CV objective and reduce CV candidate misses, but lower candidate F1/log-loss quality and student-test classifier Top-1 in this run. The final end-to-end decoder results must therefore be examined separately; no uniform improvement claim is made.')
    p(f'<b>Selected inference artifact:</b> {escape(manifest["model"])}. Its candidate strategy is stored alongside the decoder configuration, preventing training/inference mismatch.')
    page();h('5 / HMM and Viterbi reconstruction')
    p('The hidden state at observation t is one candidate directed road arc. State IDs are candidate-to-arc mappings rather than global road classes. Fixed emissions are log normalized classifier probabilities. Adaptive emissions blend those with distance/heading geometry, with the blend adjusted by normalized candidate entropy. The classifier always contributes.')
    p('Directed transitions combine projected arc offsets and shortest-path network distance. Same-road negative projected progress up to the selected jitter tolerance is treated as measurement jitter. Network distance is compared with observed GPS displacement, with a time-gap-dependent denominator. Moves beyond 65 * dt + 70 m are invalid; searches are bounded at 2000 m.')
    table(['Decoder choice','Final value'],[[k,v] for k,v in decoder.items() if k not in ['warning','selection']],[210,295])
    sub('Viterbi recurrence and failure handling')
    p('V[t,j] = emission[t,j] + max_i(V[t-1,i] + transition[t,i,j]). Computation uses log scores and per-step normalization. Backpointers recover the best full sequence. Gaps above 60 seconds or wholly infeasible transitions restart a chunk; resets are returned as diagnostics.')
    p('If the reference road is not in the candidates, the decoder cannot recover it. Inference still returns a best available segment; the development scorer records the miss. When graph connectors cannot be found within the search bound, display geometry breaks into separate polylines instead of drawing an invented straight road.')
    p('The 30 m same-road jitter tolerance was experimentally important. It corrects noisy projections; it is not a claim that reverse driving is legal or that every network-feasible transition matches the true route.')
    page();h('5.1 / Actual route comparisons')
    table(['Method','Mean point accuracy','Direct continuity','Arc-set F1'],[[name,pct(row.point_accuracy),pct(row.direct_arc_continuity),pct(row.route_arc_f1)] for name,row in means.iterrows()],[170,115,110,110])
    p('All figures above are equal-trip means on the same ten student-test trips. Direct continuity checks collapsed consecutive predicted arcs sharing a node. Arc-set F1 measures segment coverage, not traversal order. Exact collapsed-route equality is recorded separately and is not implied by high point accuracy. Network feasibility allows valid multi-arc connectors and tolerated same-road GPS jitter.')
    fig('route_comparison.png','Per-trip decoding behavior and aggregate comparison. Settings were developed using these trips.',maxheight=240)
    selected=routes[routes.method==selected_method];baseline=routes[routes.method=='classifier_only'].set_index('trip_id')
    best=selected.sort_values('point_accuracy').iloc[-1];worst=selected.sort_values('point_accuracy').iloc[0]
    p(f'Best decoded trip: {best.trip_id}, {pct(best.point_accuracy)}. Most difficult decoded trip: {worst.trip_id}, {pct(worst.point_accuracy)}. Per-trip regressions and resets are visible in the CSV rather than removed from the aggregate.')
    page();h('6 / Tested project contributions')
    p('These are tested engineering contributions within PathSnap. Standard spatial indexing, boosting, HMMs, Viterbi and calibration are established techniques; no claim of global research originality is made.')
    table(['Idea','Experiment / measured decision'],[
      ['Directional candidates','Same samples/folds/hyperparameters; adopted only after improved declared combined CV objective. End-to-end behavior measured separately.'],
      ['Time/distance-aware transitions','Directed network distance, elapsed-time scaling, speed limit and gap resets; compared with classifier-only predictions.'],
      ['Geometry + learned emissions','Fixed versus adaptive HMM with the same final candidate model. Gains are modest beyond the strong fixed decoder.'],
      ['GPS jitter tolerance','8 m and 30 m tolerances, two emission strengths, three beta values, fixed and adaptive emissions were searched on permitted development trips.'],
      ['Probability calibration','Group-aware sigmoid diagnostic retained separately; production probability semantics remain explicit.'],
      ['Noise and dropout','Fixed-seed added coordinate noise and temporal thinning with unchanged original reference labels.']],[150,355])
    sub('Calibration: a small gain does not justify every change')
    p(f'Nearest-candidate tuned model student-test log loss was {cal["base_test_log_loss"]:.6f}; sigmoid calibration measured {cal["test_metrics"]["log_loss"]:.6f}. Top-1 was unchanged because a monotonic sigmoid preserves candidate ordering. The nested calibrated CV log loss was {cal["cv_metrics"]["log_loss"]:.6f}, versus {cal["base_cv_log_loss"]:.6f} for the uncalibrated baseline.')
    p('The calibrated outer-fold base fits use fewer training trips due to a disjoint calibration split, limiting strict comparison. The small probability gain did not establish a compelling replacement under the original CV selection objective. Calibration was not silently adopted. This experiment was performed before the final directional-candidate refit.')
    fig('calibration.png','Actual out-of-fold reliability diagnostic, with calibration-protocol caveat above.',maxheight=200)
    page();h('6.1 / Robustness and failure cases')
    p('Stress tests use student-test trips 00000052, 00000007 and 00000056. Added Gaussian coordinate noise has sigma 0, 5, 15 or 30 m; temporal thinning retains every fifth or tenth observation. Seeds are fixed. Labels are the original derived labels at retained observation indexes, not realigned to the perturbed GPS.')
    fig('robustness.png','Actual robustness runs on three development trips; not a guarantee across all trip conditions.',maxheight=230)
    robust=pd.read_csv(ROOT/'results'/'robustness.csv');summary=robust.groupby(['noise_sigma_m','sample_stride']).mean(numeric_only=True).reset_index()
    table(['Noise sigma','Keep every Nth','Classifier accuracy','Decoded accuracy','Candidate miss'],[[f'{r.noise_sigma_m:.0f} m',int(r.sample_stride),pct(r.classifier_accuracy),pct(r.decoder_accuracy),pct(r.candidate_miss_rate)] for r in summary.itertuples()],[90,100,110,110,95])
    p('Severe independent GPS noise can corrupt direction estimates, remove the correct road from the candidate set and degrade the decoder more than the classifier. This failure is retained in the evidence. Temporal thinning also changes feature distributions and omits intermediate roads, so route coverage and point accuracy answer different questions. Expanding candidates, robust smoothing and retraining with augmented noise are possible next experiments, not claimed verified improvements.')
    page();h('7 / Geographical visualization')
    shot('folium_development_map.png','Actual browser screenshot of the generated Folium development map for trip 00000007. Reference is legitimately available only in this development visualization.',maxheight=330)
    p('The interactive HTML and generation code are included. Raw GPS points are orange, the predicted route green, the supplied reference purple and optional road context gray. Layer controls, labels, a legend and geographic fit bounds support comparison. OpenStreetMap tiles and Leaflet CDN assets require connectivity; the evaluator UI also has its own offline geographic canvas.')
    fig('geographic_comparison.png','Independent plot of the same actual coordinates. No reference route is sent to the evaluator-facing UI.',maxheight=220)
    page();h('8 / API and user interface')
    shot('ui_desktop.png','Actual separate-origin browser screenshot after a live API request. The UI shows predicted geometry, raw GPS, relative confidence, server metrics, latency and observation playback.',maxheight=420)
    p('The responsive UI includes ten actual active trip options, configurable model-server URL, loading/error states, zoom/pan, layer toggles, playback and downloadable prediction JSON. Experiment tables are served from measured result files. Incorrect-server recovery and a 390 px mobile layout were exercised in browser QA.')
    p('The geographic canvas works without online basemap tiles. Reference route arrays are not included in the prediction response. The browser separately requests supplied reference geometry for the blue actual-path comparison layer. Displayed confidence is a relative normalized model score, not an independently calibrated correctness guarantee.')
    page();h('8.1 / API execution evidence')
    table(['Trip','HTTP','Observations','Point accuracy','Inference time'],[[r['trip_id'],r['status'],r['observations'],pct(r['point_accuracy']),f'{r["inference_s"]:.3f} s'] for r in api],[100,55,110,125,115])
    p('These are actual HTTP requests against the locally running final server. Inference time includes loading, candidate generation, classifier scoring and graph decoding; HTTP wall time also includes geometry serialization and reference scoring. Local timing varies with machine load.')
    logs=(ROOT/'results'/'server_log_excerpt.txt').read_text(errors='replace').splitlines();entries=[x for x in logs if 'INFERENCE request=' in x][-5:]
    sub('Actual receiving-server log excerpt')
    for line in entries:p(escape(line),'SmallPS')
    p('<b>Evidence boundary:</b> this excerpt is real local server output, not a screenshot of a second laptop or CMD. Capture a genuine receiving-console screenshot during physical two-laptop rehearsal to satisfy the organizer\'s console-screenshot requirement.')
    shot('api_documentation.png','Actual local OpenAPI documentation screenshot; endpoint contracts are included in the source.',maxheight=110)
    page();h('8.2 / Deployment and verification')
    table(['Host','Files and command','Verification'],[
      ['Laptop 1','Complete backend, artifacts, raw trip files and results. run_backend.cmd [port]','Health endpoint, visible request logs, selected model manifest'],
      ['Laptop 2','UI-only ZIP. run_ui.cmd [port]; set Laptop 1 URL in UI settings','Reach server, select all ten trips, confirm route/metric updates']],[80,255,170])
    p('The UI-only archive contains no model weights, raw dataset or reference labels. No LAN IP is hardcoded; the browser stores its configured API URL. Both launcher ports are configurable. Reserved evaluator folders, when legitimately provided, activate evaluator mode; the supplied development ZIP does not contain them.')
    sub('Local automated evidence')
    p(escape((ROOT/'results'/'test_results.txt').read_text().strip().splitlines()[-1]))
    for check in browser['checks']:p('- '+escape(check),'SmallPS')
    p('Browser QA uses UI port 8080 and API port 8000 on the same machine. Cross-origin operation is real; physical cross-laptop reachability is not established. A detailed network/deployment checklist is included in docs/DEPLOYMENT.md.')
    sub('Pending before evaluation')
    p('1. Physical two-laptop rehearsal and genuine receiving-console screenshot.<br/>2. Confirmation of the official scoring convention; supplied evaluator trips now have a separate frozen-model replay.<br/>3. Public GitHub publication through the team account, then URL verification.<br/>4. Replace placeholders, review AI-assisted explanations and add team interpretation.')
    page();h('9 / Final audit and team review')
    p('The source repository includes a requirement-by-requirement checklist mapped to all five PDFs. It records full implementation evidence, local verification limits and unresolved external requirements. The final manifest ties the chosen classifier, feature order and candidate strategy to the decoder configuration.')
    sub('Experiments actually executed')
    p(f'Seven baseline algorithms; sixteen Bayesian trials; tuned/untuned comparison; four feature sets; four candidate-count coverage levels; group-aware sigmoid calibration; inference-time directional candidates; a training-matched directional candidate comparison; {len(json.loads((ROOT/"results"/"decoder_search.json").read_text()))} decoder settings on ten trips; eighteen noise/dropout cases; training diagnostics; live API requests for all ten trips; automated unit/integration tests and real browser screenshots.')
    sub('Defensible conclusions')
    p(f'The final pipeline obtains {pct(means.loc[selected_method,"point_accuracy"])} equal-trip decoded point accuracy on permitted development trips, compared with {pct(means.loc["classifier_only","point_accuracy"])} for its classifier-only predictions and {pct(means.loc["fixed_hmm","point_accuracy"])} for the strongest measured fixed HMM on the same candidate/model setup. Adaptive gains beyond fixed decoding are small and do not imply universal improvement.')
    p('Model selection follows recorded grouped-CV evidence. Route reconstruction improves pointwise agreement and route coherence on the supplied development data. Reference-derived labels, development tuning and a small fixed test set limit generalisation claims. Reserved evaluator performance remains unknown.')
    sub('Team interpretation placeholders')
    p('[TEAM REVIEW] Explain which failure case matters most and why.<br/>[TEAM REVIEW] Confirm actual contributions and understanding of every subsystem.<br/>[TEAM REVIEW] Add physical deployment screenshots and the public repository URL.<br/>[TEAM REVIEW] State the event-required AI assistance disclosure accurately.')
    sub('Sources and reproducibility')
    p('Organizer sources: Main Guidelines; Models and Training Guidelines; Deliverables; Assessment and Plagiarism Policy; Dataset Exploration. Software references: scikit-learn GroupKFold, Optuna TPESampler, SciPy sparse graph algorithms, FastAPI and Folium official documentation. URLs and pinned dependencies are in README.md. Full source, seeds, configurations, results and inference artifacts accompany this report. No outside team implementation or results were used.','SmallPS')
    audit_path=ROOT/'results'/'critical_audit'/'accuracy_audit.json'
    if audit_path.exists():
        audit=json.loads(audit_path.read_text());new=json.loads((ROOT/'results'/'critical_audit'/'final_accuracy.json').read_text())
        improvement=json.loads((ROOT/'results'/'critical_audit'/'uturn_validation_decision.json').read_text())
        benchmark=pd.read_csv(ROOT/'results'/'critical_audit'/'decoder_pruning_benchmark.csv')
        page();h('10 / Independent critical audit')
        p(f'The original 95.25% claim reproduces as {100*audit["macro_trip_accuracy"]:.4f}% equal-trip mean. Observation weighting instead gives {100*audit["observation_weighted_accuracy"]:.4f}%: {audit["total_correct"]:,} correct out of {audit["total_observations"]:,}. These summaries answer different questions and are both retained.')
        p('An independently coded geometry/convolution/reference-DP-history implementation reproduced every reference label on the ten student-test trips. Raw candidates, features, classifier probabilities and cached labels were replayed; complete-trip CV membership was rechecked. No identical track files or matching moving ten-observation windows were found across training/student-test partitions. This is evidence against those duplication mechanisms, not proof against all semantic overlap.')
        p('Reference-label agreement remains partly circular: the aligner and predictor both use distance and heading. Removing heading from the reference aligner changes some labels; doubling the forward-progress penalty did not change these ten reference sequences. The report therefore cannot claim 95% independently verified physical road accuracy.')
        sensitivity=json.loads((ROOT/'results'/'critical_audit'/'decoder_selection_sensitivity.json').read_text())
        p(f'Leave-one-trip-out reselection of the original decoder settings gives {pct(sensitivity["leave_one_trip_out_decoder_selection_accuracy"])}. This only diagnoses decoder-selection sensitivity conditional on the fixed model/alignment design; it is not a nested unbiased pipeline test.')
        sub('Per-trip error audit of the original pipeline')
        table(['Trip','Errors','Missing reference candidate','Reverse directed road','Independent label differences'],[[r['trip_id'],r['errors'],r['errors_reference_not_candidate'],r['errors_reverse_directed_segment'],r['independent_alignment_disagreements']] for r in audit['records']],[75,60,130,120,120])
        p('Trip 00000077 is the largest contributor: many errors choose the reverse road direction, not a missing road candidate. A general U-turn prior was therefore tested on training-only holdout trips rather than tuned against this student-test trip.')
        page();h('10.1 / Validated changes and rejections')
        p(f'Pruning directed shortest-path searches to each source\'s maximum physically admissible travel cap preserves every feasible transition and all ten original predicted sequences. The measured transition-build totals fell from {benchmark.unpruned_s.sum():.2f} s to {benchmark.pruned_s.sum():.2f} s ({benchmark.unpruned_s.sum()/benchmark.pruned_s.sum():.2f}x). These are measured same-machine timings, not a universal speed guarantee.')
        p(f'The soft U-turn cost log(2) was assessed on a seeded twelve-trip training-only holdout, with a classifier fitted on the remaining 68 trips. Mean holdout accuracy improved by {100*improvement["training_holdout_accuracy_gain"]:.3f} percentage points. A separate eighteen-case training-holdout noise/dropout replay improved by {100*improvement["mean_robustness_gain"]:.3f} points on average, with no case dropping over two points. Repeated median decoding time was {improvement["repeated_median_decode_ratio"]:.3f} times baseline.')
        p(f'The prior passed the predeclared gates before student-test evaluation and was retained. Its descriptive student-test result is {100*new["mean_trip_accuracy"]:.4f}% equal-trip mean and {100*new["observation_weighted_accuracy"]:.4f}% observation-weighted. This is a negligible aggregate change from the original development result; trip 00000040 regresses while trip 00000077 improves. No statistical-significance or generalisation guarantee is claimed.')
        p('A row-normalized transition-HMM alternative was tested and rejected: it reduced training-holdout mean accuracy and increased decoding cost. The production implementation uses unnormalized transition compatibility potentials in a Viterbi/MAP chain. They are proportional plausibility scores, not a stochastic transition matrix or calibrated probability of driving behavior.')
        p('Reliability fixes include finite single-candidate entropy, integer-index validation, separate reference-scoring failure handling, complete-trip inventories, schema checks, configurable data root, port-independent UI origin, loading-state locking and keyboard/touch map controls. Expanded-query adaptive reranking changed two noisy-case scores. A matching refit reduced grouped-CV objective, so it was rejected; production explicitly retains the historical_v1 profile used in training. Both profiles and experimental evidence are preserved.')
        rejected=json.loads((ROOT/'results'/'critical_audit'/'corrected_candidate_refit.json').read_text())
        p(f'<b>Rejected candidate-refit configuration:</b> the same 71-iteration, 32-leaf tuned boosting setup with current_v2 candidates achieved grouped-CV Macro F1 {pct(rejected["cv_metrics"]["macro_f1"])}, Top-1 {pct(rejected["cv_metrics"]["top1_accuracy"])} and log loss {rejected["cv_metrics"]["log_loss"]:.5f}. Its combined objective fell from {rejected["historical_cv_objective"]:.6f} to {rejected["corrected_cv_objective"]:.6f}. Student-test metrics for this rejected refit are N/A: it failed the training-only promotion criterion, so no final student-test model was fitted. This is a candidate-processing variant, not an eighth algorithm family.')
        sub('Reproducibility checks')
        p('All seven baseline models plus tuned/directional variants were refitted in the same three trip-grouped folds and every stored metric reproduced within 1e-7. Sixteen Bayesian objectives/fold records match the SQLite study and CSV. Four feature ablations and nested calibration metrics were replayed. Robustness was reexecuted using the final candidate profile; historical outputs and the rejected fallback variant remain available for comparison.')
        clean=(ROOT/'results'/'critical_audit'/'clean_environment_tests.txt').read_text()
        p(escape(clean.strip().splitlines()[-1]))
        p('A new isolated virtual environment installed the locked dependencies, passed pip check, reloaded the saved model, and served actual HTTP inference. The deployment package smoke test and physical two-laptop boundary are documented in FINAL_READINESS_AUDIT.md. One clean-environment Starlette/httpx deprecation warning is recorded; tests and HTTP requests still pass.')
        page();h('10.2 / Consolidated required comparison')
        families=['Linear','Probabilistic','Tree','Ensemble','Ensemble','Boosting','Neural','Boosting','Boosting']
        configs=['C=1; 300 iter','var smooth 1e-7','depth12; leaf25','100 trees; depth18; leaf10','100 trees; depth20; leaf8','130 iter; 23 leaves; rate .09','32/16 units; 45 epochs','71 iter; 32 leaves; rate .087','Same tuned HGB; directional candidates']
        rows=[]
        for i,r in enumerate(models.itertuples()):
            continuity=modelroute.loc[r.model,'direct_arc_continuity']
            rows.append([f'M{i+1} / '+short(r.model),families[min(i,8)],configs[min(i,8)],pct(r.cv_macro_f1),pct(r.test_top1_accuracy),pct(continuity),pct(r.test_macro_f1),f'{r.test_log_loss:.4f}',f'{r.test_inference_s:.3f}s'])
        table(['Model','Family','Key configuration','CV F1','Test Top-1','Direct continuity','Test F1','Log loss','Inference'],rows,[73,55,101,46,46,46,46,46,46])
        p('Continuity is equal-trip mean for classifier-only outputs. Inference time is classifier prediction summed over ten trips, not total HTTP latency. Model-specific explanations and full source configurations appear earlier and in the repository. The final U-turn prior changes sequence decoding, not this classifier comparison.','SmallPS')
    evaluator_path=ROOT/'results/evaluator_verification.json'
    if evaluator_path.exists():
        ev=json.loads(evaluator_path.read_text())
        page();h('11 / Supplied evaluator replay')
        p('After model selection was complete, a separate evaluator_test.zip containing ten trips and supplied .route references was received. The saved model, features, candidate profile and decoder settings were preserved. No evaluator result was used to select algorithms, features or hyperparameters, and no prediction was manually altered.')
        table(['Measure','Verified value'],[
          ['Evaluator trips / observations',f'{ev["trips"]} / {ev["observations"]:,}'],
          ['Equal-trip derived point agreement',f'{100*ev["equal_trip_point_accuracy"]:.4f}%'],
          ['Pooled derived point agreement',f'{100*ev["pooled_point_accuracy"]:.4f}%'],
          ['Model artifact unchanged',str(ev['model_matches_audited_artifact'])],
          ['Official evaluator scoring verified','No'],
          ['Physical two-laptop execution verified','No']],[270,235])
        table(['Trip','Observations','Derived agreement','Reference arcs'],[[r['trip_id'],r['observations'],f'{100*r["point_accuracy"]:.2f}%',r['reference_arcs']] for r in ev['records']],[110,120,140,135])
        p('These percentages use the same documented monotone alignment to supplied route sequences; they are not official evaluator accuracy or independently verified physical ground truth. The original seven-model comparisons and development results remain unchanged.')
        p('The UI now renders supplied actual-path geometry in blue and model-predicted geometry in green as independently toggleable layers. Reference geometry is loaded through GET /api/reference/{trip_id} after POST inference; it does not feed the classifier or decoder. Missing or malformed references leave inference functional. Set PATHSNAP_REFERENCE_DISPLAY=0 before starting the backend for a reference-free demonstration.')
        p('Evidence: results/evaluator_inventory.json, results/evaluator_verification.json, results/browser_qa.json and tests/test_reference_display.py. Raw files remain private on Laptop 1 and are excluded from publication. The UI transfer ZIP contains no raw reference files.')
    doc=SimpleDocTemplate(str(OUT/'PathSnap_Technical_Report.pdf'),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=53,bottomMargin=54,title='PathSnap Technical Report',author=team['team_name'])
    doc.build(story,onFirstPage=banner,onLaterPages=banner)
    print(OUT/'PathSnap_Technical_Report.pdf',flush=True)

if __name__=='__main__':main()
