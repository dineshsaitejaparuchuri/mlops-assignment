import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak", "hr_reserve"]
CATEGORICAL = ["cp", "restecg", "slope", "thal", "ca"]
BINARY = ["sex", "fbs", "exang"]
RAW_FEATURES = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
                "exang", "oldpeak", "slope", "ca", "thal"]


def add_hr_reserve(df: pd.DataFrame) -> pd.DataFrame:
    # share of the age-predicted maximum heart rate (220 - age) reached during exercise
    out = df.copy()
    out["hr_reserve"] = out["thalach"] / (220 - out["age"]).clip(lower=1)
    return out


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    binary = SimpleImputer(strategy="most_frequent")
    return ColumnTransformer([("num", numeric, NUMERIC),
                              ("cat", categorical, CATEGORICAL),
                              ("bin", binary, BINARY)])


def build_pipeline(model) -> Pipeline:
    return Pipeline([("features", FunctionTransformer(add_hr_reserve)),
                     ("prep", build_preprocessor()),
                     ("model", model)])


def feature_names(pipeline: Pipeline) -> np.ndarray:
    return pipeline.named_steps["prep"].get_feature_names_out()
