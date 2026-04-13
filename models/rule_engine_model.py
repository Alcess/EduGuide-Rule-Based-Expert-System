"""Hand-authored rule base for the EduGuide expert system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    rule_id: str
    risk_level: str
    description: str
    reason: str
    condition: callable


class RuleEngineModel:
    def __init__(self) -> None:
        self.rules = self._build_rules()

    def evaluate(self, student_values: dict) -> dict:
        # Convert raw values into normalized bands before checking them against the rule set.
        profile = self._build_profile(student_values)
        triggered_rules = []

        for rule in self.rules:
            if rule.condition(profile):
                triggered_rules.append(
                    {
                        "rule_id": rule.rule_id,
                        "risk_level": rule.risk_level,
                        "description": rule.description,
                        "reason": rule.reason,
                    }
                )

        if triggered_rules:
            # Multiple rules can fire; the final classification always follows the highest-severity match.
            final_risk = self._highest_severity(triggered_rules)
            primary_rules = [rule for rule in triggered_rules if rule["risk_level"] == final_risk]
            explanation = (
                f"Assigned {final_risk} because the highest-severity triggered rules were "
                + ", ".join(rule["rule_id"] for rule in primary_rules)
                + "."
            )
        else:
            final_risk = "Moderate Risk"
            explanation = (
                "No explicit rule matched exactly, so the fallback review policy assigned Moderate Risk "
                "for a balanced manual follow-up."
            )

        return {
            "derived_profile": profile,
            "triggered_rules": triggered_rules,
            "risk_level": final_risk,
            "recommendations": self._recommendations_for(final_risk),
            "explanation": explanation,
        }

    def _build_profile(self, student_values: dict) -> dict:
        # The rule engine operates on simplified bands so the rules remain readable and deterministic.
        attendance = float(student_values["Attendance"])
        hours_studied = float(student_values["Hours_Studied"])
        previous_scores = float(student_values["Previous_Scores"])
        exam_score = float(student_values["Exam_Score"])
        tutoring_sessions = int(student_values["Tutoring_Sessions"])

        return {
            "attendance_band": self._three_band(attendance, low_cutoff=75, high_cutoff=90),
            "study_band": self._three_band(hours_studied, low_cutoff=15, high_cutoff=25),
            "previous_band": self._three_band(previous_scores, low_cutoff=65, high_cutoff=85),
            "exam_band": self._three_band(exam_score, low_cutoff=65, high_cutoff=80),
            "tutoring_band": self._tutoring_band(tutoring_sessions),
            "parental_involvement": str(student_values["Parental_Involvement"]).lower(),
            "access_to_resources": str(student_values["Access_to_Resources"]).lower(),
            "internet_access": str(student_values["Internet_Access"]).lower(),
        }

    def _build_rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="R1",
                risk_level="High Risk",
                description="IF attendance is low AND study hours is low AND exam score is low THEN risk = High Risk",
                reason="The student is struggling across attendance, study effort, and current exam performance.",
                condition=lambda profile: profile["attendance_band"] == "low"
                and profile["study_band"] == "low"
                and profile["exam_band"] == "low",
            ),
            Rule(
                rule_id="R2",
                risk_level="High Risk",
                description="IF attendance is low AND previous scores is low THEN risk = High Risk",
                reason="Weak historical performance combined with poor attendance indicates sustained academic risk.",
                condition=lambda profile: profile["attendance_band"] == "low"
                and profile["previous_band"] == "low",
            ),
            Rule(
                rule_id="R3",
                risk_level="High Risk",
                description="IF exam score is low AND access to resources is low AND internet access is no THEN risk = High Risk",
                reason="Low performance combined with limited learning access suggests the student needs immediate support.",
                condition=lambda profile: profile["exam_band"] == "low"
                and profile["access_to_resources"] == "low"
                and profile["internet_access"] == "no",
            ),
            Rule(
                rule_id="R4",
                risk_level="High Risk",
                description="IF exam score is low AND parental involvement is low AND tutoring sessions is none THEN risk = High Risk",
                reason="The student has low current performance without home support or tutoring intervention.",
                condition=lambda profile: profile["exam_band"] == "low"
                and profile["parental_involvement"] == "low"
                and profile["tutoring_band"] == "none",
            ),
            Rule(
                rule_id="R5",
                risk_level="Moderate Risk",
                description="IF attendance is medium AND exam score is medium THEN risk = Moderate Risk",
                reason="The student is performing in the middle range and should be monitored before decline occurs.",
                condition=lambda profile: profile["attendance_band"] == "medium"
                and profile["exam_band"] == "medium",
            ),
            Rule(
                rule_id="R6",
                risk_level="Moderate Risk",
                description="IF previous scores is medium AND study hours is medium THEN risk = Moderate Risk",
                reason="The student shows average preparation and average historical performance.",
                condition=lambda profile: profile["previous_band"] == "medium"
                and profile["study_band"] == "medium",
            ),
            Rule(
                rule_id="R7",
                risk_level="Moderate Risk",
                description="IF exam score is medium AND tutoring sessions is none THEN risk = Moderate Risk",
                reason="Current results are average and there is no active tutoring support.",
                condition=lambda profile: profile["exam_band"] == "medium"
                and profile["tutoring_band"] == "none",
            ),
            Rule(
                rule_id="R8",
                risk_level="Low Risk",
                description="IF attendance is high AND study hours is high AND exam score is high THEN risk = Low Risk",
                reason="The student is strong across attendance, effort, and current exam performance.",
                condition=lambda profile: profile["attendance_band"] == "high"
                and profile["study_band"] == "high"
                and profile["exam_band"] == "high",
            ),
            Rule(
                rule_id="R9",
                risk_level="Low Risk",
                description="IF previous scores is high AND attendance is high AND tutoring support is active THEN risk = Low Risk",
                reason="The student has strong past performance, strong attendance, and is actively using support resources.",
                condition=lambda profile: profile["previous_band"] == "high"
                and profile["attendance_band"] == "high"
                and profile["tutoring_band"] == "active",
            ),
        ]

    def _highest_severity(self, triggered_rules: list[dict]) -> str:
        severity = {"Low Risk": 1, "Moderate Risk": 2, "High Risk": 3}
        return max(triggered_rules, key=lambda rule: severity[rule["risk_level"]])["risk_level"]

    def _recommendations_for(self, risk_level: str) -> list[str]:
        if risk_level == "Low Risk":
            return [
                "Maintain current study habits and review routines.",
                "Continue regular attendance and participation.",
                "Keep tracking progress with periodic self-checks.",
            ]

        if risk_level == "High Risk":
            return [
                "Consult an academic adviser as soon as possible.",
                "Increase attendance immediately and follow a structured study plan.",
                "Join tutoring sessions and request additional learning resources.",
                "Coordinate with family or school support for closer monitoring.",
            ]

        return [
            "Improve study consistency each week.",
            "Increase attendance and reduce missed class time.",
            "Seek tutoring support if performance does not improve.",
        ]

    @staticmethod
    def _three_band(value: float, low_cutoff: float, high_cutoff: float) -> str:
        # Shared helper for numeric fields that use low / medium / high buckets.
        if value < low_cutoff:
            return "low"
        if value >= high_cutoff:
            return "high"
        return "medium"

    @staticmethod
    def _tutoring_band(value: int) -> str:
        if value <= 0:
            return "none"
        if value == 1:
            return "limited"
        return "active"