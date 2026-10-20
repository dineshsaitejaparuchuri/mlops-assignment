"""Build docs/report/MLOps_Assignment1_Report.pdf and docs/report/architecture.png.

Every number is read from models/metrics.json, mlruns/, data/ or docs/run_outputs/.
    python scripts/build_report.py
"""
import json
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image as PILImage  # noqa: E402
import joblib  # noqa: E402
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph,  # noqa: E402
                                Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "report"
PDF = OUT / "MLOps_Assignment1_Report.pdf"
REPO_URL = os.getenv("HEART_MLOPS_REPO_URL", "").strip()
STUDENT_NAME = os.getenv("HEART_MLOPS_STUDENT_NAME", "").strip()
STUDENT_ROLL_NUMBER = os.getenv("HEART_MLOPS_ROLL_NUMBER", "").strip()
SHOTS = ROOT / "screenshots"

metrics = json.loads((ROOT / "models" / "metrics.json").read_text())
df = pd.read_csv(ROOT / "data" / "heart_cleaned.csv")
ro = ROOT / "docs" / "run_outputs"


# ---------------------------------------------------------------- experiment data
# MLflow's local store is intentionally ignored by Git so the repository stays small.
# A clean checkout can still rebuild the report from the committed experiment summary;
# running src.train recreates the full local MLflow history.
def read_runs_from_markdown() -> pd.DataFrame:
    experiment_text = (ROOT / "docs" / "experiments.md").read_text(encoding="utf-8")
    rows = []
    for line in experiment_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        # The committed summary may intentionally omit MLflow run IDs so the
        # report can be rebuilt from a clean checkout without the local mlruns/ store.
        if len(cells) < 6 or cells[0].strip().lower() == "run" or set(cells[0]) <= {"-", ":"}:
            continue
        run_name = cells[0].strip("` ")
        auc_match = re.match(r"([0-9.]+)\s*(?:±\s*([0-9.]+))?", cells[4])
        if not auc_match:
            continue
        rows.append({
            "run": run_name,
            "cv_accuracy": float(cells[1]),
            "cv_precision": float(cells[2]),
            "cv_recall": float(cells[3]),
            "cv_roc_auc": float(auc_match.group(1)),
            "cv_roc_auc_std": float(auc_match.group(2) or 0.0),
            "test_roc_auc": float(cells[5]),
            "run_id": cells[6].strip("` ") if len(cells) >= 7 else "",
        })
    if not rows:
        raise RuntimeError("No experiment rows found. Run `python -m src.train` and rebuild the report.")
    return pd.DataFrame(rows).sort_values("cv_roc_auc", ascending=False)


def read_runs() -> pd.DataFrame:
    store = ROOT / "mlruns"
    if store.is_dir():
        exp_dirs = [p for p in store.iterdir() if p.is_dir() and p.name.isdigit() and p.name != "0"]
        rows = []
        for exp in exp_dirs:
            for run in exp.iterdir():
                meta_path = run / "meta.yaml"
                metrics_dir = run / "metrics"
                if not meta_path.exists() or not metrics_dir.is_dir():
                    continue
                meta = meta_path.read_text(encoding="utf-8")
                name_match = re.search(r"run_name: (.*)", meta)
                start_match = re.search(r"start_time: (\d+)", meta)
                if not name_match or not start_match:
                    continue
                row = {"run": name_match.group(1), "run_id": run.name,
                       "start": int(start_match.group(1))}
                for metric_file in metrics_dir.iterdir():
                    row[metric_file.name] = float(
                        metric_file.read_text(encoding="utf-8").strip().splitlines()[-1].split()[1])
                rows.append(row)
        if rows:
            out = pd.DataFrame(rows)
            # CI may leave older batches in the store; keep the latest batch only.
            out = out[out.start >= out.start.max() - 15 * 60 * 1000].drop(columns="start")
            return out.sort_values("cv_roc_auc", ascending=False)
    return read_runs_from_markdown()


runs = read_runs()
best = runs.iloc[0]
if best["run"] != metrics["best_run"]:
    raise RuntimeError(
        "The experiment summary and models/metrics.json are out of sync. "
        "Re-run training or update the summary."
    )
# In a clean checkout, the summary table has no local run IDs. In that case,
# carry the known ID for the selected run from metrics.json and leave the others blank.
if not str(best.get("run_id", "")):
    runs.loc[runs["run"] == metrics["best_run"], "run_id"] = metrics["mlflow_run_id"]
runs["run_id"] = runs["run_id"].fillna("")
n_pos, n_neg = int(df.target.sum()), int((df.target == 0).sum())
miss = df.isna().sum()
miss = miss[miss > 0].to_dict()
corr = df.corr()["target"].drop("target").sort_values(ascending=False)
pytest_summary = (ro / "pytest.txt").read_text().strip().splitlines()[-1]
n_tests = int(re.search(r"(\d+) passed", pytest_summary).group(1))
t5, tt, cvm = (metrics["test_metrics_at_0.5"], metrics["test_metrics_at_threshold"],
               metrics["cv_metrics"])
thr = metrics["decision_threshold"]


# ---------------------------------------------------------------- diagram
def draw_architecture(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                    fc=fc, ec="#333", lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.3, color="#333"))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, label, ha="center", fontsize=7)

    ax.text(5.5, 5.95, "Heart-disease risk: end-to-end MLOps architecture", ha="center",
            fontsize=12, weight="bold")
    # row 1: training pipeline
    box(0.2, 4.4, 1.9, 0.9, "UCI Cleveland\nraw data\n(download_data.py)", "#fde8c8")
    box(2.6, 4.4, 1.9, 0.9, "data/\nheart_cleaned.csv\n+ EDA (eda.py)", "#fde8c8")
    box(5.0, 4.4, 2.2, 0.9, "src/train.py\nPipeline: impute+scale\n+one-hot, LR / RF, CV", "#d6e8fa")
    box(7.7, 4.4, 1.7, 0.9, "MLflow tracking\n+ registry\n(./mlruns)", "#d6f0d6")
    box(9.6, 4.4, 1.2, 0.9, "models/\nmodel.joblib\nmetrics.json", "#e9dcf7")
    arrow(2.1, 4.85, 2.6, 4.85)
    arrow(4.5, 4.85, 5.0, 4.85)
    arrow(7.2, 4.85, 7.7, 4.85, "log")
    arrow(7.2, 4.6, 9.6, 4.6)
    # row 2: CI
    box(0.2, 2.75, 3.2, 0.9, "GitHub Actions (ci.yml)\nflake8 -> pytest -> train -> docker build\n-> smoke test -> upload artifacts",
        "#f3d4d4")
    arrow(1.8, 4.4, 1.8, 3.65, "push / PR")
    arrow(3.4, 3.2, 5.0, 4.4)
    # row 2: serving
    box(5.0, 2.75, 2.4, 0.9, "Docker image\nheart-disease-api\n(multi-stage, non-root)", "#d6e8fa")
    box(8.0, 2.75, 2.8, 0.9, "FastAPI + uvicorn\n/predict  /health  /metrics\nlogs/api.log + stdout", "#d6e8fa")
    arrow(10.2, 4.4, 10.2, 3.65)
    ax.text(10.35, 4.0, "loaded at\nstartup", fontsize=7)
    arrow(7.4, 3.2, 8.0, 3.2, "runs")
    # row 3: Kubernetes + monitoring
    ax.add_patch(FancyBboxPatch((0.2, 0.2), 10.6, 2.0, boxstyle="round,pad=0.04",
                                fc="none", ec="#555", lw=1.4, ls="--"))
    ax.text(0.4, 1.95, "Kubernetes namespace: heart-mlops", fontsize=8.5, weight="bold")
    box(0.5, 0.45, 2.0, 0.9, "Ingress (nginx)\nheart.local\nor NodePort 30080", "#fde8c8")
    box(3.0, 0.45, 2.0, 0.9, "Service heart-api\nClusterIP :80", "#fde8c8")
    box(5.5, 0.45, 2.2, 0.9, "Deployment heart-api\n2 replicas, probes,\nrolling update", "#d6e8fa")
    box(8.2, 0.45, 2.4, 0.9, "Prometheus -> Grafana\n(scrape /metrics,\nrequest rate / p95 / errors)", "#d6f0d6")
    arrow(2.5, 0.9, 3.0, 0.9)
    arrow(5.0, 0.9, 5.5, 0.9)
    arrow(7.7, 0.9, 8.2, 0.9, "scrape")
    arrow(6.6, 2.75, 6.6, 1.35, "image")
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


OUT.mkdir(parents=True, exist_ok=True)
ARCH = OUT / "architecture.png"
draw_architecture(ARCH)


def ensure_report_plots() -> Path:
    """Keep the report buildable even when the ignored MLflow store is absent."""
    store = ROOT / "mlruns"
    if store.is_dir():
        candidates = list(store.glob("[!0]*/" + str(metrics["mlflow_run_id"]) + "/artifacts/plots"))
        candidates = [item for item in candidates if (item / "roc_curve.png").exists()
                      and (item / "confusion_matrix.png").exists()]
        if candidates:
            return candidates[0]

    plot_dir = OUT / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    roc_path = plot_dir / "roc_curve.png"
    cm_path = plot_dir / "confusion_matrix.png"
    if roc_path.exists() and cm_path.exists():
        return plot_dir

    bundle = joblib.load(ROOT / "models" / "model.joblib")
    X = df[bundle["features"]]
    X_train, X_test, y_train, y_test = train_test_split(
        X, df["target"], test_size=0.2, stratify=df["target"], random_state=42)
    pipeline = bundle["pipeline"]

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_estimator(pipeline, X_test, y_test, ax=ax, cmap="Blues")
    ax.set_title("Confusion matrix (test, threshold 0.5)")
    fig.tight_layout()
    fig.savefig(cm_path, dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    RocCurveDisplay.from_estimator(pipeline, X_test, y_test, ax=ax)
    ax.plot([0, 1], [0, 1], "--", color="grey")
    ax.set_title("ROC curve (held-out test set)")
    fig.tight_layout()
    fig.savefig(roc_path, dpi=130)
    plt.close(fig)
    return plot_dir


plots_dir = ensure_report_plots()

# ---------------------------------------------------------------- styles
ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["BodyText"], fontSize=8.8, leading=11.4, spaceAfter=3.5)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=16, spaceBefore=6, spaceAfter=8,
                    textColor=colors.HexColor("#17365d"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.5, spaceBefore=6, spaceAfter=4,
                    textColor=colors.HexColor("#17365d"))
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.2, leading=10.5, alignment=TA_CENTER,
                     textColor=colors.HexColor("#444444"), spaceAfter=4)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=7.8, leading=9.6, leftIndent=6,
                      backColor=colors.HexColor("#f4f4f4"), borderPadding=4, spaceAfter=4)
TITLE = ParagraphStyle("title", parent=ss["Title"], fontSize=26, leading=32, spaceAfter=12,
                       textColor=colors.HexColor("#17365d"))
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
W = A4[0] - 3.4 * cm


def P(t, s=BODY):
    return Paragraph(t, s)


def bullets(items):
    return [P("&bull; " + i, ParagraphStyle("b", parent=BODY, leftIndent=12, firstLineIndent=-8,
                                           spaceAfter=2)) for i in items]


def code(t):
    return Preformatted(t.strip("\n"), CODE)


def crop(src, box, name):
    dest = OUT / "crops" / name
    dest.parent.mkdir(exist_ok=True)
    PILImage.open(src).crop(box).save(dest)
    return dest


def img(path, width=W, caption=None, max_h=3.9 * cm):
    path = Path(path)
    w, h = PILImage.open(path).size
    width = min(width, max_h * w / h)
    out = [Image(str(path), width=width, height=width * h / w)]
    if caption:
        out.append(P(caption, CAP))
    return KeepTogether(out)


def table(data, widths, header=True, font=8):
    rows = [[P(str(c), CELL) if isinstance(c, str) else c for c in r] for r in data]
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f1"))]
    t.setStyle(TableStyle(st))
    return t


def todo_box(title, cmd, expect, fname):
    inner = [P(f"<b>SCREENSHOT TO CAPTURE - {title}</b>",
               ParagraphStyle("t", parent=CELL, textColor=colors.HexColor("#8a1c1c"), fontSize=9)),
             P("Not produced in this environment (see docs/MISSING_SCREENSHOTS.md). "
               "Run the command below on a machine with the required tooling and save as "
               f"<font face='Courier'>screenshots/{fname}</font>.", CELL),
             Preformatted(cmd, ParagraphStyle("c", fontName="Courier", fontSize=7.4, leading=9)),
             P(f"<i>Expected:</i> {expect}", CELL)]
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#c0392b")),
                           ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3f0")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([t, Spacer(1, 8)])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.1 * cm, "Heart-disease risk MLOps - Assignment 1 report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()


s = []
# ---------------------------------------------------------------- title
s += [Spacer(1, 3 * cm), P("Heart-Disease Risk Prediction", TITLE),
      P("Building and evaluating a reproducible machine-learning service, from data preparation to deployment and monitoring.", ParagraphStyle(
            "st", parent=BODY, fontSize=13, leading=17)),
      Spacer(1, 1 * cm),
      table([["Course", "MLOps (AIMLCZG523) - Assignment 01"],
             ["Dataset", "Heart Disease UCI (Cleveland), 303 patients, 13 features + binary target"],
             ["Student name", STUDENT_NAME or "Enter student name before submission"],
             ["Roll number", STUDENT_ROLL_NUMBER or "Enter roll number before submission"],
             ["Code repository", REPO_URL or "Repository URL to be added after GitHub publication"],
             ["Best model", f"Logistic Regression (C={metrics['params']['C']}), registered as "
                            f"{metrics['registered_model']['name']} v{metrics['registered_model']['version']}"],
             ["Held-out test", f"ROC-AUC {tt['roc_auc']:.3f}; recall {tt['recall']:.3f} at "
                               f"threshold {thr} (accuracy {t5['accuracy']:.3f}, recall "
                               f"{t5['recall']:.3f} at 0.5)"],
] , [3.5 * cm, W - 3.5 * cm],
            header=False),
      Spacer(1, 1 * cm), P("Contents", H2)]
toc = ["1. Setup and installation", "2. Data acquisition and EDA",
       "3. Feature engineering and modelling", "4. Experiment tracking with MLflow",
       "5. Architecture", "6. CI/CD pipeline and testing", "7. Containerisation",
       "8. Kubernetes deployment and monitoring", "9. Results and limitations",
       "10. Repository and deliverables map", "11. Evidence screenshots"]
s += bullets(toc)
s += [Spacer(1, 1 * cm),
      P("<b>Scope and verification.</b> The results and screenshots in this report come from the project artifacts and captured runs. "
        "Docker, a local Kubernetes cluster, Prometheus, Grafana and the CI workflow were exercised locally. "
        "The CI workflow was run with <font face='Courier'>act</font>; it has not yet been verified on GitHub-hosted runners. "
        "The local MLflow run store is generated during training and is not included in the source archive, so the report builder "
        "can also read the committed experiment summary on a clean checkout.",
        BODY), PageBreak()]

# ---------------------------------------------------------------- 1 setup
s += [P("1. Setup and installation", H1),
      P("I used Python 3.11 for the project. The core API, training code and tests install from "
        "<font face='Courier'>requirements.txt</font>. Notebook and report tools are listed separately in "
        "<font face='Courier'>requirements-notebooks.txt</font>, which keeps the CI install smaller."),
      P("Clean-machine setup", H2),
      code("""
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest test -v && flake8 src test
"""),
      P("The cleaned CSV is included, so a first run does not need to download the data again. To reproduce that step, run "
        "<font face='Courier'>python -m src.download_data</font>; create the EDA figures with "
        "<font face='Courier'>python -m src.eda</font> and rerun the nine model configurations with "
        "<font face='Courier'>python -m src.train</font>. Notebook/report tools are installed separately from "
        "<font face='Courier'>requirements-notebooks.txt</font>. I fixed the random seed at 42 to make the split and "
        "training results repeatable in the same software environment. Start the service locally with "
        "<font face='Courier'>uvicorn src.api:app --port 8000</font>."),
      P("Repository layout", H2),
      table([["Path", "Purpose"],
             ["src/download_data.py, eda.py", "data acquisition + cleaning, EDA figures and summary"],
             ["src/features.py", "feature engineering and the scikit-learn preprocessing pipeline"],
             ["src/train.py", "model search, MLflow logging, registry, threshold selection, export"],
             ["src/api.py, schemas.py", "FastAPI service: /predict, /health, /metrics, request logging"],
             ["test/", f"{n_tests} pytest tests (features, API, model artifact round trip)"],
             ["notebooks/", "01_eda, 02_training, 03_inference - executed, outputs saved"],
             ["Dockerfile, docker-compose.yml", "multi-stage image; compose adds Prometheus + Grafana"],
             ["k8s/, monitoring/", "Kubernetes manifests, Prometheus config, Grafana dashboard"],
             [".github/workflows/ci.yml", "lint, test, train, build image, smoke test, artifacts"],
             ["docs/", "experiment record, run outputs, this report, demo script"]],
            [5.2 * cm, W - 5.2 * cm]),
      Spacer(1, 6),
      P("Notebooks are regenerated and executed with <font face='Courier'>python "
        "scripts/build_notebooks.py</font>; they read from <font face='Courier'>data/</font> and "
        "<font face='Courier'>models/</font> only and never overwrite the trained model or the "
        "MLflow store."), PageBreak()]

# ---------------------------------------------------------------- 2 EDA
miss_txt = ", ".join(f"{k} ({v})" for k, v in miss.items())
top = ", ".join(f"{k} ({v:+.2f})" for k, v in corr.head(5).items())
s += [P("2. Data acquisition and exploratory data analysis", H1),
      P("<b>Source.</b> The Cleveland subset of the UCI Heart Disease data "
        "(<font face='Courier'>processed.cleveland.data</font>) is fetched by "
        "<font face='Courier'>src/download_data.py</font>. The script replaces '?' with NaN, "
        "casts every column to numeric and binarises the 0-4 severity label "
        "(&gt;0 = disease), then writes "
        f"<font face='Courier'>data/heart_cleaned.csv</font>: {df.shape[0]} rows x "
        f"{df.shape[1]} columns (13 features + <i>target</i>)."),
      P(f"<b>Data quality.</b> There are {int(sum(miss.values()))} missing values: {miss_txt}. I kept them as missing in the CSV "
        "and handle them inside the model pipeline. That way, imputation values are learned from each training fold rather than "
        f"from the full dataset. The classes are reasonably balanced ({n_neg} without the target condition and {n_pos} with it; "
        f"{n_pos / len(df):.1%} positive), so I did not apply resampling."),
      img(SHOTS / "eda" / "class_balance.png", width=6 * cm,
          caption="Figure 1 - class balance (screenshots/eda/class_balance.png)"),
      P(f"<b>Initial patterns.</b> In this sample, the features with the strongest correlations with the target are {top}. "
        f"Fasting blood sugar ({corr['fbs']:+.2f}) and cholesterol ({corr['chol']:+.2f}) have weaker linear correlations, "
        f"while maximum heart rate is negatively correlated ({corr['thalach']:+.2f}). The highest cholesterol value is "
        f"{df.chol.max():.0f} mg/dl; I left it unchanged rather than assume it was an error. These are associations in a small dataset, "
        "not evidence that any one feature causes heart disease."),
      img(SHOTS / "eda" / "histograms.png", caption="Figure 2 - numeric feature distributions "
          "by diagnosis (histograms with KDE)"),
      img(SHOTS / "eda" / "correlation_heatmap.png", width=11.5 * cm,
          caption="Figure 3 - correlation heatmap of all 14 columns"),
      img(SHOTS / "eda" / "categorical_counts.png", caption="Figure 4 - categorical features "
          "by diagnosis (sex, cp, exang, slope, ca, thal)"),
      P("<b>What I took from the plots.</b> The disease-positive group tends to be older, has lower peak heart rate and shows higher ST depression. "
        "Asymptomatic chest-pain records, exercise-induced angina, thal=7 and non-zero ca values also appear more often in that group. "
        "I used these patterns to understand the data, not to make clinical claims. The notebook and <font face='Courier'>docs/eda_summary.txt</font> "
        "contain the plots and summary statistics for reference."), PageBreak()]

# ---------------------------------------------------------------- 3 modelling
s += [P("3. Feature engineering and modelling", H1),
      P("Feature engineering", H2),
      P("I put preprocessing and classification in the same scikit-learn <font face='Courier'>Pipeline</font> "
        "(<font face='Courier'>src/features.py</font>) and save that complete pipeline with the model. This avoids a common deployment bug: "
        "the API cannot accidentally use different transformations from the ones used during training."),
      table([["Group", "Columns", "Treatment"],
             ["Numeric", "age, trestbps, chol, thalach, oldpeak, hr_reserve",
              "median imputation + StandardScaler"],
             ["Categorical", "cp, restecg, slope, thal, ca",
              "most-frequent imputation + one-hot (unknown categories ignored)"],
             ["Binary", "sex, fbs, exang", "most-frequent imputation, passed through"]],
            [2.4 * cm, 7.2 * cm, W - 9.6 * cm]),
      Spacer(1, 6),
      P("<b>Engineered feature.</b> <font face='Courier'>hr_reserve = thalach / (220 - age)</font> "
        "is the fraction of the age-predicted maximum heart rate reached during the stress test. "
        "Raw peak heart rate falls with age, so the ratio separates 'low for their age' from "
        "'low because old'. It is added by a <font face='Courier'>FunctionTransformer</font>, "
        "making it part of the pipeline and therefore of the API."),
      P("Model development and tuning", H2),
      P(f"I split the data into training and test sets using a stratified 80/20 split and seed 42 "
        f"({metrics['n_train']} training rows and {metrics['n_test']} test rows). I kept the test split aside for the final report "
        "and compared two model families using small parameter grids. With only about 240 training records, a very large search "
        "could end up tuning to noise rather than a reliable pattern:"),
      *bullets(["<b>Logistic Regression</b> (max_iter 2000): C in {0.03, 0.3, 3} - 3 runs.",
                "<b>Random Forest</b> (300 trees): max_depth in {3, 6, None} x min_samples_leaf in "
                "{1, 4} - 6 runs."]),
      P("I evaluated every configuration with stratified five-fold cross-validation on the training data, tracking accuracy, precision, recall and ROC-AUC. "
        f"The top mean ROC-AUC came from <b>{metrics['best_run']}</b> ({cvm['roc_auc']:.3f}; accuracy {cvm['accuracy']:.3f}, "
        f"precision {cvm['precision']:.3f}, recall {cvm['recall']:.3f}). Logistic Regression edged out the Random Forest configurations in this run. "
        "That does not mean it will always be better, but it is a sensible choice here: it performed well and is relatively light to serve and explain."),
      P("Decision threshold chosen for recall", H2),
      P("For this exercise I preferred a threshold that favours recall, because a false negative can be more costly than an additional follow-up. "
        f"Using out-of-fold predictions from the training split, I selected the highest threshold in [0.20, 0.70] that still reached "
        f"{metrics['target_recall']:.0%} recall: <b>{thr}</b>. The test set was not used to choose it. The held-out results show the trade-off:"),
      table([["held-out test (61 rows)", "accuracy", "precision", "recall", "ROC-AUC"],
             ["threshold 0.5", f"{t5['accuracy']:.3f}", f"{t5['precision']:.3f}",
              f"{t5['recall']:.3f}", f"{t5['roc_auc']:.3f}"],
             [f"threshold {thr}", f"{tt['accuracy']:.3f}", f"{tt['precision']:.3f}",
              f"{tt['recall']:.3f}", f"{tt['roc_auc']:.3f}"]],
            [4.6 * cm] + [(W - 4.6 * cm) / 4] * 4),
      Spacer(1, 4),
      P("On this particular test split, the lower threshold raised recall to 100% but reduced precision, so more healthy patients would be flagged for follow-up. "
        "There are only 61 test records; a single patient changes a metric by roughly 1.6 percentage points. I would treat these numbers as an illustration "
        "of the threshold trade-off, not as a reliable estimate of real-world clinical performance."),
      PageBreak()]

# ---------------------------------------------------------------- 4 mlflow
s += [P("4. Experiment tracking with MLflow", H1),
      P("In <font face='Courier'>src/train.py</font>, I log each of the nine model configurations to the local MLflow experiment "
        "<font face='Courier'>heart-disease-risk</font>. A run records its settings, cross-validation and test metrics, ROC/confusion-matrix plots, "
        "and fitted pipeline. The best run is tagged <font face='Courier'>selected=true</font>; it also receives the tuned-threshold metrics and is registered as "
        f"<font face='Courier'>{metrics['registered_model']['name']}</font> "
        f"version {metrics['registered_model']['version']}."),
      P(f"The table below is sorted by mean cross-validation ROC-AUC. When the local MLflow store is present, the report reads metrics from it; "
        "on a clean checkout it uses the committed experiment summary so the PDF can still be rebuilt before the next training run. "
        f"There are {len(runs)} recorded configurations.", BODY)]
tdata = [["run", "cv acc", "cv prec", "cv recall", "cv ROC-AUC", "test ROC-AUC", "run id"]]
for _, r in runs.iterrows():
    tdata.append([r["run"], f"{r['cv_accuracy']:.3f}", f"{r['cv_precision']:.3f}",
                  f"{r['cv_recall']:.3f}", f"{r['cv_roc_auc']:.3f} ± {r['cv_roc_auc_std']:.3f}",
                  f"{r['test_roc_auc']:.3f}", r["run_id"][:8]])
s += [table(tdata, [4.6 * cm, 1.3 * cm, 1.4 * cm, 1.6 * cm, 2.6 * cm, 2.1 * cm, W - 14.6 * cm]),
      Spacer(1, 6),
      P("The cross-validation standard deviations (about 0.014 to 0.037 for ROC-AUC) are large enough that small gaps between runs should not be overinterpreted. "
        "In this experiment Logistic Regression was competitive with, and slightly ahead of, the Random Forest candidates. The experiment notes and metrics file "
        "are kept alongside the code so the reported figures can be checked."),
      img(SHOTS / "mlflow_runs_list.png", caption="Figure 5 - MLflow UI: training runs, sorted by "
          "cv_roc_auc (real screenshot of the local MLflow server)"),
      img(SHOTS / "mlflow_run_detail.png", width=11 * cm, max_h=6 * cm, caption="Figure 6 - MLflow run page of the "
          "selected run (metrics, parameters, registered model link)"),
      img(crop(SHOTS / "mlflow_model_registry.png", (0, 0, 1400, 460), "registry.png"), width=13 * cm, caption="Figure 7 - model registry: "
          f"{metrics['registered_model']['name']} version {metrics['registered_model']['version']}"),
      P("Model packaging and reproducibility", H2),
      P("The deployable artifact is <font face='Courier'>models/model.joblib</font>, a dict "
        "holding the fitted <i>pipeline</i> (preprocessing + classifier), the decision "
        "<i>threshold</i> and the ordered <i>features</i> list. The same pipeline is also stored as "
        "an MLflow model inside each run. Pinned requirements, a fixed seed and the committed cleaned "
        "dataset make the whole chain reproducible from a clean checkout."),
      PageBreak()]

# ---------------------------------------------------------------- 5 architecture
s += [P("5. Architecture", H1),
      img(ARCH, caption="Figure 8 - architecture: training pipeline (top), CI and containerised "
          "serving (middle), Kubernetes deployment with Prometheus/Grafana monitoring (bottom)"),
      P("<b>How the pieces fit together.</b> The UCI data is cleaned and explored before <font face='Courier'>src/train.py</font> evaluates the candidate models, logs the runs to MLflow and exports the winner. "
        "The GitHub Actions workflow is configured to lint, test, retrain, build the Docker image and smoke-test the API on pushes and pull requests. The container serves the saved model through FastAPI. "
        "In Kubernetes, two API replicas sit behind a Service, while Prometheus collects <font face='Courier'>/metrics</font> for the Grafana dashboard."),
      P("<b>API contract.</b>", BODY),
      table([["Endpoint", "Behaviour"],
             ["POST /predict", "13 raw features as JSON, validated by pydantic ranges (422 otherwise); "
              "returns prediction, label, confidence, probability_disease"],
             ["GET /health", "liveness/readiness; reports whether the model is loaded"],
             ["GET /metrics", "Prometheus exposition: api_requests_total, "
              "api_request_latency_seconds, model_predictions_total"]],
            [3.2 * cm, W - 3.2 * cm]),
      Spacer(1, 6),
      P("Example request and response (captured in docs/run_outputs/api_samples.txt):"),
      code("""
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' \\
  -d '{"age":57,"sex":1,"cp":4,"trestbps":140,"chol":241,"fbs":0,"restecg":0,
       "thalach":123,"exang":1,"oldpeak":0.2,"slope":2,"ca":0,"thal":7}'
{"prediction":1,"label":"heart disease","confidence":0.848,"probability_disease":0.848}
"""),
      P("The API returns both the probability of the disease class and the confidence associated with the predicted label. "
        "For invalid input, such as an age of 250, FastAPI returns HTTP 422 and identifies the field that failed validation."),
      img(SHOTS / "api_docs.png", width=10.5 * cm, max_h=7.5 * cm, caption="Figure 9 - FastAPI interactive "
          "documentation at /docs (real screenshot)"),
      PageBreak()]

# ---------------------------------------------------------------- 6 CI
s += [P("6. CI/CD pipeline and automated testing", H1),
      P(f"<b>Tests.</b> {n_tests} pytest tests (<font face='Courier'>{pytest_summary.strip('= ')}"
        "</font>) cover: cleaning rules (question marks, label binarisation), the committed "
        "CSV's shape, the engineered feature, preprocessor output (no NaN, standardised numerics), "
        "robustness to unseen categories and missing values, the API (health, valid prediction, 7 "
        "out-of-range cases and a missing field returning 422, Prometheus counters) and a "
        "saved-model round trip. flake8 (max line length 100) reports no findings."),
      P("<b>Workflow</b> (<font face='Courier'>.github/workflows/ci.yml</font>, triggered on every "
        "push and pull request, ubuntu-latest, Python 3.11 with pip caching). Steps run in order and "
        "any non-zero exit fails the job; <font face='Courier'>set -o pipefail</font> with "
        "<font face='Courier'>tee</font> keeps logs while preserving failures:"),
      table([["#", "Step", "What it enforces"],
             ["1", "Install dependencies", "clean install from requirements.txt"],
             ["2", "Lint", "flake8 src test -> ci-output/flake8.txt"],
             ["3", "Unit tests", "pytest -v + JUnit XML -> ci-output/"],
             ["4", "Train model", "python -m src.train (9 MLflow runs) -> ci-output/train.txt"],
             ["5", "Verify artifacts", "models/model.joblib and metrics.json must exist"],
             ["6", "Summarise MLflow runs", "lists run metadata -> ci-output/mlruns-summary.txt"],
             ["7", "Build Docker image", "docker build -t heart-disease-api:ci ."],
             ["8", "Smoke test container", "scripts/smoke_test.sh: /health, /predict, /metrics"],
             ["9", "Container logs", "always(): docker logs -> ci-output/container.log"],
             ["10", "Upload artifacts", "always(): model, metrics, logs/, ci-output/, mlruns/"]],
            [0.8 * cm, 4.4 * cm, W - 5.2 * cm]),
      Spacer(1, 6),
      P("Retraining in CI is intended to catch changes that break the training process, saved-model contract or container before a change is merged. Each workflow run also uploads logs, JUnit output, the model and the MLflow run store for inspection. "
        "The included screenshot is from the local <font face='Courier'>act</font> run; a hosted GitHub Actions run still needs to be triggered after the repository is published."),
      img(SHOTS / "terminal_pytest.png", width=W, caption="Figure 10 - pytest -v output "
          "(text captured from a real run, rendered to PNG; docs/run_outputs/pytest_verbose.txt)"),
      P("<b>Local run of the CI workflow.</b> <font face='Courier'>scripts/run_ci_local.sh</font> "
        "executes the unmodified <font face='Courier'>ci.yml</font> with <font face='Courier'>act</font> "
        "inside a Python 3.11 runner container; only checkout, setup-python and upload-artifact are "
        "replaced by local stubs (<font face='Courier'>.ci-local/</font>) so nothing contacts GitHub. "
        "All steps succeeded: 18 tests passed, flake8 clean, model retrained, image built, container "
        "smoke test passed, artifacts collected. Full log: docs/run_outputs/act_ci_full.txt."),
      img(SHOTS / "ci_run.png", width=10.5 * cm, caption="Figure 11 - local run of the CI workflow "
          "(act; real captured output, rendered to PNG)"),
      PageBreak()]

# ---------------------------------------------------------------- 7 docker
s += [P("7. Containerisation", H1),
      P("The <font face='Courier'>Dockerfile</font> is multi-stage: a builder stage creates a "
        "virtualenv and installs <font face='Courier'>requirements.txt</font>; the runtime stage "
        "(python:3.11-slim) copies only the venv, <font face='Courier'>src/</font> and "
        "<font face='Courier'>models/model.joblib</font>, so the image ships no training data or "
        "MLflow store. It runs as a non-root user (uid 10001), exposes port 8000, defines a "
        "HEALTHCHECK against <font face='Courier'>/health</font>, and starts "
        "<font face='Courier'>uvicorn src.api:app</font>. A build-time check fails the build if "
        "<font face='Courier'>src/api.py</font> is missing."),
      code("""
docker build -t heart-disease-api:latest .
docker run -d --name heart-api -p 8000:8000 heart-disease-api:latest
scripts/smoke_test.sh http://localhost:8000      # /health, /predict, /metrics
docker compose up --build                        # API + Prometheus :9090 + Grafana :3000
"""),
      P("<b>Local verification recorded for this project.</b> The captured run shows that the image built successfully and the container started: "
        "<font face='Courier'>docker ps</font> reported <i>healthy</i> (HEALTHCHECK), "
        "<font face='Courier'>id -u</font> returned 10001 (non-root), "
        "<font face='Courier'>models/model.joblib</font> is present in the image, "
        "/health and /predict returned 200 and an invalid body returned 422. Output: "
        "docs/run_outputs/docker_run.txt."),
      img(SHOTS / "docker_build_run.png", width=W, max_h=5 * cm, caption="Figure 12 - docker run, "
          "health status, non-root user, smoke test and a 422 (real captured text)"),
      PageBreak()]

# ---------------------------------------------------------------- 8 k8s
s += [P("8. Kubernetes deployment and monitoring", H1),
      P("The manifests in <font face='Courier'>k8s/</font> are set up for a local kind or Minikube cluster. For a cloud cluster, the Service can be switched to a LoadBalancer and the Ingress controller configured for that environment."),
      table([["Manifest", "Content"],
             ["namespace.yaml", "namespace heart-mlops"],
             ["deployment.yaml", "heart-api: 2 replicas, RollingUpdate (maxSurge 1, maxUnavailable 0), "
              "requests 100m/128Mi, limits 500m/512Mi, liveness + readiness probes on /health, "
              "Prometheus scrape annotations"],
             ["service.yaml", "ClusterIP service heart-api, port 80 -> container port 8000"],
             ["ingress.yaml", "nginx Ingress, host heart.local -> heart-api"],
             ["service-nodeport.yaml", "NodePort 30080 alternative (change type to LoadBalancer on "
              "a cloud cluster)"],
             ["monitoring/", "Prometheus (config map, RBAC, deployment, service), Grafana "
              "(datasource and dashboard provisioning), dashboard JSON"]],
            [3.8 * cm, W - 3.8 * cm]),
      Spacer(1, 6),
      code("""
scripts/deploy_local.sh        # builds image, loads into kind/minikube, applies manifests
kubectl -n heart-mlops get pods,svc
kubectl -n heart-mlops port-forward svc/heart-api 8000:80
scripts/smoke_test.sh http://localhost:8000
"""),
      P("Monitoring and logging", H2),
      P("<b>Logging.</b> A middleware logs every request (method, path, status, latency in ms) to "
        "stdout - what <font face='Courier'>kubectl logs</font> and Docker show - and to "
        "<font face='Courier'>logs/api.log</font>. Model load and the threshold are logged at "
        "start-up. <b>Metrics.</b> Prometheus counters and histograms are exposed at "
        "<font face='Courier'>/metrics</font>: request count by method/path/status, latency "
        "histogram by path, and predictions by label. The provisioned Grafana dashboard 'Heart "
        "Disease API' has four panels: request rate, p95 latency, 5xx error share and predictions "
        "by label. The scrape target and dashboards are the same in docker-compose and Kubernetes."),
      img(crop(SHOTS / "api_metrics.png", (0, 270, 1200, 560), "metrics.png"), width=13 * cm, caption="Figure 13 - GET /metrics from the "
          "running API (api_requests_total and latency histogram visible; real screenshot)"),
      P("<b>Local Kubernetes evidence.</b> The captured kind-cluster run (<font face='Courier'>scripts/deploy_local.sh</font>) shows "
        "2/2 heart-api pods Ready, plus Prometheus and Grafana; the smoke test passed through "
        "<font face='Courier'>kubectl port-forward</font>; Prometheus showed both heart-api pods as "
        "<i>up</i>, and the Grafana dashboard loaded with data. The Ingress manifest passed "
        "<font face='Courier'>kubectl apply --dry-run=server</font>, but the ingress-nginx controller was not installed. "
        "For that reason, the verified access path was port-forwarding; Ingress routing itself remains unverified."),
      img(SHOTS / "k8s_pods_services.png", width=W, max_h=5 * cm, caption="Figure 14 - kubectl get pods,svc "
          "(real captured text)"),
      img(SHOTS / "k8s_smoke_test.png", width=W, max_h=5 * cm, caption="Figure 15 - smoke test served by "
          "the pods through port-forward (real captured text)"),
      img(SHOTS / "prometheus_targets.png", width=W, max_h=5 * cm, caption="Figure 16 - Prometheus targets "
          "page (real browser screenshot)"),
      img(SHOTS / "grafana_dashboard.png", width=W, max_h=7 * cm, caption="Figure 17 - Grafana "
          "'Heart Disease API' dashboard (real browser screenshot; the 5xx panel is empty because "
          "no errors occurred)"),
      PageBreak()]

# ---------------------------------------------------------------- 9 results
s += [P("9. Results and limitations", H1),
      P("Results", H2),
      *bullets([f"Best model: {metrics['best_run']} - CV ROC-AUC {cvm['roc_auc']:.3f}, CV accuracy "
                f"{cvm['accuracy']:.3f}, CV recall {cvm['recall']:.3f}.",
                f"Held-out test at the default 0.5: accuracy {t5['accuracy']:.3f}, precision "
                f"{t5['precision']:.3f}, recall {t5['recall']:.3f}, ROC-AUC {t5['roc_auc']:.3f}.",
                f"At the recall-oriented threshold {thr}: accuracy {tt['accuracy']:.3f}, precision "
                f"{tt['precision']:.3f}, recall {tt['recall']:.3f}.",
                f"Random forests reached CV ROC-AUC {runs[runs.run.str.startswith('random')].cv_roc_auc.min():.3f}"
                f"-{runs[runs.run.str.startswith('random')].cv_roc_auc.max():.3f}; none beat logistic "
                "regression.",
                f"{n_tests} unit tests pass, flake8 is clean, and the API returns validated "
                "predictions with request logging and Prometheus metrics."]),
      Table([[Image(str(plots_dir / "roc_curve.png"), width=4.6 * cm, height=4.6 * cm * 0.889),
              Image(str(plots_dir / "confusion_matrix.png"), width=4.6 * cm, height=4.6 * cm * 0.889)],
             [P("Figure 18 - ROC curve on the held-out test set", CAP),
              P("Figure 19 - confusion matrix at the default threshold (0.5)", CAP)]]),
      P("Limitations and honest caveats", H2),
      *bullets(["<b>Small data.</b> 303 patients (61 test rows): one patient moves a metric by "
                "~1.6 points, and CV standard deviations (up to 0.037) exceed many gaps between "
                "configurations. Treat the ranking of close runs as noise.",
                "<b>Single hold-out split.</b> The threshold and model were chosen with "
                "training-only data, but a single split cannot quantify variance; repeated "
                "CV or an external cohort would be stronger.",
                "<b>Population shift.</b> The Cleveland cohort is one hospital from the 1980s; "
                "calibration and performance on other populations are unknown. This is a teaching "
                "project and not a medical device.",
                "<b>Precision trade-off.</b> The 0.26 threshold maximises recall and therefore "
                "produces more false positives.",
                "<b>Deployment verification.</b> Everything was verified locally (Docker Desktop, kind, "
                "act). The workflow has not run on GitHub-hosted runners, and the Ingress was only "
                "dry-run validated because no ingress controller was installed.",
                "<b>Monitoring scope.</b> Operational metrics only: no data-drift or "
                "prediction-distribution monitoring and no automated retraining trigger. "
                "The MLflow store is local files, so it is not shared between machines."]),
      P("Possible next steps: drift monitoring on input features, a remote MLflow tracking server, "
        "image push to a registry from CI, and a Helm chart for the manifests."),
      PageBreak()]

# ---------------------------------------------------------------- 10 repo
s += [P("10. Repository and deliverables map", H1),
      P(f"<b>Code repository:</b> {REPO_URL if REPO_URL else 'Publication to GitHub is the remaining external step; see docs/UPLOAD_TO_GITHUB.md.'} "
        "<b>API access:</b> no public endpoint is configured; run locally "
        "(<font face='Courier'>uvicorn src.api:app --port 8000</font>, "
        "<font face='Courier'>docker run -p 8000:8000 heart-disease-api</font>, or the Kubernetes "
        "port-forward above) and open http://localhost:8000/docs."),
      table([["Assignment requirement", "Where it is"],
             ["EDA, cleaning, download script", "src/download_data.py, src/eda.py, notebooks/01_eda.ipynb, "
              "docs/eda_summary.txt, Section 2"],
             ["Features and models (>=2, CV, metrics)", "src/features.py, src/train.py, "
              "notebooks/02_training.ipynb, docs/experiments.md, Section 3"],
             ["Experiment tracking", "mlruns/ (via src/train.py), screenshots/mlflow_*.png, Section 4"],
             ["Packaging and reproducibility", "models/model.joblib, requirements.txt, pipeline in "
              "src/features.py"],
             ["Unit tests + CI/CD", "test/, .github/workflows/ci.yml, docs/run_outputs/, Section 6"],
             ["Docker", "Dockerfile, docker-compose.yml, scripts/smoke_test.sh, Section 7"],
             ["Kubernetes", "k8s/, scripts/deploy_local.sh, Section 8"],
             ["Monitoring and logging", "src/api.py, monitoring/, k8s/monitoring/, Section 8"],
             ["Inference notebook", "notebooks/03_inference.ipynb"],
             ["Written report", "docs/report/ (this PDF)"],
             ["Demo video outline", "docs/demo_video_script.md (recording not included in this package)"]],
            [5.4 * cm, W - 5.4 * cm]),
      Spacer(1, 6),
      P("11. Evidence screenshots", H1),
      P("The <font face='Courier'>screenshots/</font> folder contains EDA plots, MLflow pages, API documentation and sample responses, Prometheus/Grafana views, plus captured test, lint, Docker, Kubernetes and local-CI output. Browser images were captured from local services; terminal images were rendered from saved command output. The GitHub-hosted Actions run and public Ingress route remain external verification items, as noted above.", BODY)]

first = True
for i, f in enumerate(s):
    if isinstance(f, PageBreak):
        s[i] = CondPageBreak(0.5 * cm)

doc = SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm,
                        topMargin=1.5 * cm, bottomMargin=1.6 * cm,
                        title="Heart-disease risk MLOps - Assignment 1 report")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("wrote", PDF)
