"""Dataset loading and input validation for the EduGuide prototype."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class DatasetModel:
    selected_columns = [
        "Attendance",
        "Hours_Studied",
        "Previous_Scores",
        "Tutoring_Sessions",
        "Parental_Involvement",
        "Access_to_Resources",
        "Internet_Access",
        "Exam_Score",
    ]

    numeric_fields = [
        "Attendance",
        "Hours_Studied",
        "Previous_Scores",
        "Tutoring_Sessions",
        "Exam_Score",
    ]

    categorical_fields = [
        "Parental_Involvement",
        "Access_to_Resources",
        "Internet_Access",
    ]

    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.dataframe: pd.DataFrame | None = None
        self.numeric_summary: dict[str, dict[str, float]] = {}
        self.categorical_options: dict[str, list[str]] = {}

    def load_dataset(self) -> dict:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")

        try:
            dataframe = pd.read_csv(self.dataset_path)
        except Exception as error:
            raise ValueError(f"Unable to read dataset: {error}") from error

        missing_columns = [column for column in self.selected_columns if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(
                "The dataset is missing required prototype columns: " + ", ".join(missing_columns)
            )

        self.dataframe = dataframe
        self.numeric_summary = self._build_numeric_summary(dataframe)
        self.categorical_options = self._build_categorical_options(dataframe)

        return {
            "row_count": len(dataframe),
            "all_columns": list(dataframe.columns),
            "selected_columns": self.selected_columns,
            "numeric_summary": self.numeric_summary,
            "categorical_options": self.categorical_options,
            "dataset_path": str(self.dataset_path),
        }

    def validate_student_values(self, raw_values: dict[str, str]) -> dict:
        if self.dataframe is None:
            raise RuntimeError("Load the dataset before evaluating a student.")

        cleaned_values: dict[str, object] = {}

        for field in self.numeric_fields:
            raw_text = str(raw_values.get(field, "")).strip()
            if raw_text == "":
                raise ValueError(f"{field.replace('_', ' ')} is required.")

            try:
                numeric_value = float(raw_text)
            except ValueError as error:
                raise ValueError(f"{field.replace('_', ' ')} must be numeric.") from error

            summary = self.numeric_summary[field]
            if numeric_value < summary["min"] or numeric_value > summary["max"]:
                raise ValueError(
                    f"{field.replace('_', ' ')} must be between {summary['min']} and {summary['max']} based on the dataset."
                )

            if field == "Tutoring_Sessions":
                if numeric_value != int(numeric_value):
                    raise ValueError("Tutoring Sessions must be a whole number.")
                cleaned_values[field] = int(numeric_value)
            else:
                cleaned_values[field] = round(numeric_value, 2)

        for field in self.categorical_fields:
            value = str(raw_values.get(field, "")).strip()
            options = self.categorical_options[field]
            if value not in options:
                raise ValueError(f"{field.replace('_', ' ')} must be one of: {', '.join(options)}")
            cleaned_values[field] = value

        return cleaned_values

    def _build_numeric_summary(self, dataframe: pd.DataFrame) -> dict[str, dict[str, float]]:
        summary: dict[str, dict[str, float]] = {}
        for field in self.numeric_fields:
            series = dataframe[field].dropna().astype(float)
            summary[field] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": round(float(series.mean()), 2),
            }
        return summary

    def _build_categorical_options(self, dataframe: pd.DataFrame) -> dict[str, list[str]]:
        options: dict[str, list[str]] = {}
        for field in self.categorical_fields:
            values = dataframe[field].dropna().astype(str).str.strip()
            options[field] = sorted(value for value in values.unique() if value)
        return options