"""Dataset loading, normalization, and input validation for EduGuide."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


FIELD_SPECS = [
    {"name": "Hours_Studied", "label": "Hours Studied", "input_type": "entry"},
    {"name": "Attendance", "label": "Attendance (%)", "input_type": "entry"},
    {"name": "Parental_Involvement", "label": "Parental Involvement", "input_type": "combo"},
    {"name": "Access_to_Resources", "label": "Access to Resources", "input_type": "combo"},
    {"name": "Extracurricular_Activities", "label": "Extracurricular Activities", "input_type": "combo"},
    {"name": "Sleep_Hours", "label": "Sleep Hours", "input_type": "entry"},
    {"name": "Previous_Scores", "label": "Previous Score Percentage (%)", "input_type": "entry"},
    {"name": "Motivation_Level", "label": "Motivation Level", "input_type": "combo"},
    {"name": "Internet_Access", "label": "Internet Access", "input_type": "combo"},
    {"name": "Tutoring_Sessions", "label": "Tutoring Sessions", "input_type": "entry"},
    {"name": "Family_Income", "label": "Family Income", "input_type": "combo"},
    {"name": "Teacher_Quality", "label": "Teacher Quality", "input_type": "combo"},
    {"name": "School_Type", "label": "School Type", "input_type": "combo"},
    {"name": "Peer_Influence", "label": "Peer Influence", "input_type": "combo"},
    {"name": "Physical_Activity", "label": "Physical Activity", "input_type": "entry"},
    {"name": "Learning_Disabilities", "label": "Learning Disabilities", "input_type": "combo"},
    {"name": "Parental_Education_Level", "label": "Parental Education Level", "input_type": "combo"},
    {"name": "Distance_from_Home", "label": "Distance from Home", "input_type": "combo"},
    {"name": "Exam_Score", "label": "Exam Score Percentage (%)", "input_type": "entry"},
]

PERCENTAGE_SCORE_FIELDS = {"Previous_Scores", "Exam_Score"}

NUMERIC_BANDS = {
    "Hours_Studied": {
        "Low": (1, 15),
        "Moderate": (16, 24),
        "High": (25, None),
    },
    "Attendance": {
        "Low": (60, 74),
        "Moderate": (75, 89),
        "High": (90, None),
    },
    "Sleep_Hours": {
        "Inadequate": (4, 5),
        "Adequate": (6, 8),
        "Excessive": (9, None),
    },
    "Previous_Scores": {
        "Low": (0, 59),
        "Average": (60, 79),
        "High": (80, 100),
    },
    "Tutoring_Sessions": {
        "None": (0, 0),
        "Occasional": (1, 2),
        "Frequent": (3, None),
    },
    "Physical_Activity": {
        "Low": (0, 1),
        "Moderate": (2, 4),
        "High": (5, None),
    },
    "Exam_Score": {
        "Low": (0, 59),
        "Average": (60, 79),
        "High": (80, 100),
    },
}

CATEGORY_ORDER = {
    "Parental_Involvement": ["Low", "Medium", "High"],
    "Access_to_Resources": ["Low", "Medium", "High"],
    "Extracurricular_Activities": ["No", "Yes"],
    "Motivation_Level": ["Low", "Medium", "High"],
    "Internet_Access": ["No", "Yes"],
    "Family_Income": ["Low", "Medium", "High"],
    "Teacher_Quality": ["Low", "Medium", "High"],
    "School_Type": ["Public", "Private"],
    "Peer_Influence": ["Negative", "Neutral", "Positive"],
    "Learning_Disabilities": ["No", "Yes"],
    "Parental_Education_Level": ["High School", "College", "Postgraduate"],
    "Distance_from_Home": ["Near", "Moderate", "Far"],
}

NORMALIZED_ALIASES = {
    "yes": "Yes",
    "no": "No",
    "low": "Low",
    "medium": "Medium",
    "moderate": "Moderate",
    "high": "High",
    "public": "Public",
    "private": "Private",
    "negative": "Negative",
    "neutral": "Neutral",
    "positive": "Positive",
    "college": "College",
    "high school": "High School",
    "postgraduate": "Postgraduate",
    "near": "Near",
    "far": "Far",
}


class DatasetModel:
    selected_columns = [item["name"] for item in FIELD_SPECS]
    numeric_fields = [item["name"] for item in FIELD_SPECS if item["input_type"] == "entry"]
    categorical_fields = [item["name"] for item in FIELD_SPECS if item["input_type"] == "combo"]

    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.dataframe: pd.DataFrame | None = None
        self.numeric_summary: dict[str, dict[str, float]] = {}
        self.categorical_options: dict[str, list[str]] = {}
        self.normalization_notes: list[str] = []

    def get_field_specs(self) -> list[dict[str, str]]:
        return [dict(item) for item in FIELD_SPECS]

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
                "The dataset is missing required application columns: " + ", ".join(missing_columns)
            )

        self.dataframe = self._normalize_dataset_scores(dataframe.copy())
        self.numeric_summary = self._build_numeric_summary(self.dataframe)
        self.categorical_options = self._build_categorical_options(self.dataframe)

        return {
            "row_count": len(self.dataframe),
            "all_columns": list(self.dataframe.columns),
            "selected_columns": self.selected_columns,
            "numeric_summary": self.numeric_summary,
            "categorical_options": self.categorical_options,
            "banding_rules": self.get_banding_rules(),
            "normalization_notes": list(self.normalization_notes),
            "dataset_path": str(self.dataset_path),
        }

    def get_banding_rules(self) -> dict[str, dict[str, str]]:
        banding_rules: dict[str, dict[str, str]] = {}
        for field, bands in NUMERIC_BANDS.items():
            field_rules: dict[str, str] = {}
            for label, (minimum, maximum) in bands.items():
                if maximum is None:
                    field_rules[label] = f"{minimum}+"
                elif minimum == maximum:
                    field_rules[label] = str(minimum)
                else:
                    field_rules[label] = f"{minimum}-{maximum}"
            banding_rules[field] = field_rules
        return banding_rules

    def validate_student_values(self, raw_values: dict[str, str]) -> dict[str, object]:
        if self.dataframe is None:
            raise RuntimeError("Load the dataset before evaluating a student.")

        cleaned_values: dict[str, object] = {}

        for field in self.numeric_fields:
            raw_text = str(raw_values.get(field, "")).strip()
            if raw_text == "":
                raise ValueError(f"{self.label_for(field)} is required.")

            try:
                numeric_value = float(raw_text)
            except ValueError as error:
                raise ValueError(f"{self.label_for(field)} must be numeric.") from error

            if field in PERCENTAGE_SCORE_FIELDS:
                numeric_value = self._normalize_score_input(field, numeric_value)
            else:
                summary = self.numeric_summary[field]
                if numeric_value < summary["min"] or numeric_value > summary["max"]:
                    raise ValueError(
                        f"{self.label_for(field)} must be between {summary['min']} and {summary['max']} based on the dataset."
                    )

            if field in {"Hours_Studied", "Sleep_Hours", "Tutoring_Sessions", "Physical_Activity"}:
                if numeric_value != int(numeric_value):
                    raise ValueError(f"{self.label_for(field)} must be a whole number.")
                cleaned_values[field] = int(numeric_value)
            else:
                cleaned_values[field] = round(numeric_value, 2)

        for field in self.categorical_fields:
            raw_text = str(raw_values.get(field, "")).strip()
            if raw_text == "":
                raise ValueError(f"{self.label_for(field)} is required.")

            cleaned_values[field] = self._normalize_categorical_value(field, raw_text)

        return cleaned_values

    def label_for(self, field_name: str) -> str:
        for item in FIELD_SPECS:
            if item["name"] == field_name:
                return item["label"]
        return field_name.replace("_", " ")

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

    def _normalize_dataset_scores(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        self.normalization_notes = []

        for field in PERCENTAGE_SCORE_FIELDS:
            series = dataframe[field].astype(float)
            below_zero_count = int((series < 0).sum())
            above_hundred_count = int((series > 100).sum())

            if below_zero_count or above_hundred_count:
                dataframe[field] = series.clip(lower=0, upper=100)

            if field == "Exam_Score" and above_hundred_count:
                # Treat exam percentages above 100 as data anomalies and cap them to 100.
                self.normalization_notes.append(
                    f"Exam_Score anomalies above 100 were capped to 100 for {above_hundred_count} dataset row(s)."
                )
            elif above_hundred_count:
                self.normalization_notes.append(
                    f"{field} values above 100 were capped to 100 for {above_hundred_count} dataset row(s)."
                )

            if below_zero_count:
                self.normalization_notes.append(
                    f"{field} values below 0 were raised to 0 for {below_zero_count} dataset row(s)."
                )

        return dataframe

    def _normalize_score_input(self, field: str, numeric_value: float) -> float:
        if numeric_value < 0:
            raise ValueError(f"{self.label_for(field)} must be between 0 and 100.")

        if field == "Exam_Score" and numeric_value > 100:
            # Treat user-entered exam percentages above 100 as anomalies and cap them to 100.
            return 100.0

        if numeric_value > 100:
            raise ValueError(f"{self.label_for(field)} must be between 0 and 100.")

        return numeric_value

    def _build_categorical_options(self, dataframe: pd.DataFrame) -> dict[str, list[str]]:
        options: dict[str, list[str]] = {}
        for field in self.categorical_fields:
            values = dataframe[field].dropna().astype(str).str.strip()
            normalized_values = {
                self._normalize_text(value): self._canonicalize_option(value) for value in values if str(value).strip()
            }
            resolved_values = list(normalized_values.values())
            options[field] = self._sort_categorical_values(field, resolved_values)
        return options

    def _normalize_categorical_value(self, field: str, value: str) -> str:
        normalized_text = self._normalize_text(value)
        options = self.categorical_options.get(field, [])

        for option in options:
            if self._normalize_text(option) == normalized_text:
                return option

        alias = NORMALIZED_ALIASES.get(normalized_text)
        if alias in options:
            return alias

        raise ValueError(f"{self.label_for(field)} must be one of: {', '.join(options)}")

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(str(value).strip().replace("_", " ").split()).lower()

    @staticmethod
    def _canonicalize_option(value: str) -> str:
        normalized_text = DatasetModel._normalize_text(value)
        if normalized_text in NORMALIZED_ALIASES:
            return NORMALIZED_ALIASES[normalized_text]
        return " ".join(part.capitalize() for part in normalized_text.split())

    def _sort_categorical_values(self, field: str, values: list[str]) -> list[str]:
        unique_values = list(dict.fromkeys(values))
        preferred_order = CATEGORY_ORDER.get(field)
        if preferred_order is None:
            return sorted(unique_values)

        order_map = {value: index for index, value in enumerate(preferred_order)}
        return sorted(unique_values, key=lambda value: (order_map.get(value, len(order_map)), value))