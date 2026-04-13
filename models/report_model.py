"""Report generation and integrity verification for the EduGuide prototype."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from utils.sha256_scratch import sha256_hex


class ReportModel:
    def create_report(self, student_values: dict, evaluation: dict, nonce: str | None = None) -> dict:
        report = {
            "report_id": f"EDU-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6].upper()}",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "selected_student_values": student_values,
            "derived_profile": evaluation["derived_profile"],
            "triggered_rules": evaluation["triggered_rules"],
            "assigned_risk_level": evaluation["risk_level"],
            "recommendations": evaluation["recommendations"],
            "explanation": evaluation["explanation"],
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
        return json.dumps(report, indent=2, ensure_ascii=True)