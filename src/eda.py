from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

DATA = Path("data/heart_cleaned.csv")
OUT = Path("screenshots/eda")
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)
    df = pd.read_csv(DATA)
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.ravel(), NUMERIC):
        sns.histplot(data=df, x=col, hue="target", kde=True, ax=ax, palette="Set1")
    axes.ravel()[-1].axis("off")
    fig.suptitle("Numeric feature distributions by diagnosis (1 = disease)")
    fig.tight_layout()
    fig.savefig(OUT / "histograms.png", dpi=150)
    plt.close(fig)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df.corr(), annot=True, fmt=".2f", cmap="vlag", center=0)
    plt.title("Feature correlation")
    plt.tight_layout()
    plt.savefig(OUT / "correlation_heatmap.png", dpi=150)
    plt.close()

    plt.figure(figsize=(5, 4))
    ax = sns.countplot(data=df, x="target", hue="target", palette="Set1", legend=False)
    ax.bar_label(ax.containers[0])
    plt.title("Class balance")
    plt.tight_layout()
    plt.savefig(OUT / "class_balance.png", dpi=150)
    plt.close()

    cats = ["sex", "cp", "exang", "slope", "ca", "thal"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.ravel(), cats):
        sns.countplot(data=df, x=col, hue="target", ax=ax, palette="Set1")
    fig.suptitle("Categorical features by diagnosis")
    fig.tight_layout()
    fig.savefig(OUT / "categorical_counts.png", dpi=150)
    plt.close(fig)

    with open("docs/eda_summary.txt", "w") as f:
        f.write(f"shape: {df.shape}\n\nmissing values per column:\n{df.isna().sum()}\n\n")
        f.write(f"class balance:\n{df['target'].value_counts()}\n\n")
        f.write(f"describe:\n{df.describe().T.round(2)}\n\n")
        f.write(f"correlation with target:\n"
                f"{df.corr()['target'].drop('target').sort_values().round(3)}\n")
    print("EDA outputs written to", OUT)


if __name__ == "__main__":
    main()
