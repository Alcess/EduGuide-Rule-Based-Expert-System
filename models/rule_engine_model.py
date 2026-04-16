"""Forward-chaining rule base for the EduGuide expert system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


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

RISK_SEVERITY = {"Low Risk": 1, "Moderate Risk": 2, "High Risk": 3}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    stage: str
    description: str
    reason: str
    conclusion_field: str
    conclusion_value: str
    condition: Callable[[dict[str, object]], bool]


class RuleEngineModel:
    def __init__(self) -> None:
        self.intermediate_rules = self._build_intermediate_rules()
        self.risk_rules = self._build_risk_rules()
        self.fallback_rule = self._build_fallback_rule()
        self.recommendation_rules = self._build_recommendation_rules()
        self.rule_count = (
            len(self.intermediate_rules)
            + len(self.risk_rules)
            + 1
            + len(self.recommendation_rules)
        )

    def evaluate(self, student_values: dict[str, object]) -> dict[str, object]:
        categorized_inputs = self._build_profile(student_values)
        known_facts: dict[str, object] = dict(categorized_inputs)
        triggered_rules: list[dict[str, str]] = []
        explanation_trace: list[str] = []

        changed = True
        while changed:
            changed = False
            for rule in self.intermediate_rules:
                if rule.condition(known_facts) and known_facts.get(rule.conclusion_field) != rule.conclusion_value:
                    known_facts[rule.conclusion_field] = rule.conclusion_value
                    triggered_rules.append(self._format_trigger(rule))
                    explanation_trace.append(
                        f"{rule.rule_id} fired: {rule.reason} Derived {rule.conclusion_field.replace('_', ' ')} = {rule.conclusion_value}."
                    )
                    changed = True

        intermediate_facts = {
            field: known_facts.get(field, "Not Derived") for field in INTERMEDIATE_FIELDS
        }

        risk_matches = [rule for rule in self.risk_rules if rule.condition(known_facts)]
        for rule in risk_matches:
            triggered_rules.append(self._format_trigger(rule))
            explanation_trace.append(
                f"{rule.rule_id} fired: {rule.reason} Derived Risk Level = {rule.conclusion_value}."
            )

        if risk_matches:
            final_risk = max(risk_matches, key=lambda item: RISK_SEVERITY[item.conclusion_value]).conclusion_value
            final_risk_rules = [rule.rule_id for rule in risk_matches if rule.conclusion_value == final_risk]
        else:
            triggered_rules.append(self._format_trigger(self.fallback_rule))
            explanation_trace.append(
                "R17 fired: No explicit final risk rule matched, so the system applied the fallback Moderate Risk classification."
            )
            final_risk = self.fallback_rule.conclusion_value
            final_risk_rules = [self.fallback_rule.rule_id]

        recommendation_rule = self.recommendation_rules[final_risk]
        triggered_rules.append(self._format_trigger(recommendation_rule))
        explanation_trace.append(
            f"{recommendation_rule.rule_id} fired: {recommendation_rule.reason} Recommendation selected for {final_risk}."
        )

        explanation_text = (
            f"Forward chaining started from categorized student facts, derived intermediate knowledge groups, "
            f"then selected {final_risk} from risk rules {', '.join(final_risk_rules)}."
        )

        return {
            "categorized_inputs": categorized_inputs,
            "intermediate_facts": intermediate_facts,
            "triggered_rules": triggered_rules,
            "risk_level": final_risk,
            "recommendation": recommendation_rule.conclusion_value,
            "explanation_trace": explanation_trace,
            "explanation_text": explanation_text,
        }

    def _build_profile(self, student_values: dict[str, object]) -> dict[str, object]:
        return {
            "Hours_Studied": self._hours_studied_band(float(student_values["Hours_Studied"])),
            "Attendance": self._attendance_band(float(student_values["Attendance"])),
            "Parental_Involvement": str(student_values["Parental_Involvement"]),
            "Access_to_Resources": str(student_values["Access_to_Resources"]),
            "Extracurricular_Activities": str(student_values["Extracurricular_Activities"]),
            "Sleep_Hours": self._sleep_band(int(student_values["Sleep_Hours"])),
            "Previous_Scores": self._previous_scores_band(float(student_values["Previous_Scores"])),
            "Motivation_Level": str(student_values["Motivation_Level"]),
            "Internet_Access": str(student_values["Internet_Access"]),
            "Tutoring_Sessions": self._tutoring_band(int(student_values["Tutoring_Sessions"])),
            "Family_Income": str(student_values["Family_Income"]),
            "Teacher_Quality": str(student_values["Teacher_Quality"]),
            "School_Type": str(student_values["School_Type"]),
            "Peer_Influence": str(student_values["Peer_Influence"]),
            "Physical_Activity": self._physical_activity_band(int(student_values["Physical_Activity"])),
            "Learning_Disabilities": str(student_values["Learning_Disabilities"]),
            "Parental_Education_Level": str(student_values["Parental_Education_Level"]),
            "Distance_from_Home": str(student_values["Distance_from_Home"]),
            "Exam_Score": self._exam_score_band(float(student_values["Exam_Score"])),
        }

    def _build_intermediate_rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="R1",
                stage="intermediate",
                description="IF Attendance is Low AND Hours_Studied is Low AND Previous_Scores is Low THEN Academic_Foundation = Weak",
                reason="Low attendance, low study time, and low previous scores indicate a weak academic base.",
                conclusion_field="Academic_Foundation",
                conclusion_value="Weak",
                condition=lambda facts: facts.get("Attendance") == "Low"
                and facts.get("Hours_Studied") == "Low"
                and facts.get("Previous_Scores") == "Low",
            ),
            Rule(
                rule_id="R2",
                stage="intermediate",
                description="IF Attendance is Moderate AND Hours_Studied is Moderate AND Previous_Scores is Average THEN Academic_Foundation = Average",
                reason="Balanced attendance, study time, and prior scores suggest an average academic foundation.",
                conclusion_field="Academic_Foundation",
                conclusion_value="Average",
                condition=lambda facts: facts.get("Attendance") == "Moderate"
                and facts.get("Hours_Studied") == "Moderate"
                and facts.get("Previous_Scores") == "Average",
            ),
            Rule(
                rule_id="R3",
                stage="intermediate",
                description="IF Attendance is High AND Hours_Studied is High AND Previous_Scores is High THEN Academic_Foundation = Strong",
                reason="Strong attendance, study time, and previous scores support a strong academic foundation.",
                conclusion_field="Academic_Foundation",
                conclusion_value="Strong",
                condition=lambda facts: facts.get("Attendance") == "High"
                and facts.get("Hours_Studied") == "High"
                and facts.get("Previous_Scores") == "High",
            ),
            Rule(
                rule_id="R4",
                stage="intermediate",
                description="IF Motivation_Level is Low AND Peer_Influence is Negative AND Extracurricular_Activities is No THEN Engagement_Status = Poor",
                reason="Low motivation with negative peer influence and no extracurricular activity shows poor engagement.",
                conclusion_field="Engagement_Status",
                conclusion_value="Poor",
                condition=lambda facts: facts.get("Motivation_Level") == "Low"
                and facts.get("Peer_Influence") == "Negative"
                and facts.get("Extracurricular_Activities") == "No",
            ),
            Rule(
                rule_id="R5",
                stage="intermediate",
                description="IF Motivation_Level is High AND Peer_Influence is Positive AND Extracurricular_Activities is Yes THEN Engagement_Status = Strong",
                reason="High motivation, positive peers, and active extracurricular involvement indicate strong engagement.",
                conclusion_field="Engagement_Status",
                conclusion_value="Strong",
                condition=lambda facts: facts.get("Motivation_Level") == "High"
                and facts.get("Peer_Influence") == "Positive"
                and facts.get("Extracurricular_Activities") == "Yes",
            ),
            Rule(
                rule_id="R6",
                stage="intermediate",
                description="IF Parental_Involvement is Low AND Family_Income is Low AND Parental_Education_Level is High School THEN Home_Support = Limited",
                reason="Low involvement, low income, and limited parental education indicate constrained home support.",
                conclusion_field="Home_Support",
                conclusion_value="Limited",
                condition=lambda facts: facts.get("Parental_Involvement") == "Low"
                and facts.get("Family_Income") == "Low"
                and facts.get("Parental_Education_Level") == "High School",
            ),
            Rule(
                rule_id="R7",
                stage="intermediate",
                description="IF Access_to_Resources is Low AND Internet_Access is No AND Distance_from_Home is Far THEN Access_Status = Barrier",
                reason="Low resources, no internet access, and long travel distance create an access barrier.",
                conclusion_field="Access_Status",
                conclusion_value="Barrier",
                condition=lambda facts: facts.get("Access_to_Resources") == "Low"
                and facts.get("Internet_Access") == "No"
                and facts.get("Distance_from_Home") == "Far",
            ),
            Rule(
                rule_id="R8",
                stage="intermediate",
                description="IF Sleep_Hours is Inadequate AND Physical_Activity is Low THEN Wellbeing_Status = At_Risk",
                reason="Insufficient sleep and low physical activity place student wellbeing at risk.",
                conclusion_field="Wellbeing_Status",
                conclusion_value="At_Risk",
                condition=lambda facts: facts.get("Sleep_Hours") == "Inadequate"
                and facts.get("Physical_Activity") == "Low",
            ),
            Rule(
                rule_id="R9",
                stage="intermediate",
                description="IF Learning_Disabilities is Yes AND Tutoring_Sessions is None THEN Support_Need = Unmet",
                reason="Learning disabilities without tutoring support indicate unmet support needs.",
                conclusion_field="Support_Need",
                conclusion_value="Unmet",
                condition=lambda facts: facts.get("Learning_Disabilities") == "Yes"
                and facts.get("Tutoring_Sessions") == "None",
            ),
            Rule(
                rule_id="R10",
                stage="intermediate",
                description="IF Teacher_Quality is Low AND School_Type is Public AND Access_to_Resources is Low THEN Learning_Environment = Challenging",
                reason="Low teacher quality within a low-resource public-school setting indicates a challenging learning environment.",
                conclusion_field="Learning_Environment",
                conclusion_value="Challenging",
                condition=lambda facts: facts.get("Teacher_Quality") == "Low"
                and facts.get("School_Type") == "Public"
                and facts.get("Access_to_Resources") == "Low",
            ),
            Rule(
                rule_id="R11",
                stage="intermediate",
                description="IF Exam_Score is Low THEN Current_Performance = Poor",
                reason="A low current exam score indicates poor current performance.",
                conclusion_field="Current_Performance",
                conclusion_value="Poor",
                condition=lambda facts: facts.get("Exam_Score") == "Low",
            ),
            Rule(
                rule_id="R12",
                stage="intermediate",
                description="IF Exam_Score is High AND Academic_Foundation = Strong THEN Current_Performance = Strong",
                reason="High exam performance supported by a strong foundation indicates strong current performance.",
                conclusion_field="Current_Performance",
                conclusion_value="Strong",
                condition=lambda facts: facts.get("Exam_Score") == "High"
                and facts.get("Academic_Foundation") == "Strong",
            ),
        ]

    def _build_risk_rules(self) -> list[Rule]:
        return [
            Rule(
                rule_id="R13",
                stage="risk",
                description="IF Academic_Foundation = Weak AND Current_Performance = Poor THEN Risk_Level = High Risk",
                reason="Weak academic foundation with poor current performance requires immediate attention.",
                conclusion_field="Risk_Level",
                conclusion_value="High Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Weak"
                and facts.get("Current_Performance") == "Poor",
            ),
            Rule(
                rule_id="R14",
                stage="risk",
                description="IF Academic_Foundation = Weak AND any major support barrier exists THEN Risk_Level = High Risk",
                reason="A weak foundation combined with support, access, wellbeing, or environment barriers indicates high risk.",
                conclusion_field="Risk_Level",
                conclusion_value="High Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Weak"
                and any(
                    facts.get(field) == expected
                    for field, expected in {
                        "Home_Support": "Limited",
                        "Access_Status": "Barrier",
                        "Support_Need": "Unmet",
                        "Learning_Environment": "Challenging",
                        "Wellbeing_Status": "At_Risk",
                    }.items()
                ),
            ),
            Rule(
                rule_id="R15",
                stage="risk",
                description="IF Academic_Foundation = Average AND any supporting concern exists THEN Risk_Level = Moderate Risk",
                reason="An average foundation with engagement, home, access, wellbeing, or environment concerns suggests moderate risk.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Average"
                and any(
                    facts.get(field) == expected
                    for field, expected in {
                        "Engagement_Status": "Poor",
                        "Home_Support": "Limited",
                        "Access_Status": "Barrier",
                        "Wellbeing_Status": "At_Risk",
                        "Learning_Environment": "Challenging",
                    }.items()
                ),
            ),
            Rule(
                rule_id="R16",
                stage="risk",
                description="IF Academic_Foundation = Strong AND Engagement_Status = Strong AND Current_Performance = Strong THEN Risk_Level = Low Risk",
                reason="Strong foundation, engagement, and current performance indicate low academic risk.",
                conclusion_field="Risk_Level",
                conclusion_value="Low Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Strong"
                and facts.get("Engagement_Status") == "Strong"
                and facts.get("Current_Performance") == "Strong",
            ),
        ]

    @staticmethod
    def _build_fallback_rule() -> Rule:
        return Rule(
            rule_id="R17",
            stage="risk",
            description="IF no explicit final risk rule fires THEN Risk_Level = Moderate Risk",
            reason="No explicit High Risk, Moderate Risk, or Low Risk classification rule matched, so the deterministic fallback applies.",
            conclusion_field="Risk_Level",
            conclusion_value="Moderate Risk",
            condition=lambda _facts: True,
        )

    def _build_recommendation_rules(self) -> dict[str, Rule]:
        return {
            "High Risk": Rule(
                rule_id="R18",
                stage="recommendation",
                description="IF Risk_Level = High Risk THEN provide immediate intervention guidance",
                reason="High-risk cases require urgent academic intervention and structured support.",
                conclusion_field="Recommendation",
                conclusion_value=(
                    "Immediate intervention is needed. The student should meet with an academic adviser, "
                    "attend tutoring sessions, improve attendance immediately, and follow a structured study plan."
                ),
                condition=lambda _facts: True,
            ),
            "Moderate Risk": Rule(
                rule_id="R19",
                stage="recommendation",
                description="IF Risk_Level = Moderate Risk THEN provide improvement and monitoring guidance",
                reason="Moderate-risk cases benefit from targeted improvement and close follow-up.",
                conclusion_field="Recommendation",
                conclusion_value=(
                    "The student should improve study consistency, monitor attendance, strengthen weak subject areas, "
                    "and seek tutoring or consultation if necessary."
                ),
                condition=lambda _facts: True,
            ),
            "Low Risk": Rule(
                rule_id="R20",
                stage="recommendation",
                description="IF Risk_Level = Low Risk THEN provide maintenance guidance",
                reason="Low-risk cases should sustain the habits that are already working.",
                conclusion_field="Recommendation",
                conclusion_value=(
                    "The student should maintain current study habits, continue regular attendance, and sustain positive academic engagement."
                ),
                condition=lambda _facts: True,
            ),
        }

    @staticmethod
    def _format_trigger(rule: Rule) -> dict[str, str]:
        return {
            "rule_id": rule.rule_id,
            "stage": rule.stage,
            "description": rule.description,
            "reason": rule.reason,
            "conclusion_field": rule.conclusion_field,
            "conclusion_value": rule.conclusion_value,
        }

    @staticmethod
    def _hours_studied_band(value: float) -> str:
        if value <= 15:
            return "Low"
        if value >= 25:
            return "High"
        return "Moderate"

    @staticmethod
    def _attendance_band(value: float) -> str:
        if value <= 74:
            return "Low"
        if value >= 90:
            return "High"
        return "Moderate"

    @staticmethod
    def _sleep_band(value: int) -> str:
        if value <= 5:
            return "Inadequate"
        if value >= 9:
            return "Excessive"
        return "Adequate"

    @staticmethod
    def _previous_scores_band(value: float) -> str:
        # Previous scores are interpreted as percentages rather than dataset-specific raw scores.
        if value < 60:
            return "Low"
        if value >= 80:
            return "High"
        return "Average"

    @staticmethod
    def _tutoring_band(value: int) -> str:
        if value <= 0:
            return "None"
        if value >= 3:
            return "Frequent"
        return "Occasional"

    @staticmethod
    def _physical_activity_band(value: int) -> str:
        if value <= 1:
            return "Low"
        if value >= 5:
            return "High"
        return "Moderate"

    @staticmethod
    def _exam_score_band(value: float) -> str:
        # Exam scores are interpreted as percentages rather than dataset-specific raw scores.
        if value < 60:
            return "Low"
        if value >= 80:
            return "High"
        return "Average"