"""Generate the three notebooks, then execute them in place.

    python scripts/build_notebooks.py

Notebooks only read from data/ and models/; they never retrain into models/ or mlruns/.
"""
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.v4 import new_code_cell as code
from nbformat.v4 import new_markdown_cell as md
from nbformat.v4 import new_notebook

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks"

SETUP = """import os, sys, warnings
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="whitegrid")
%matplotlib inline
print("working dir:", Path.cwd())"""

eda = [
    md("# 01 - Exploratory data analysis\nUCI Cleveland heart-disease data. Reads `data/heart_cleaned.csv` "
       "(produced by `python -m src.download_data`; no network needed here)."),
    code(SETUP),
    code("from src.download_data import clean, COLUMNS\n"
         "df = pd.read_csv('data/heart_cleaned.csv')\n"
         "print(df.shape)\ndf.head()"),
    md("## Cleaning rules (`src.download_data.clean`)\n`?` becomes NaN and the 0-4 severity label is "
       "binarised (>0 = disease). Check the function on a tiny raw frame:"),
    code("raw = pd.DataFrame([[63,1,1,145,233,1,2,150,0,2.3,3,'0.0','6.0',0],\n"
         "                    [67,1,4,160,286,0,2,108,1,1.5,2,'?','3.0',2]], columns=COLUMNS)\n"
         "clean(raw)"),
    md("## Missing values and class balance"),
    code("print(df.isna().sum()[lambda s: s > 0])\n"
         "print(df['target'].value_counts().rename({0: 'no disease', 1: 'disease'}))\n"
         "print((df['target'].value_counts(normalize=True)*100).round(1))"),
    code("df.describe().T.round(2)"),
    md("## Distributions"),
    code("num = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']\n"
         "fig, axes = plt.subplots(2, 3, figsize=(14, 7))\n"
         "for ax, c in zip(axes.ravel(), num):\n"
         "    sns.histplot(data=df, x=c, hue='target', kde=True, ax=ax, palette='Set1')\n"
         "axes.ravel()[-1].axis('off')\nfig.tight_layout(); plt.show()"),
    code("cats = ['sex', 'cp', 'exang', 'slope', 'ca', 'thal']\n"
         "fig, axes = plt.subplots(2, 3, figsize=(14, 7))\n"
         "for ax, c in zip(axes.ravel(), cats):\n"
         "    sns.countplot(data=df, x=c, hue='target', ax=ax, palette='Set1')\n"
         "fig.tight_layout(); plt.show()"),
    md("## Correlations"),
    code("plt.figure(figsize=(10, 8))\nsns.heatmap(df.corr(), annot=True, fmt='.2f', cmap='vlag', center=0)\n"
         "plt.title('Feature correlation'); plt.show()"),
    code("df.corr()['target'].drop('target').sort_values(ascending=False).round(3)"),
    md("## Engineered feature `hr_reserve`\n`thalach / (220 - age)`; compare it with raw `thalach` "
       "as a separator of the classes."),
    code("from src.features import add_hr_reserve\n"
         "d = add_hr_reserve(df)\n"
         "print(d[['thalach', 'hr_reserve', 'target']].corr()['target'].round(3))\n"
         "sns.boxplot(data=d, x='target', y='hr_reserve'); plt.show()"),
    md("**Takeaways:** classes are near balanced (164/139), so accuracy is meaningful; `thal`, `ca`, "
       "`exang`, `oldpeak`, `cp` and `thalach` carry most of the signal; `fbs` and `chol` are weak; "
       "only 6 cells are missing, so median / most-frequent imputation inside the pipeline is enough."),
]

training = [
    md("# 02 - Feature engineering and model training\nRe-runs the model comparison from `src/train.py` "
       "using the same split (stratified 80/20, seed 42) and CV (5-fold), **without** writing to "
       "`models/` or `mlruns/`, then checks the result against the saved `models/metrics.json`."),
    code(SETUP),
    code("import json, joblib\n"
         "from sklearn.base import clone\n"
         "from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split\n"
         "from src.features import RAW_FEATURES, build_pipeline, feature_names\n"
         "from src.train import GRIDS, SEED, SCORING, holdout_metrics\n"
         "df = pd.read_csv('data/heart_cleaned.csv')\n"
         "X, y = df[RAW_FEATURES], df['target']\n"
         "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)\n"
         "cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)\n"
         "print(len(X_train), len(X_test))"),
    md("## Preprocessing pipeline\nImputation + scaling + one-hot live inside the sklearn `Pipeline`, "
       "so the API applies exactly the same transforms."),
    code("pipe = build_pipeline(GRIDS['logreg'][0])\npipe"),
    md("## Grid search (one config per row, CV on training split only)"),
    code("rows, fitted = [], {}\n"
         "for name, (est, grid) in GRIDS.items():\n"
         "    from sklearn.model_selection import ParameterGrid\n"
         "    for params in ParameterGrid(grid):\n"
         "        p = build_pipeline(clone(est).set_params(**params))\n"
         "        s = cross_validate(p, X_train, y_train, cv=cv, scoring=SCORING)\n"
         "        p.fit(X_train, y_train)\n"
         "        label = f'{name}-' + '-'.join(f'{k}{v}' for k, v in params.items())\n"
         "        fitted[label] = p\n"
         "        rows.append({'run': label, **{f'cv_{m}': s[f'test_{m}'].mean() for m in SCORING},\n"
         "                     'cv_auc_std': s['test_roc_auc'].std(),\n"
         "                     'test_auc': holdout_metrics(y_test, p.predict_proba(X_test)[:, 1], 0.5)['roc_auc']})\n"
         "res = pd.DataFrame(rows).sort_values('cv_roc_auc', ascending=False).round(3)\nres"),
    code("saved = json.load(open('models/metrics.json'))\n"
         "best = res.iloc[0]\n"
         "print('notebook winner :', best['run'], best['cv_roc_auc'])\n"
         "print('saved winner    :', saved['best_run'], round(saved['cv_metrics']['roc_auc'], 3))\n"
         "assert best['run'] == saved['best_run']"),
    code("fig, ax = plt.subplots(figsize=(9, 4))\n"
         "r = res.sort_values('cv_roc_auc')\n"
         "ax.barh(r['run'], r['cv_roc_auc'], xerr=r['cv_auc_std'], color='steelblue')\n"
         "ax.set_xlim(0.8, 0.95); ax.set_xlabel('CV ROC-AUC (mean +/- std)'); fig.tight_layout(); plt.show()"),
    md("## Winner: evaluation, curves and threshold\nLoad the saved bundle and evaluate on the held-out test set."),
    code("bundle = joblib.load('models/model.joblib')\n"
         "print(bundle.keys(), bundle['threshold'], bundle['features'])\n"
         "pl, thr = bundle['pipeline'], bundle['threshold']\n"
         "proba = pl.predict_proba(X_test)[:, 1]\n"
         "pd.DataFrame({'t=0.5': holdout_metrics(y_test, proba, 0.5),\n"
         "              f't={thr}': holdout_metrics(y_test, proba, thr)}).round(3)"),
    code("from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay\n"
         "fig, axes = plt.subplots(1, 3, figsize=(14, 4))\n"
         "RocCurveDisplay.from_predictions(y_test, proba, ax=axes[0]); axes[0].plot([0,1],[0,1],'--',c='grey')\n"
         "for ax, t in zip(axes[1:], (0.5, thr)):\n"
         "    ConfusionMatrixDisplay.from_predictions(y_test, (proba >= t).astype(int), ax=ax, cmap='Blues')\n"
         "    ax.set_title(f'Confusion matrix, t={t}')\n"
         "fig.tight_layout(); plt.show()"),
    code("coef = pd.Series(pl.named_steps['model'].coef_[0], index=feature_names(pl)).sort_values()\n"
         "fig, ax = plt.subplots(figsize=(7, 6))\n"
         "coef.plot.barh(ax=ax, color=['tomato' if v > 0 else 'steelblue' for v in coef])\n"
         "ax.set_title('Logistic regression coefficients (standardised inputs)'); fig.tight_layout(); plt.show()"),
    md("The threshold 0.26 was chosen on out-of-fold training predictions (recall >= 90%), not on the test set."),
]

inference = [
    md("# 03 - Inference\nLoads `models/model.joblib` (dict with `pipeline`, `threshold`, `features`), "
       "predicts directly, then through the FastAPI app in-process (`TestClient`, no network) "
       "and checks both agree."),
    code(SETUP),
    code("import joblib, json\nbundle = joblib.load('models/model.joblib')\n"
         "print({k: (type(v).__name__ if k == 'pipeline' else v) for k, v in bundle.items()})"),
    code("sample = {'age': 57, 'sex': 1, 'cp': 4, 'trestbps': 140, 'chol': 241, 'fbs': 0, 'restecg': 0,\n"
         "          'thalach': 123, 'exang': 1, 'oldpeak': 0.2, 'slope': 2, 'ca': 0, 'thal': 7}\n"
         "low = {'age': 35, 'sex': 0, 'cp': 2, 'trestbps': 110, 'chol': 180, 'fbs': 0, 'restecg': 0,\n"
         "       'thalach': 175, 'exang': 0, 'oldpeak': 0.0, 'slope': 1, 'ca': 0, 'thal': 3}\n"
         "rows = pd.DataFrame([sample, low])[bundle['features']]\n"
         "p = bundle['pipeline'].predict_proba(rows)[:, 1]\n"
         "out = pd.DataFrame({'p_disease': p.round(4), 'prediction': (p >= bundle['threshold']).astype(int)},\n"
         "                   index=['high-risk sample', 'low-risk sample'])\nout"),
    md("## Same payloads through the API (in-process)"),
    code("from fastapi.testclient import TestClient\nfrom src.api import app\n"
         "with TestClient(app) as client:\n"
         "    print(client.get('/health').json())\n"
         "    r1 = client.post('/predict', json=sample); r2 = client.post('/predict', json=low)\n"
         "    bad = client.post('/predict', json={**sample, 'age': 250})\n"
         "    print(r1.status_code, r1.json()); print(r2.status_code, r2.json())\n"
         "    print(bad.status_code, bad.json()['detail'][0]['msg'])\n"
         "assert abs(r1.json()['probability_disease'] - p[0]) < 1e-3\n"
         "assert abs(r2.json()['probability_disease'] - p[1]) < 1e-3\n"
         "print('API and direct model agree')"),
    md("## Batch scoring of the whole cleaned dataset"),
    code("df = pd.read_csv('data/heart_cleaned.csv')\n"
         "pp = bundle['pipeline'].predict_proba(df[bundle['features']])[:, 1]\n"
         "df['pred'] = (pp >= bundle['threshold']).astype(int)\n"
         "print(pd.crosstab(df['target'], df['pred'], rownames=['actual'], colnames=['predicted']))\n"
         "print('note: includes training rows, so this is not a generalisation estimate')"),
]


def main() -> None:
    NB.mkdir(exist_ok=True)
    for fname, cells in [("01_eda.ipynb", eda), ("02_training.ipynb", training),
                         ("03_inference.ipynb", inference)]:
        nb = new_notebook(cells=cells, metadata={
            "kernelspec": {"name": "heart-mlops-venv", "display_name": "heart-mlops (.venv)",
                           "language": "python"}})
        ExecutePreprocessor(timeout=600, kernel_name="heart-mlops-venv").preprocess(
            nb, {"metadata": {"path": str(NB)}})
        nbformat.write(nb, NB / fname)
        print("executed", fname)


if __name__ == "__main__":
    main()
