from typing import Literal

from pydantic import BaseModel, Field


class PatientFeatures(BaseModel):
    age: int = Field(ge=18, le=100, examples=[57])
    sex: Literal[0, 1] = Field(description="1 = male, 0 = female", examples=[1])
    cp: int = Field(ge=1, le=4, description="chest pain type", examples=[4])
    trestbps: float = Field(ge=70, le=250, description="resting BP, mm Hg", examples=[140])
    chol: float = Field(ge=100, le=700, description="serum cholesterol, mg/dl", examples=[241])
    fbs: Literal[0, 1] = Field(description="fasting blood sugar > 120 mg/dl", examples=[0])
    restecg: int = Field(ge=0, le=2, examples=[0])
    thalach: float = Field(ge=60, le=230, description="max heart rate achieved", examples=[123])
    exang: Literal[0, 1] = Field(description="exercise-induced angina", examples=[1])
    oldpeak: float = Field(ge=0, le=10, description="ST depression", examples=[0.2])
    slope: int = Field(ge=1, le=3, examples=[2])
    ca: int = Field(ge=0, le=4, description="major vessels coloured", examples=[0])
    thal: int = Field(ge=3, le=7, description="3 normal, 6 fixed, 7 reversible", examples=[7])


class Prediction(BaseModel):
    prediction: Literal[0, 1]
    label: str
    confidence: float = Field(ge=0, le=1)
    probability_disease: float = Field(ge=0, le=1)
