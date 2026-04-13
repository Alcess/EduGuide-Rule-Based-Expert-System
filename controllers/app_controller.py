"""Application controller that coordinates the EduGuide MVC flow."""

from __future__ import annotations

from pathlib import Path

from models.crypto_model import CryptoModel
from models.dataset_model import DatasetModel
from models.report_model import ReportModel
from models.rule_engine_model import RuleEngineModel
from utils.file_utils import load_encrypted_wrapper, resolve_dataset_path, save_encrypted_wrapper
from views.main_view import MainView


class AppController:
    def __init__(self, root) -> None:
        # Keep base paths centralized so record and dataset handling stay relative to the project root.
        self.base_dir = Path(__file__).resolve().parent.parent
        self.records_dir = self.base_dir / "records"

        self.dataset_model = DatasetModel(resolve_dataset_path(self.base_dir))
        self.rule_engine_model = RuleEngineModel()
        self.report_model = ReportModel()
        self.crypto_model = CryptoModel(self.report_model)

        self.system_info = self._build_system_info()
        self.view = MainView(root, self.system_info)
        self.view.bind_actions(self)

        self.dataset_metadata: dict | None = None
        self.current_student_values: dict | None = None
        self.current_evaluation: dict | None = None
        self.current_report: dict | None = None
        self.current_wrapper: dict | None = None
        self.output_sections = {
            "dataset": "",
            "evaluation": "",
            "report": "",
            "crypto": "",
            "verification": "",
        }
        self.view.set_status("Home screen ready. Review the overview or select Start Evaluation to continue.")

    def show_landing_page(self) -> None:
        self.view.show_landing_page()
        self.view.set_status("Home screen ready. Review the overview or select Start Evaluation to continue.")

    def show_evaluation_page(self) -> None:
        self.view.show_evaluation_page()
        if self.dataset_metadata is None:
            # The evaluation screen depends on dataset-backed ranges and category options.
            self.load_dataset()
            if self.dataset_metadata is None:
                return
        elif not self.output_sections["dataset"]:
            self.output_sections["dataset"] = self._format_dataset_section(self.dataset_metadata)
            self._refresh_output()

        self.view.set_status("Evaluation workspace ready.")

    def show_help(self) -> None:
        self.view.show_text_dialog("EduGuide System Information / Help", self._build_help_text())

    def load_dataset(self) -> None:
        try:
            self.dataset_metadata = self.dataset_model.load_dataset()
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Dataset load failed.")
            return

    # Refresh the selectable categorical values every time the dataset is loaded.
        self.view.set_categorical_options(self.dataset_metadata["categorical_options"])
        self.output_sections["dataset"] = self._format_dataset_section(self.dataset_metadata)
        self.output_sections["evaluation"] = ""
        self.output_sections["report"] = ""
        self.output_sections["crypto"] = ""
        self.output_sections["verification"] = ""
        self._refresh_output()
        self.view.set_status("Dataset loaded successfully.")

    def evaluate_student(self) -> None:
        if self.dataset_metadata is None:
            self.view.show_error("Load the dataset before evaluating a student.")
            return

        try:
            # Validation normalizes raw GUI input into the types expected by the rule engine.
            student_values = self.dataset_model.validate_student_values(self.view.get_student_inputs())
            evaluation = self.rule_engine_model.evaluate(student_values)
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Evaluation failed.")
            return

        self.current_student_values = student_values
        self.current_evaluation = evaluation
        # A fresh evaluation invalidates any previously generated report or wrapper.
        self.current_report = None
        self.current_wrapper = None

        self.output_sections["evaluation"] = self._format_evaluation_section(student_values, evaluation)
        self.output_sections["report"] = ""
        self.output_sections["crypto"] = ""
        self.output_sections["verification"] = ""
        self._refresh_output()
        self.view.set_status(f"Student evaluated: {evaluation['risk_level']}")

    def generate_report(self) -> None:
        if self.current_student_values is None or self.current_evaluation is None:
            self.view.show_error("Evaluate a student before generating a report.")
            return

        self.current_report = self.report_model.create_report(self.current_student_values, self.current_evaluation)
        self.current_wrapper = None

        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["crypto"] = ""
        self.output_sections["verification"] = ""
        self._refresh_output()
        self.view.set_status("Report generated and ready for preview or saving.")

    def save_encrypted_report(self) -> None:
        if self.current_report is None:
            self.view.show_error("Generate a report before saving it.")
            return

        passphrase = self.view.ask_passphrase("Enter a passphrase to encrypt this report:")
        if not passphrase:
            self.view.show_error("A passphrase is required to save an encrypted report.")
            return

        try:
            # Encryption returns both the storage wrapper and the report copy with its nonce-bound hash.
            wrapper, saved_report = self.crypto_model.encrypt_report(self.current_report, passphrase)
            saved_path = save_encrypted_wrapper(self.records_dir, wrapper)
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Encrypted report save failed.")
            return

        self.current_report = saved_report
        self.current_wrapper = wrapper
        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["crypto"] = self._format_crypto_section(
            f"Encrypted report saved to: {saved_path}",
            wrapper,
        )
        self.output_sections["verification"] = self._format_verification_section(
            self.report_model.verify_report(self.current_report, stored_hash=wrapper["stored_integrity_hash"])
        )
        self._refresh_output()
        self.view.set_status("Encrypted report saved successfully.")
        self.view.show_info(f"Encrypted report saved to:\n{saved_path}")

    def open_encrypted_report(self) -> None:
        selected_path = self.view.ask_open_report_path(self.records_dir)
        if not selected_path:
            return

        passphrase = self.view.ask_passphrase("Enter the passphrase used to encrypt this report:")
        if not passphrase:
            self.view.show_error("A passphrase is required to open an encrypted report.")
            return

        try:
            wrapper = load_encrypted_wrapper(Path(selected_path))
            result = self.crypto_model.decrypt_report(wrapper, passphrase)
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Open report failed.")
            return

        self.current_wrapper = wrapper
        self.current_report = result["report"]
        # Recovering the original form values makes the reopened report consistent with the evaluation workspace.
        self.current_student_values = self.current_report.get("selected_student_values")
        self.current_evaluation = None

        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["crypto"] = self._format_crypto_section(
            f"Decrypted saved report from: {selected_path}",
            wrapper,
        )
        self.output_sections["verification"] = self._format_verification_section(result["verification"])
        self._refresh_output()
        self.view.show_evaluation_page()

        if result["verification"]["passed"]:
            self.view.set_status("Encrypted report opened and integrity verified.")
        else:
            self.view.set_status("Encrypted report opened, but integrity verification failed.")

    def verify_current_report(self) -> None:
        if self.current_report is None:
            self.view.show_error("Generate or open a report before verifying integrity.")
            return

        stored_hash = None
        if self.current_wrapper is not None:
            stored_hash = self.current_wrapper.get("stored_integrity_hash")

        verification = self.report_model.verify_report(self.current_report, stored_hash=stored_hash)
        self.output_sections["verification"] = self._format_verification_section(verification)
        self._refresh_output()
        self.view.set_status("Integrity verification completed.")

    def _refresh_output(self) -> None:
        # Preserve a stable top-to-bottom section order even when some sections are empty.
        ordered_sections = [
            self.output_sections["dataset"],
            self.output_sections["evaluation"],
            self.output_sections["report"],
            self.output_sections["crypto"],
            self.output_sections["verification"],
        ]
        content = "\n\n".join(section for section in ordered_sections if section.strip())
        self.view.set_output(content)

    def _build_system_info(self) -> dict:
        return {
            "title": "EduGuide: Rule-Based Academic Advising Expert System",
            "subtitle": (
                "A student advising system with academic risk classification, recommendation generation, "
                "report handling, and SHA-256-based report security."
            ),
            "overview": (
                "EduGuide evaluates selected academic performance factors through explicit IF-THEN rules instead of a "
                "machine-learning model. The application reviews student inputs, derives performance bands, classifies "
                "the case as Low Risk, Moderate Risk, or High Risk, and produces recommendations plus a structured report "
                "that can be saved, reopened, and checked for integrity."
            ),
            "variables_intro": (
                "The current system uses eight dataset-backed variables selected from StudentPerformanceFactors.csv. "
                "These are the same fields used for validation, rule evaluation, and reporting in the live system."
            ),
            "variables": [
                {
                    "name": "Attendance",
                    "description": "Student attendance percentage used to determine whether class participation is low, medium, or high.",
                },
                {
                    "name": "Hours Studied",
                    "description": "Study effort indicator used to derive the study band applied by the rule base.",
                },
                {
                    "name": "Previous Scores",
                    "description": "Historical academic performance used to detect whether past achievement suggests ongoing risk.",
                },
                {
                    "name": "Exam Score",
                    "description": "Current assessment performance used directly in several risk-classification rules.",
                },
                {
                    "name": "Tutoring Sessions",
                    "description": "Support-session count interpreted as none, limited, or active tutoring support.",
                },
                {
                    "name": "Parental Involvement",
                    "description": "Categorical indicator of home support considered in explainable advising rules.",
                },
                {
                    "name": "Access to Resources",
                    "description": "Learning-resource availability used to judge whether the student has adequate academic support inputs.",
                },
                {
                    "name": "Internet Access",
                    "description": "Connectivity status used to capture access limitations that can increase academic risk.",
                },
            ],
            "modules": [
                {
                    "name": "User Input Module",
                    "description": "Collects the selected student performance values and opens existing protected reports for review.",
                },
                {
                    "name": "Preprocessing Module",
                    "description": "Validates numeric ranges against the dataset and enforces allowed categorical values before inference begins.",
                },
                {
                    "name": "Rule Base and Inference Module",
                    "description": "Applies the hand-authored IF-THEN rules to the derived student profile and records every triggered rule.",
                },
                {
                    "name": "Risk Classification Module",
                    "description": "Assigns Low Risk, Moderate Risk, or High Risk based on the highest-severity triggered rule or the fallback policy.",
                },
                {
                    "name": "Recommendation Module",
                    "description": "Generates advising actions that match the final risk level and the rule explanation.",
                },
                {
                    "name": "Report Generation Module",
                    "description": "Builds a structured report containing the student values, derived profile, triggered rules, explanation, and recommendations.",
                },
                {
                    "name": "SHA-256 Hash Generation Module",
                    "description": "Computes a report integrity hash using the project’s from-scratch SHA-256 implementation.",
                },
                {
                    "name": "Report Encryption / Decryption and Integrity Verification",
                    "description": "Protects saved reports with the reversible keystream workflow, then reopens records and checks stored integrity hashes.",
                },
            ],
            "rule_based_text": (
                f"EduGuide uses human-readable IF-THEN rules, which keeps the advising logic transparent and easy to review in an academic setting. "
                f"The current system uses {len(self.rule_engine_model.rules)} explicit rules, staying within the intended ten-rule scope while keeping the output explainable, reviewable, and easy to interpret."
            ),
            "security_text": (
                "The project includes a SHA-256 implementation written from scratch in pure Python. That hash is used for report integrity checking and also participates in the protected report workflow by deriving keystream blocks for the reversible encryption layer. SHA-256 itself is still a one-way hash, so it does not perform reversible decryption on its own."
            ),
            "workflow_intro": (
                "Use the landing page as the entry point for system overview and navigation, then move into the evaluation workspace when you are ready to enter data or inspect a saved report."
            ),
            "workflow_steps": [
                "Select Start Evaluation to open the advising workspace inside the same window.",
                "Review the dataset summary and enter the required student variables.",
                "Evaluate the student to obtain the risk class, triggered rules, and recommendations.",
                "Generate a report, then optionally save an encrypted copy or reopen an existing protected record.",
                "Use Back to Landing Page whenever you want to return to the presentation-focused home screen.",
            ],
        }

    def _build_help_text(self) -> str:
        variable_lines = [
            f"- {item['name']}: {item['description']}" for item in self.system_info["variables"]
        ]
        module_lines = [
            f"- {item['name']}: {item['description']}" for item in self.system_info["modules"]
        ]
        workflow_lines = [
            f"{index}. {step}" for index, step in enumerate(self.system_info["workflow_steps"], start=1)
        ]

        return (
            f"{self.system_info['title']}\n\n"
            "Overview\n"
            f"{self.system_info['overview']}\n\n"
            "Variables Used\n"
            + "\n".join(variable_lines)
            + "\n\nMain Modules / Functions\n"
            + "\n".join(module_lines)
            + "\n\nRule-Based Expert System\n"
            + self.system_info["rule_based_text"]
            + "\n\nSecurity and Report Protection\n"
            + self.system_info["security_text"]
            + "\n\nHow to Proceed\n"
            + "\n".join(workflow_lines)
        )

    def _format_dataset_section(self, metadata: dict) -> str:
        numeric_lines = []
        for field, summary in metadata["numeric_summary"].items():
            numeric_lines.append(
                f"- {field}: min={summary['min']}, max={summary['max']}, mean={summary['mean']}"
            )

        categorical_lines = []
        for field, values in metadata["categorical_options"].items():
            categorical_lines.append(f"- {field}: {', '.join(values)}")

        return (
            "DATASET SUMMARY\n"
            f"Path: {metadata['dataset_path']}\n"
            f"Rows loaded: {metadata['row_count']}\n"
            f"Selected dataset columns: {', '.join(metadata['selected_columns'])}\n"
            "Numeric field ranges:\n"
            + "\n".join(numeric_lines)
            + "\nCategorical options:\n"
            + "\n".join(categorical_lines)
        )

    def _format_evaluation_section(self, student_values: dict, evaluation: dict) -> str:
        input_lines = [f"- {field}: {value}" for field, value in student_values.items()]
        profile_lines = [f"- {field}: {value}" for field, value in evaluation["derived_profile"].items()]

        if evaluation["triggered_rules"]:
            triggered_lines = [
                f"- {rule['rule_id']} [{rule['risk_level']}]: {rule['description']} | {rule['reason']}"
                for rule in evaluation["triggered_rules"]
            ]
        else:
            triggered_lines = ["- No explicit rule matched. Fallback review policy applied."]

        recommendation_lines = [f"- {item}" for item in evaluation["recommendations"]]

        return (
            "EVALUATION RESULT\n"
            "Selected student values:\n"
            + "\n".join(input_lines)
            + "\nDerived bands and conditions:\n"
            + "\n".join(profile_lines)
            + "\nTriggered rules:\n"
            + "\n".join(triggered_lines)
            + f"\nAssigned risk level: {evaluation['risk_level']}\n"
            + f"Reason: {evaluation['explanation']}\n"
            + "Recommendations:\n"
            + "\n".join(recommendation_lines)
        )

    def _format_report_section(self, report: dict) -> str:
        return "GENERATED REPORT\n" + self.report_model.preview_text(report)

    def _format_crypto_section(self, headline: str, wrapper: dict) -> str:
        return (
            "ENCRYPTION / DECRYPTION STATUS\n"
            f"{headline}\n"
            f"Encryption scheme: {wrapper['encryption_scheme']}\n"
            f"Nonce: {wrapper['nonce']}\n"
            f"Stored integrity hash: {wrapper['stored_integrity_hash']}\n"
            f"Notice: {wrapper['educational_notice']}"
        )

    def _format_verification_section(self, verification: dict) -> str:
        status = "PASSED" if verification["passed"] else "FAILED"
        stored_line = (
            f"Wrapper stored hash: {verification['stored_hash']}\n"
            if verification.get("stored_hash") is not None
            else ""
        )
        return (
            "INTEGRITY VERIFICATION\n"
            f"Status: {status}\n"
            f"Computed hash: {verification['computed_hash']}\n"
            f"Report hash: {verification['report_hash']}\n"
            + stored_line
        )