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
        personalized_recommendation_items = self._build_personalized_recommendations(
            categorized_inputs,
            intermediate_facts,
            final_risk,
        )
        final_recommendation = " ".join(personalized_recommendation_items)
        triggered_rules.append(self._format_trigger(recommendation_rule))
        explanation_trace.append(
            f"{recommendation_rule.rule_id} fired: {recommendation_rule.reason} Recommendation selected for {final_risk}."
        )
        explanation_trace.append(
            "Personalized recommendation details were expanded based on derived intermediate facts and categorized student inputs."
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
            "recommendation": final_recommendation,
            "explanation_trace": explanation_trace,
            "explanation_text": explanation_text,
        }

    def _build_profile(self, student_values: dict[str, object]) -> dict[str, object]:
        return {
            "Hours_Studied": self._hours_studied_band(self._as_float(student_values["Hours_Studied"])),
            "Attendance": self._attendance_band(self._as_float(student_values["Attendance"])),
            "Parental_Involvement": str(student_values["Parental_Involvement"]),
            "Access_to_Resources": str(student_values["Access_to_Resources"]),
            "Extracurricular_Activities": str(student_values["Extracurricular_Activities"]),
            "Sleep_Hours": self._sleep_band(self._as_int(student_values["Sleep_Hours"])),
            "Previous_Scores": self._previous_scores_band(self._as_float(student_values["Previous_Scores"])),
            "Motivation_Level": str(student_values["Motivation_Level"]),
            "Internet_Access": str(student_values["Internet_Access"]),
            "Tutoring_Sessions": self._tutoring_band(self._as_int(student_values["Tutoring_Sessions"])),
            "Family_Income": str(student_values["Family_Income"]),
            "Teacher_Quality": str(student_values["Teacher_Quality"]),
            "School_Type": str(student_values["School_Type"]),
            "Peer_Influence": str(student_values["Peer_Influence"]),
            "Physical_Activity": self._physical_activity_band(self._as_int(student_values["Physical_Activity"])),
            "Learning_Disabilities": str(student_values["Learning_Disabilities"]),
            "Parental_Education_Level": str(student_values["Parental_Education_Level"]),
            "Distance_from_Home": str(student_values["Distance_from_Home"]),
            "Exam_Score": self._exam_score_band(self._as_float(student_values["Exam_Score"])),
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
            Rule(
                rule_id="R21",
                stage="intermediate",
                description="IF Academic_Foundation is not yet derived AND at least two of Attendance = Low, Hours_Studied = Low, Previous_Scores = Low THEN Academic_Foundation = Weak",
                reason="Two weak academic signals are enough to derive a weak academic foundation when no earlier rule has already concluded it.",
                conclusion_field="Academic_Foundation",
                conclusion_value="Weak",
                condition=lambda facts: facts.get("Academic_Foundation") is None
                and sum(
                    [
                        facts.get("Attendance") == "Low",
                        facts.get("Hours_Studied") == "Low",
                        facts.get("Previous_Scores") == "Low",
                    ]
                )
                >= 2,
            ),
            Rule(
                rule_id="R22",
                stage="intermediate",
                description="IF Academic_Foundation is not yet derived AND at least two of Attendance, Hours_Studied, and Previous_Scores are moderate or better THEN Academic_Foundation = Average",
                reason="Two moderate-or-better academic indicators support deriving an average academic foundation when none has been set yet.",
                conclusion_field="Academic_Foundation",
                conclusion_value="Average",
                condition=lambda facts: facts.get("Academic_Foundation") is None
                and sum(
                    [
                        facts.get("Attendance") in ("Moderate", "High"),
                        facts.get("Hours_Studied") in ("Moderate", "High"),
                        facts.get("Previous_Scores") in ("Average", "High"),
                    ]
                )
                >= 2,
            ),
            Rule(
                rule_id="R23",
                stage="intermediate",
                description="IF Engagement_Status is not yet derived AND at least two of Motivation_Level = Low, Peer_Influence = Negative, Extracurricular_Activities = No THEN Engagement_Status = Poor",
                reason="Two negative engagement indicators justify deriving poor engagement when no stronger prior rule has already done so.",
                conclusion_field="Engagement_Status",
                conclusion_value="Poor",
                condition=lambda facts: facts.get("Engagement_Status") is None
                and sum(
                    [
                        facts.get("Motivation_Level") == "Low",
                        facts.get("Peer_Influence") == "Negative",
                        facts.get("Extracurricular_Activities") == "No",
                    ]
                )
                >= 2,
            ),
            Rule(
                rule_id="R24",
                stage="intermediate",
                description="IF Engagement_Status is not yet derived AND at least two of Motivation_Level = High, Peer_Influence = Positive, Extracurricular_Activities = Yes THEN Engagement_Status = Strong",
                reason="Two positive engagement indicators justify deriving strong engagement when no earlier rule has already concluded it.",
                conclusion_field="Engagement_Status",
                conclusion_value="Strong",
                condition=lambda facts: facts.get("Engagement_Status") is None
                and sum(
                    [
                        facts.get("Motivation_Level") == "High",
                        facts.get("Peer_Influence") == "Positive",
                        facts.get("Extracurricular_Activities") == "Yes",
                    ]
                )
                >= 2,
            ),
            Rule(
                rule_id="R25",
                stage="intermediate",
                description="IF Home_Support is not yet derived AND Parental_Involvement = Low AND Family_Income = Low THEN Home_Support = Limited",
                reason="Low parental involvement with low family income is sufficient to derive limited home support when not already set.",
                conclusion_field="Home_Support",
                conclusion_value="Limited",
                condition=lambda facts: facts.get("Home_Support") is None
                and facts.get("Parental_Involvement") == "Low"
                and facts.get("Family_Income") == "Low",
            ),
            Rule(
                rule_id="R26",
                stage="intermediate",
                description="IF Access_Status is not yet derived AND Access_to_Resources = Low AND either Internet_Access = No OR Distance_from_Home = Far THEN Access_Status = Barrier",
                reason="Low resources combined with either internet or distance barriers is enough to derive an access barrier when one has not already been concluded.",
                conclusion_field="Access_Status",
                conclusion_value="Barrier",
                condition=lambda facts: facts.get("Access_Status") is None
                and facts.get("Access_to_Resources") == "Low"
                and (
                    facts.get("Internet_Access") == "No"
                    or facts.get("Distance_from_Home") == "Far"
                ),
            ),
            Rule(
                rule_id="R27",
                stage="intermediate",
                description="IF Support_Need is not yet derived AND Learning_Disabilities = Yes AND Tutoring_Sessions is None or Occasional THEN Support_Need = Unmet",
                reason="Learning disabilities with missing or only occasional tutoring indicate unmet support needs unless a prior rule already established support status.",
                conclusion_field="Support_Need",
                conclusion_value="Unmet",
                condition=lambda facts: facts.get("Support_Need") is None
                and facts.get("Learning_Disabilities") == "Yes"
                and facts.get("Tutoring_Sessions") in ("None", "Occasional"),
            ),
            Rule(
                rule_id="R28",
                stage="intermediate",
                description="IF Learning_Environment is not yet derived AND Teacher_Quality = Low AND Access_to_Resources = Low THEN Learning_Environment = Challenging",
                reason="Low teacher quality and low resource access together indicate a challenging learning environment when not already set by a narrower rule.",
                conclusion_field="Learning_Environment",
                conclusion_value="Challenging",
                condition=lambda facts: facts.get("Learning_Environment") is None
                and facts.get("Teacher_Quality") == "Low"
                and facts.get("Access_to_Resources") == "Low",
            ),
            Rule(
                rule_id="R29",
                stage="intermediate",
                description="IF Current_Performance is not yet derived AND Exam_Score = Average THEN Current_Performance = Average",
                reason="An average exam score should explicitly derive average current performance when no stronger current-performance rule has already fired.",
                conclusion_field="Current_Performance",
                conclusion_value="Average",
                condition=lambda facts: facts.get("Current_Performance") is None
                and facts.get("Exam_Score") == "Average",
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
            Rule(
                rule_id="R30",
                stage="risk",
                description="IF Academic_Foundation = Average AND Current_Performance = Average THEN Risk_Level = Moderate Risk",
                reason="Average academic foundation with average current performance should classify explicitly as moderate risk rather than falling through to fallback.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Average"
                and facts.get("Current_Performance") == "Average",
            ),
            Rule(
                rule_id="R31",
                stage="risk",
                description="IF Academic_Foundation = Strong AND Current_Performance = Average THEN Risk_Level = Moderate Risk",
                reason="Strong historical foundation with only average current performance still warrants explicit moderate risk monitoring.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Strong"
                and facts.get("Current_Performance") == "Average",
            ),
            Rule(
                rule_id="R32",
                stage="risk",
                description="IF Academic_Foundation = Weak AND Current_Performance = Average THEN Risk_Level = Moderate Risk",
                reason="A weak foundation remains concerning even when current performance is only average, so the case should classify explicitly as moderate risk.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Weak"
                and facts.get("Current_Performance") == "Average",
            ),
            Rule(
                rule_id="R33",
                stage="risk",
                description="IF Attendance = Low AND Current_Performance = Poor THEN Risk_Level = High Risk",
                reason="Low attendance combined with poor current performance is a strong direct indicator of high risk.",
                conclusion_field="Risk_Level",
                conclusion_value="High Risk",
                condition=lambda facts: facts.get("Attendance") == "Low"
                and facts.get("Current_Performance") == "Poor",
            ),
            Rule(
                rule_id="R34",
                stage="risk",
                description="IF Attendance = Low AND Academic_Foundation = Average THEN Risk_Level = Moderate Risk",
                reason="Low attendance should raise concern even for students with an average academic foundation.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Attendance") == "Low"
                and facts.get("Academic_Foundation") == "Average",
            ),
            Rule(
                rule_id="R35",
                stage="risk",
                description="IF Learning_Disabilities = Yes AND Current_Performance = Poor THEN Risk_Level = High Risk",
                reason="Learning disabilities combined with poor current performance should explicitly classify as high risk.",
                conclusion_field="Risk_Level",
                conclusion_value="High Risk",
                condition=lambda facts: facts.get("Learning_Disabilities") == "Yes"
                and facts.get("Current_Performance") == "Poor",
            ),
            Rule(
                rule_id="R36",
                stage="risk",
                description="IF Learning_Disabilities = Yes AND Current_Performance = Average THEN Risk_Level = Moderate Risk",
                reason="Learning disabilities with average current performance still justify explicit moderate risk monitoring.",
                conclusion_field="Risk_Level",
                conclusion_value="Moderate Risk",
                condition=lambda facts: facts.get("Learning_Disabilities") == "Yes"
                and facts.get("Current_Performance") == "Average",
            ),
            Rule(
                rule_id="R37",
                stage="risk",
                description="IF Academic_Foundation = Strong AND Current_Performance = Strong AND Engagement_Status != Poor THEN Risk_Level = Low Risk",
                reason="Strong foundation and strong current performance should qualify as low risk as long as engagement is not poor.",
                conclusion_field="Risk_Level",
                conclusion_value="Low Risk",
                condition=lambda facts: facts.get("Academic_Foundation") == "Strong"
                and facts.get("Current_Performance") == "Strong"
                and facts.get("Engagement_Status") != "Poor",
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

    def _build_personalized_recommendations(
        self,
        categorized_inputs: dict[str, object],
        intermediate_facts: dict[str, object],
        final_risk: str,
    ) -> list[str]:
        recommendation_items = [
            self.recommendation_rules[final_risk].conclusion_value,
        ]

        if intermediate_facts.get("Academic_Foundation") == "Weak":
            recommendation_items.extend(
                [
                    "Review weak subject fundamentals.",
                    "Follow a structured weekly study plan.",
                    "Provide remediation on prerequisite lessons.",
                ]
            )

        if intermediate_facts.get("Academic_Foundation") == "Average":
            recommendation_items.extend(
                [
                    "Strengthen weak topics through guided review.",
                    "Improve study consistency to prevent performance decline.",
                ]
            )

        if intermediate_facts.get("Engagement_Status") == "Poor":
            recommendation_items.extend(
                [
                    "Reduce distractions and improve focus during class.",
                    "Encourage positive peer support and better study companions.",
                    "Increase active participation in class and academic activities.",
                ]
            )

        if intermediate_facts.get("Home_Support") == "Limited":
            recommendation_items.extend(
                [
                    "Encourage closer parent or guardian monitoring.",
                    "Provide simple home follow-up guidance for study support.",
                    "Refer the student for school-based support when home assistance is limited.",
                ]
            )

        if intermediate_facts.get("Access_Status") == "Barrier":
            recommendation_items.extend(
                [
                    "Provide alternative offline learning resources.",
                    "Improve access to study materials, internet, or school-based resources.",
                    "Consider distance-related accommodations if feasible.",
                ]
            )

        if intermediate_facts.get("Wellbeing_Status") == "At_Risk":
            recommendation_items.extend(
                [
                    "Improve sleep habits and daily routine.",
                    "Encourage regular physical activity and balanced wellbeing practices.",
                    "Monitor whether fatigue is affecting classroom performance.",
                ]
            )

        if intermediate_facts.get("Support_Need") == "Unmet":
            recommendation_items.extend(
                [
                    "Prioritize tutoring or academic intervention immediately.",
                    "Provide specialized support if learning difficulties are present.",
                    "Monitor learning progress more frequently.",
                ]
            )

        if intermediate_facts.get("Learning_Environment") == "Challenging":
            recommendation_items.extend(
                [
                    "Increase teacher check-ins and guided support.",
                    "Provide clearer instructional scaffolding and accessible materials.",
                    "Use classroom interventions to reduce environmental learning barriers.",
                ]
            )

        if intermediate_facts.get("Current_Performance") == "Poor":
            recommendation_items.extend(
                [
                    "Conduct an immediate academic performance review.",
                    "Focus first on the weakest current subject areas.",
                    "Increase short-term monitoring and tutorial support.",
                ]
            )

        if intermediate_facts.get("Current_Performance") == "Average":
            recommendation_items.extend(
                [
                    "Reinforce partially mastered topics.",
                    "Monitor progress closely to avoid movement into higher risk.",
                ]
            )

        if categorized_inputs.get("Attendance") == "Low":
            recommendation_items.extend(
                [
                    "Improve attendance immediately.",
                    "Identify and address the causes of absenteeism early.",
                ]
            )

        if categorized_inputs.get("Learning_Disabilities") == "Yes":
            recommendation_items.extend(
                [
                    "Use differentiated instructional support.",
                    "Consider referral for specialized intervention or support services.",
                    "Coordinate with guidance or learning support services if available.",
                ]
            )

        if (
            categorized_inputs.get("Tutoring_Sessions") == "None"
            and final_risk in {"High Risk", "Moderate Risk"}
        ):
            recommendation_items.append(
                "Enroll the student in tutoring or remediation sessions as soon as possible."
            )

        if (
            categorized_inputs.get("Internet_Access") == "No"
            and categorized_inputs.get("Access_to_Resources") == "Low"
        ):
            recommendation_items.append(
                "Provide printed or offline learning materials whenever possible."
            )

        if final_risk == "High Risk":
            recommendation_items.append(
                "Schedule close follow-up monitoring within a short interval."
            )

        if final_risk == "Low Risk":
            recommendation_items.append(
                "Continue maintaining the habits that currently support good performance."
            )

        return self._deduplicate_preserve_order(recommendation_items)

    @staticmethod
    def _deduplicate_preserve_order(items: list[str]) -> list[str]:
        unique_items: list[str] = []
        seen: set[str] = set()

        for item in items:
            if item not in seen:
                unique_items.append(item)
                seen.add(item)

        return unique_items

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
    def _as_float(value: object) -> float:
        if isinstance(value, bool):
            raise TypeError("Boolean values are not valid numeric inputs.")
        if isinstance(value, (int, float, str)):
            return float(value)
        raise TypeError(f"Expected a numeric value, received {type(value).__name__}.")

    @staticmethod
    def _as_int(value: object) -> int:
        if isinstance(value, bool):
            raise TypeError("Boolean values are not valid integer inputs.")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            return int(value)
        raise TypeError(f"Expected an integer value, received {type(value).__name__}.")

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