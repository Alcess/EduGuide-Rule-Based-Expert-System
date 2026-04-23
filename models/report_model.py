"""Report generation and integrity verification for EduGuide."""

from __future__ import annotations

import json
import re
from typing import Callable
from datetime import datetime
from uuid import uuid4

from utils.sha256_scratch import sha256_hex


INTERMEDIATE_FIELDS = [
    "Academic_Foundation",
    "Engagement_Status",
    "Home_Support",
    "Access_Status",
    "Wellbeing_Status",
    "Support_Need",
    "Learning_Environment",
    "Current_Performance",
]

REPORT_LABELS = {
    "Previous_Scores": "Previous Score Percentage (%)",
    "Exam_Score": "Exam Score Percentage (%)",
    "Academic_Foundation": "Academic Foundation",
    "Engagement_Status": "Engagement Status",
    "Home_Support": "Home Support",
    "Access_Status": "Access Status",
    "Wellbeing_Status": "Wellbeing Status",
    "Support_Need": "Support Need",
    "Learning_Environment": "Learning Environment",
    "Current_Performance": "Current Performance",
}


class ReportModel:
    def create_report(self, student_values: dict, evaluation: dict, nonce: str | None = None) -> dict:
        timestamp = datetime.now().isoformat(timespec="seconds")
        report = {
            "report_id": f"EDU-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6].upper()}",
            "timestamp": timestamp,
            "raw_student_values": student_values,
            "categorized_inputs": evaluation["categorized_inputs"],
            "intermediate_facts": evaluation["intermediate_facts"],
            "triggered_rules": evaluation["triggered_rules"],
            "final_risk_level": evaluation["risk_level"],
            "recommendation": evaluation["recommendation"],
            "explanation_text": evaluation["explanation_text"],
            "explanation_trace": evaluation["explanation_trace"],
            "nonce": nonce,
            "integrity_hash": "",
        }
        report["integrity_hash"] = self.compute_integrity_hash(report)
        return report

    def attach_nonce_and_refresh_hash(self, report: dict, nonce: str) -> dict:
        updated_report = dict(report)
        updated_report["nonce"] = nonce
        updated_report["integrity_hash"] = self.compute_integrity_hash(updated_report)
        return updated_report

    def compute_integrity_hash(self, report: dict) -> str:
        payload = {key: value for key, value in report.items() if key != "integrity_hash"}
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256_hex(canonical_json.encode("utf-8"))

    def verify_report(self, report: dict, stored_hash: str | None = None) -> dict:
        computed_hash = self.compute_integrity_hash(report)
        report_hash = str(report.get("integrity_hash", ""))
        passed = computed_hash == report_hash

        if stored_hash is not None:
            passed = passed and computed_hash == stored_hash

        return {
            "passed": passed,
            "computed_hash": computed_hash,
            "report_hash": report_hash,
            "stored_hash": stored_hash,
        }

    @staticmethod
    def preview_text(report: dict) -> str:
        raw_values = report.get("raw_student_values") or report.get("selected_student_values", {})
        categorized_inputs = report.get("categorized_inputs") or report.get("derived_profile", {})
        intermediate_facts = report.get("intermediate_facts", {})
        triggered_rules = report.get("triggered_rules", [])
        risk_level = report.get("final_risk_level") or report.get("assigned_risk_level", "Unknown")
        recommendation = report.get("recommendation")
        if recommendation is None:
            recommendations = report.get("recommendations", [])
            recommendation = " ".join(str(item) for item in recommendations)

        explanation_text = report.get("explanation_text") or report.get("explanation", "")
        explanation_trace = report.get("explanation_trace", [])

        lines = [
            "REPORT PREVIEW",
            f"Report ID: {report.get('report_id', 'Unknown')}",
            f"Timestamp: {report.get('timestamp', 'Unknown')}",
            f"Risk level: {risk_level}",
            f"Summary: {explanation_text or 'No explanation summary available.'}",
            "",
            "RECOMMENDED ACTIONS",
        ]
        lines.extend(ReportModel._format_sentence_list(recommendation))

        lines.extend(["", "STUDENT INPUTS"])
        lines.extend(
            f"- {REPORT_LABELS.get(field, field.replace('_', ' '))}: {value}" for field, value in raw_values.items()
        )

        lines.extend(["", "CATEGORIZED PROFILE"])
        lines.extend(
            f"- {REPORT_LABELS.get(field, field.replace('_', ' '))}: {value}"
            for field, value in categorized_inputs.items()
        )

        lines.extend(["", "DERIVED FINDINGS"])
        for field in INTERMEDIATE_FIELDS:
            value = intermediate_facts.get(field, "Not Derived")
            lines.append(f"- {REPORT_LABELS.get(field, field.replace('_', ' '))}: {value}")

        lines.extend(["", "RULES THAT FIRED"])
        lines.append(ReportModel.format_rule_table(triggered_rules))

        lines.extend(
            [
                "",
                "EXPLANATION TRACE",
            ]
        )
        if explanation_trace:
            lines.extend(f"- {entry}" for entry in explanation_trace)
        else:
            lines.append("- No explanation trace stored in this report.")

        lines.extend(
            [
                "",
                "INTEGRITY AND STORAGE",
                f"- Integrity Hash: {report.get('integrity_hash', '')}",
                f"- Nonce: {report.get('nonce', 'Not attached')}",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_sentence_list(text: str | None) -> list[str]:
        if not text:
            return ["- No recommendation available."]

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", str(text).strip())
            if sentence.strip()
        ]
        return [f"- {sentence}" for sentence in sentences]

    @staticmethod
    def format_rule_table(
        triggered_rules: list[dict],
        label_resolver: Callable[[str], str] | None = None,
    ) -> str:
        if not triggered_rules:
            return "No rule trace stored in this report."

        def resolve_label(field_name: str) -> str:
            if label_resolver is not None:
                return label_resolver(field_name)
            return REPORT_LABELS.get(field_name, field_name.replace("_", " "))

        rows: list[tuple[str, str, str, str]] = []
        for rule in triggered_rules:
            rule_id = str(rule.get("rule_id", "?"))
            stage = str(rule.get("stage", "unknown")).title()
            conclusion_field = resolve_label(str(rule.get("conclusion_field", "")))
            conclusion_value = str(rule.get("conclusion_value", ""))
            conclusion = f"{conclusion_field} = {conclusion_value}".strip()
            description = ReportModel._truncate(str(rule.get("description", "")), 54)
            rows.append((rule_id, stage, conclusion, description))

        headers = ("ID", "Stage", "Conclusion", "Rule")
        widths = [
            max(len(headers[0]), max(len(row[0]) for row in rows)),
            max(len(headers[1]), max(len(row[1]) for row in rows)),
            max(len(headers[2]), min(32, max(len(row[2]) for row in rows))),
            max(len(headers[3]), min(54, max(len(row[3]) for row in rows))),
        ]

        def format_row(values: tuple[str, str, str, str]) -> str:
            cells = [
                ReportModel._truncate(values[0], widths[0]).ljust(widths[0]),
                ReportModel._truncate(values[1], widths[1]).ljust(widths[1]),
                ReportModel._truncate(values[2], widths[2]).ljust(widths[2]),
                ReportModel._truncate(values[3], widths[3]).ljust(widths[3]),
            ]
            return " | ".join(cells)

        separator = "-+-".join("-" * width for width in widths)
        lines = [format_row(headers), separator]
        lines.extend(format_row(row) for row in rows)
        return "\n".join(lines)

    @staticmethod
    def _truncate(value: str, width: int) -> str:
        if len(value) <= width:
            return value
        if width <= 3:
            return value[:width]
        return value[: width - 3].rstrip() + "..."