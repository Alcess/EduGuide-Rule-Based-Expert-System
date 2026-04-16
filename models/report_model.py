"""Report generation and integrity verification for EduGuide."""

from __future__ import annotations

import json
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
            "",
            "Raw Student Input Values",
        ]
        lines.extend(
            f"- {REPORT_LABELS.get(field, field)}: {value}" for field, value in raw_values.items()
        )

        lines.extend(["", "Categorized / Profile Values"])
        lines.extend(
            f"- {REPORT_LABELS.get(field, field)}: {value}" for field, value in categorized_inputs.items()
        )

        lines.extend(["", "Intermediate Knowledge Groups"])
        for field in INTERMEDIATE_FIELDS:
            value = intermediate_facts.get(field, "Not Derived")
            lines.append(f"- {field}: {value}")

        lines.extend(["", "Triggered Rules"])
        if triggered_rules:
            for rule in triggered_rules:
                lines.append(
                    f"- {rule.get('rule_id', '?')} [{rule.get('stage', 'unknown')}]: "
                    f"{rule.get('description', '')} => {rule.get('conclusion_field', '')} = {rule.get('conclusion_value', '')}"
                )
        else:
            lines.append("- No rule trace stored in this report.")

        lines.extend(
            [
                "",
                f"Final Risk Level: {risk_level}",
                "",
                "Recommendation",
                recommendation or "No recommendation available.",
                "",
                "Explanation Summary",
                explanation_text or "No explanation summary available.",
                "",
                "Explanation Trace",
            ]
        )
        if explanation_trace:
            lines.extend(f"- {entry}" for entry in explanation_trace)
        else:
            lines.append("- No explanation trace stored in this report.")

        lines.extend(
            [
                "",
                "Integrity and Storage",
                f"- Integrity Hash: {report.get('integrity_hash', '')}",
                f"- Nonce: {report.get('nonce', 'Not attached')}",
            ]
        )

        return "\n".join(lines)