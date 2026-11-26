"""Create an English presentation for editable Canva import, using verified project outputs."""
from pathlib import Path
import json
import os
ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'deliverables' / 'english'
ASSETS = DEST / 'assets'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'outputs' / '.mplconfig'))
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.xmlchemy import OxmlElement
from PIL import Image

NAVY='12283F'; TEAL='127F8C'; GOLD='D99A32'; INK='22384B'; GRAY='607284'; WHITE='FFFFFF'
FEATURE_LABELS=['Play time (raw)', 'Sessions / week', 'Minutes / session', 'Player level', 'Achievements']


def savefig(name):
    plt.tight_layout()
    plt.savefig(ASSETS/name, dpi=190, bbox_inches='tight')
    plt.close()


def make_charts(s,p):
    sns.set_theme(style='whitegrid', font='Arial')
    df=pd.read_csv(ROOT/'data/online_gaming_behavior_dataset.csv')
    features=s['features']; x=df[features]
    fig,axes=plt.subplots(2,3,figsize=(12,6))
    for ax,col,label in zip(axes.flat,features,FEATURE_LABELS):
        ax.hist(x[col],bins=30,color='#197c9b',edgecolor='white'); ax.set_title(label,fontsize=10)
        ax.set_ylabel('Players')
    axes.flat[-1].axis('off'); savefig('distributions.png')
    plt.figure(figsize=(8,5))
    sns.heatmap(x.corr(),annot=True,fmt='.2f',cmap='vlag',vmin=-1,vmax=1,
                xticklabels=FEATURE_LABELS,yticklabels=FEATURE_LABELS)
    plt.title('Pearson correlation: descriptive EDA'); savefig('correlations.png')
    plt.figure(figsize=(11,4))
    dendrogram(np.load(ROOT/'outputs/ward_linkage.npy'),truncate_mode='lastp',p=24,show_leaf_counts=True)
    plt.title('Ward tree: last 24 branches of the 4,000-player training sample')
    plt.xlabel('Branch; numbers in parentheses show branch size'); plt.ylabel('Ward merge distance')
    savefig('dendrogram.png')
    search=pd.read_csv(ROOT/'outputs/model_selection.csv')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for method,g in search.groupby('method'):
        axes[0].plot(g.k,g.silhouette,'o-',label=method)
        axes[1].plot(g.k,g.davies_bouldin,'o-',label=method)
    axes[0].set_title('Silhouette: higher is better'); axes[1].set_title('DBI: lower is better')
    for ax in axes: ax.set_xlabel('Number of clusters k'); ax.legend(fontsize=8)
    savefig('model_selection.png')
    normalized=(p[features]-x.mean())/x.std(ddof=0)
    plt.figure(figsize=(10,5.5))
    sns.heatmap(normalized,annot=True,fmt='.2f',cmap='vlag',center=0,
                xticklabels=FEATURE_LABELS,yticklabels=[f'C{int(c)}' for c in p.cluster])
    plt.title('Cluster means relative to all players (z-scores)')
    plt.ylabel('Cluster ID'); savefig('profiles.png')
    artifact=joblib.load(ROOT/'outputs/player_cluster_model.joblib')
    z=artifact['preprocessor'].transform(x)
    labels=artifact['model'].predict(z)
    pca=PCA(n_components=2).fit(z); xy=pca.transform(z)
    si=np.random.default_rng(42).choice(len(z),7000,replace=False)
    plt.figure(figsize=(8,5))
    scatter=plt.scatter(xy[si,0],xy[si,1],c=labels[si],cmap='tab10',s=6,alpha=.4)
    plt.legend(*scatter.legend_elements(),title='Cluster',fontsize=7)
    plt.xlabel('PC1'); plt.ylabel('PC2')
    plt.title(f'PCA 2D retains {pca.explained_variance_ratio_.sum():.1%} of variance')
    savefig('pca.png')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].bar(p.cluster,p['count'],color='#197c9b'); axes[0].set_title('Players per cluster')
    axes[1].bar(p.cluster,p.purchase_rate*100,color='#de9f37')
    axes[1].set_title('Players with a purchase (%)'); axes[1].set_ylim(0,100)
    for ax in axes:ax.set_xlabel('Cluster ID')
    savefig('sizes_purchases.png')


def content(s,p):
    return [
      ('Gamer Behavior Clustering', ['Player Profiling with Ward + K-Means', 'Data Mining Project | 13–15 minute presentation', '[Presenter 1 / Student ID]  •  [Presenter 2 / Student ID]'], None,
       'Our project explores whether players with similar behavior can be grouped into useful profiles. We combine Ward hierarchical clustering with K-Means, evaluate the resulting groups, and propose product experiments. The dataset comes from Kaggle and is explicitly synthetic for educational use. We therefore distinguish what the algorithm demonstrates from what a real game business would still need to validate. We will cover the data, preprocessing, clustering methods, evaluation, profiles, and monetization hypotheses.'),
      ('Four questions guide the project', ['What player behavior can the dataset actually measure?', 'How does Ward initialize K-Means?', 'Are the clusters compact, separated, and stable?', 'Which targeted product experiments could follow?'], None,
       'We organize the project around four questions. First, which behaviors can we measure without inventing unavailable features? Second, how are the two clustering algorithms connected in the actual implementation? Third, how do we evaluate an unsupervised solution without ground-truth segment labels? Finally, how can profiles support testable product ideas? Every numerical claim comes from executed code. The repository includes the Python pipeline and nine executed Jupyter notebooks with explanations, tables, and charts.'),
      ('40,034 players • 13 source columns', ['Kaggle author: Rabie El Kharoua | version 1', 'License: Creative Commons Attribution 4.0', 'Publisher-declared synthetic educational data', 'One row per PlayerID; no transaction history'], None,
       'The source contains 40,034 rows and 13 columns. Each row represents a synthetic player and includes demographics, context, activity, level, achievements, and an engagement category. We downloaded the original CSV and preserved its metadata and data card. The publisher explicitly states that the dataset was generated for education. This supports an algorithmic case study, but it does not establish real-world player segments or a business impact. The dataset also lacks a documented observation window for each player.'),
      ('Missing fields limit the requested metrics', ['Win/loss ratio: no wins or losses are recorded', 'Item collection rate: no timed item counts', 'True skill score: no Elo or MMR', 'High spenders: purchase flag is binary, not an amount'], None,
       'The assignment suggests play time, win/loss ratio, item collection rate, and skill score. Only some of these can be measured from this source. PlayerLevel is a progression indicator, not a validated skill score. AchievementsUnlocked is an accumulated count, not an item collection rate. InGamePurchases indicates whether a player purchases, not how much they spend. We do not fabricate the missing metrics or label any cluster as high spenders. We also flag inconsistent descriptions of the two session-duration columns.'),
      ('Five numeric features describe play style', ['PlayTimeHours: raw duration indicator; verify its units', 'SessionsPerWeek and AvgSessionDurationMinutes', 'PlayerLevel and AchievementsUnlocked', 'Exclude ID; reserve engagement and purchases for post-hoc analysis'], 'distributions.png',
       'The model uses five numeric features to represent activity, duration, and progression. We exclude PlayerID because its numerical value has no behavioral meaning. We also exclude EngagementLevel and the purchase flag from clustering and model selection. This prevents the analysis from simply reproducing an existing category or splitting users directly by purchase status. The histograms show the raw feature distributions. A near-uniform distribution does not itself demonstrate the existence of natural segments.'),
      ('Fit preprocessing on training data only', ['Training: 32,027 players | Holdout: 8,007 | seed 42', 'Numeric checks → median imputer → StandardScaler', 'Fit on training data; transform the holdout', 'Do not remove active players merely as outliers'], None,
       'We split the data into 80 percent training and 20 percent holdout using seed 42. Numeric coercion and domain checks happen before learned preprocessing. Median imputation and StandardScaler are fitted only on training observations. The holdout uses the fitted transforms. Standardization makes Euclidean distances less dependent on the original units of minutes, levels, and counts. The supplied dataset has no missing values or duplicate player IDs after inspection, but the saved imputer provides a consistent rule for future inputs.'),
      ('Correlation checks do not supply labels', ['Inspect variance and Pearson correlation', 'Do not select features using EngagementLevel', 'Avoid double-counting sessions × session duration', 'PlayTimeHours needs source validation and sensitivity analysis'], 'correlations.png',
       'The correlation chart is descriptive exploratory analysis. We use it to inspect linear relationships and potential redundancy, not to define the correct clusters. Feature inclusion is based on the assignment and the meaning of the source fields. We do not rank features using the engagement label because that would introduce supervision into the design. The two duration columns do not agree when minutes are converted to hours, so we avoid assuming that PlayTimeHours measures weekly hours. We later examine the effect of removing it. I will now hand over to our second presenter.'),
      ('K-Means provides a reproducible baseline', ['Assign each point to the nearest center', 'Update centers using cluster means; repeat', 'k-means++ | 20 initializations | up to 300 iterations', 'Efficient, but sensitive to k and cluster geometry'], None,
       'K-Means alternates between assigning each observation to its nearest center and updating centers as cluster means. It minimizes the sum of squared distances within clusters. We use k-means++ initialization, 20 starts, and up to 300 iterations for each candidate k. This is a simple baseline with a natural predict method for new players. However, it favors compact Euclidean clusters and will partition continuous data even if no natural player types exist. Evaluation and stability checks are therefore necessary.'),
      ('Ward merges clusters with the least SSE increase', ['Build the hierarchy on 4,000 training players', 'Merge the pair with the smallest increase in within-cluster SSE', 'Cut the tree at candidate k values from 2 to 8', 'Out-of-sample Ward uses nearest-centroid extension'], 'dendrogram.png',
       'Agglomerative Ward clustering starts with one cluster per observation and repeatedly merges the pair that increases within-cluster squared error the least. We fit a true Ward hierarchy on a 4,000-player training sample to control memory use. The displayed tree shows its last 24 branches; branch counts are not individual players. Ward has no natural predict method. Its holdout comparison therefore uses the nearest centroid of each sample-based cluster, and we explicitly report that extension rather than calling it exact Ward clustering on the entire holdout.'),
      ('Ward centers initialize full-training K-Means', ['Ward sample → cut the tree at k', 'Average each Ward cluster → initial centers', 'Fit K-Means on all training players with n_init = 1', 'Save the preprocessing pipeline and final model'], None,
       'The hybrid connects the methods through the initial centers. We cut the Ward hierarchy at k, calculate each cluster mean, and pass those means to K-Means through its init argument. During model selection, both stages use the same training sample. After k is locked, K-Means refines the Ward-derived centers on all training players. We use one initialization because the centers are already specified. This offers structured initialization and scalable prediction, but it does not guarantee better results than k-means++.'),
      ('Two internal metrics assess cluster geometry', ['Silhouette ↑: s = (b − a) / max(a, b)', 'a: own-cluster distance; b: nearest-other-cluster distance', 'Davies–Bouldin ↓: within-cluster scatter / center separation', 'No ground-truth segments: do not report classification accuracy'], None,
       'Silhouette compares average distance within a point’s cluster with its average distance to the nearest other cluster. For example, a equals two and b equals five gives a silhouette of 0.6. Values near zero indicate overlap; negative values suggest a closer alternative cluster. Davies–Bouldin compares cluster scatter with separation between centers, so lower values are preferred. We use the same 2,000-player silhouette sample within each evaluation stage and compute DBI on the full set at that stage. These metrics do not measure revenue or prove that the segments are meaningful outside the dataset.'),
      ('The hybrid selects k = 8 within the tested range', ['Compare all three methods on the same training sample', 'Minimize rank(Silhouette descending) + rank(DBI ascending)', 'Selected k: K-Means 8 | Ward 6 | Ward + K-Means 8', 'k = 8 is the upper boundary tested, not a global optimum'], 'model_selection.png',
       'We test k from two to eight for each method under the same training-sample conditions. The selection rule minimizes the sum of the descending silhouette rank and ascending DBI rank. Ties favor a higher silhouette and then a smaller k. The hybrid selects eight clusters within this range. We do not force three groups just to match the illustrative labels in the assignment. Because eight is the upper search boundary, this result is not a globally optimal cluster count. We lock k before evaluating the holdout.'),
      ('Holdout: Silhouette 0.1540 • DBI 1.4322', ['K-Means: k = 8 | Silhouette 0.1501 | DBI 1.4461', 'Ward extension: k = 6 | Silhouette 0.1435 | DBI 1.6267', 'Ward + K-Means: k = 8 | Silhouette 0.1540 | DBI 1.4322', 'Small metric differences do not establish a robust advantage'], None,
       'On the holdout, the hybrid scores 0.1540 for silhouette and 1.4322 for Davies–Bouldin. The baseline scores 0.1501 and 1.4461, while Ward’s centroid extension scores 0.1435 and 1.6267. The hybrid is slightly better on both metrics in this run. We have not established uncertainty around these differences, so we do not claim a robust advantage. Both K-Means variants were fitted on all training players, whereas the Ward baseline uses centroids from its training sample. The hybrid was the assignment’s primary method before inspecting these results.'),
      ('Clusters overlap and depend on initialization', ['Five alternative Ward samples: mean ARI = 0.3132', 'Lowest ARI versus seed 42 = 0.2612', 'Remove PlayTimeHours: ARI versus main model = 0.2458', 'Do not interpret eight clusters as eight proven natural types'], None,
       'We repeat Ward sampling using five alternative seeds, keep the split and k fixed, and compare holdout assignments with the reference run. The mean adjusted Rand index is 0.3132 and the minimum is 0.2612, showing substantial sensitivity to initialization. Removing PlayTimeHours gives an ARI of 0.2458 against the main model. ARI here compares partitions, not predictions against true segment labels. Metrics from the four-feature sensitivity model should not be ranked directly against the five-feature model because their distance spaces differ. Together with the low silhouette, these results limit operational interpretation.'),
      ('Profiles describe observed relative behavior', ['Eight clusters; each contains 11.9–13.4% of players', 'Describe frequency, session length, level, and achievements', 'Purchase incidence ranges from 18.9% to 20.9%', 'Purchase incidence does not measure spending intensity'], 'profiles.png',
       'We apply the training-fitted model to all rows to create descriptive profiles. Cluster IDs are identifiers, not ranks. The heatmap reports cluster means relative to the overall feature means in standard-deviation units. Warm colors indicate above-average values and cool colors indicate below-average values. Cluster sizes are fairly similar. We describe frequency and session length relatively rather than asserting validated casual or hardcore types. Purchase incidence varies only within the displayed range and cannot identify high spenders because the source does not contain amounts.'),
      ('The 2D PCA view retains only 40.3% of variance', ['PCA is a post-hoc visual aid, not a clustering input', 'Colors show assignments learned in five dimensions', 'A 2D projection cannot establish cluster validity', 'Interpret it alongside holdout metrics and stability'], 'pca.png',
       'PCA projects the five standardized inputs into two dimensions for visualization. The projection retains about 40.3 percent of the variance. Clustering was performed in the original five-dimensional standardized space, not on this plot. Overlap in the projection does not by itself prove that every assignment is wrong, while visible color patterns do not validate natural player types. We interpret the view alongside the low silhouette and the sensitivity checks rather than treating it as independent evidence of successful segmentation.'),
      ('Targeted offers remain A/B-test hypotheses', ['Short sessions: small cosmetic bundles and easy trials', 'Long sessions: optional themed content and expansions', 'Infrequent sessions: return-time touchpoints; cap prompts', 'Measure conversion, revenue per eligible player, retention, and refunds'], 'sizes_purchases.png',
       'The profile-based ideas are hypotheses, not proven monetization strategies. Short-session groups could be offered small cosmetic bundles, while longer-session groups could be shown optional themed content. For less frequent players, a return-time touchpoint may be worth testing. Randomize control and treatment within each eligible cluster and freeze assignments before the experiment. Measure all randomized eligible players, including non-buyers. Track conversion or revenue per player along with retention, refunds, and complaints. Without transaction amounts and an actual intervention, we cannot estimate uplift, ROI, or revenue gains.'),
      ('A reproducible pipeline with clearly bounded claims', ['Python pipeline + nine executed Jupyter notebooks', 'Ward → centers → K-Means; holdout and sensitivity checks', 'Next: validate units, collect real logs, timed metrics, and transactions', 'Source: Rabie El Kharoua, Kaggle (CC BY 4.0) | Questions?'], None,
       'The deliverables include the original source data, a reproducible Python pipeline, nine executed notebooks, result tables, figures, and the saved model. The hybrid uses Ward-derived centers to initialize K-Means and includes holdout evaluation and sensitivity analysis. The main limitations are synthetic data, inconsistent duration semantics, missing behavioral and spending metrics, and unstable partitions. A real deployment would require source validation, appropriate observation windows, real logs, and controlled experiments. The repository is github.com/AnhMinh207/gamer-behavior-clustering. Thank you for listening; we welcome your questions.'),
    ]


def text(slide, value, x,y,w,h,size=23,color=INK,bold=False):
    sh=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=sh.text_frame; tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(.02)
    for i,line in enumerate(value.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=line; p.font.name='Arial'; p.font.size=Pt(size)
        p.font.color.rgb=RGBColor.from_string(color); p.font.bold=bold; p.space_after=Pt(12)
    return sh


def build_deck(items):
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    prs.core_properties.title='Gamer Behavior Clustering & Player Profiling — English'
    prs.core_properties.subject='Data Mining: Ward Hierarchical Clustering and K-Means'
    for i,(title,points,chart,notes) in enumerate(items,1):
        sl=prs.slides.add_slide(prs.slide_layouts[6])
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb=RGBColor.from_string(NAVY if i==1 else 'F5F8FA')
        band=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,prs.slide_width,Inches(.1))
        band.fill.solid(); band.fill.fore_color.rgb=RGBColor.from_string(TEAL); band.line.fill.background()
        if i==1:
            text(sl,'DATA MINING / PLAYER ANALYTICS',.7,.6,11,.5,15,'50C9C3',True)
            text(sl,'GAMER BEHAVIOR\nCLUSTERING',.7,1.5,12,1.9,45,WHITE,True)
            text(sl,'WARD  →  CLUSTER CENTERS  →  K-MEANS',.7,3.7,12,.7,27,'50C9C3',True)
            text(sl,'\n'.join(points),.7,4.7,12,1.7,20,WHITE)
        else:
            text(sl,title,.6,.4,12.1,.85,28,NAVY,True)
            section='DATA & SCOPE' if i<=7 else 'MODELS & EVALUATION' if i<=14 else 'PROFILES & APPLICATION'
            text(sl,section,.62,1.28,12,.3,11,TEAL,True)
            if chart:
                text(sl,'\n'.join('• '+p for p in points),.65,1.9,4.05,4.85,20)
                f=ASSETS/chart; iw,ih=Image.open(f).size
                w,h=7.5,4.85
                if w/h>iw/ih:w=h*iw/ih
                else:h=w*ih/iw
                sl.shapes.add_picture(str(f),Inches(5.1+(7.5-w)/2),Inches(1.85+(4.85-h)/2),width=Inches(w),height=Inches(h))
            elif i==10:
                for j,p in enumerate(points):
                    box=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(.7+j*3.12),Inches(2.4),Inches(2.85),Inches(2.25))
                    box.fill.solid(); box.fill.fore_color.rgb=RGBColor.from_string(TEAL if j<3 else NAVY); box.line.fill.background()
                    text(sl,f'{j+1:02}',.9+j*3.12,2.62,2.4,.55,28,'8DE0DA',True)
                    text(sl,p,.9+j*3.12,3.3,2.4,1.15,20,WHITE)
                text(sl,'Hierarchical structure seeds a scalable model; it does not guarantee better clusters.',.75,5.3,12,1,22,GRAY)
            elif i==13:
                headers=['Method','k','Silhouette ↑','DBI ↓']
                rows=[['K-Means','8','0.1501','1.4461'],['Ward extension','6','0.1435','1.6267'],['Ward + K-Means','8','0.1540','1.4322']]
                table=sl.shapes.add_table(4,4,Inches(.8),Inches(2.0),Inches(11.7),Inches(2.6)).table
                for column,width in zip(table.columns,[4.2,1.0,3.2,3.3]):
                    column.width=Inches(width)
                for ri,row in enumerate([headers]+rows):
                    for ci,value in enumerate(row):
                        cell=table.cell(ri,ci); cell.text=value
                        cell.fill.solid(); cell.fill.fore_color.rgb=RGBColor.from_string(NAVY if ri==0 else 'D5EEEB' if ri==3 else WHITE)
                        for pp in cell.text_frame.paragraphs:
                            pp.font.name='Arial'; pp.font.size=Pt(22); pp.font.bold=ri in [0,3]
                            pp.font.color.rgb=RGBColor.from_string(WHITE if ri==0 else INK)
                text(sl,'Ward uses a nearest-centroid extension; both K-Means variants fit the full training set.',.85,4.95,11.8,.9,20,GRAY)
                text(sl,'Slightly better in this run; no uncertainty analysis establishes a robust advantage.',.85,5.85,11.8,.8,20,TEAL,True)
            else:
                for j,p in enumerate(points):
                    text(sl,f'{j+1:02}',.7,2+j*.92,.7,.55,25,TEAL,True)
                    text(sl,p,1.6,2+j*.92,10.9,.82,23)
        text(sl,'DATA MINING  •  Source: Rabie El Kharoua / Kaggle / CC BY 4.0',.65,7.03,11.3,.3,9,'9EB3C2' if i==1 else GRAY)
        text(sl,f'{i:02} / {len(items)}',12,7.03,.8,.3,10,'9EB3C2' if i==1 else GRAY)
        sl.notes_slide.notes_text_frame.text=f'Presenter {1 if i<=7 else 2} | approximately 45–50 seconds\n\n'+notes
        transition=OxmlElement('p:transition'); transition.set('spd','med'); transition.append(OxmlElement('p:fade'))
        sl.element.append(transition)
    path=DEST/'Gamer_Behavior_Clustering_English.pptx'
    prs.save(path)
    return path


def main():
    ASSETS.mkdir(parents=True,exist_ok=True)
    s=json.loads((ROOT/'outputs/summary.json').read_text(encoding='utf-8'))
    p=pd.read_csv(ROOT/'outputs/cluster_profiles.csv')
    make_charts(s,p)
    items=content(s,p); path=build_deck(items)
    (DEST/'slide_content_english.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
    # Verify every editable text run and speaker note is English/ASCII-compatible apart from common typography.
    forbidden='ăâđêôơưĂÂĐÊÔƠƯ'
    deck=Presentation(path)
    assert len(deck.slides)==18
    for slide in deck.slides:
        strings=[slide.notes_slide.notes_text_frame.text]
        for sh in slide.shapes:
            if sh.has_text_frame:strings.append(sh.text_frame.text)
            if sh.has_table:strings += [c.text for row in sh.table.rows for c in row.cells]
        assert not any(any(ch in t for ch in forbidden) for t in strings)
    print(path)


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
