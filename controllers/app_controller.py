"""Application controller that coordinates the EduGuide MVC flow."""

from __future__ import annotations

import re
from pathlib import Path

from models.crypto_model import CryptoModel
from models.dataset_model import DatasetModel
from models.report_model import ReportModel
from models.rule_engine_model import RuleEngineModel
from utils.file_utils import load_encrypted_wrapper, resolve_dataset_path, save_encrypted_wrapper
from views.main_view import MainView


class AppController:
    def __init__(self, root) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent
        self.records_dir = self.base_dir / "records"

        self.dataset_model = DatasetModel(resolve_dataset_path(self.base_dir))
        self.rule_engine_model = RuleEngineModel()
        self.report_model = ReportModel()
        self.crypto_model = CryptoModel(self.report_model)

        self.system_info = self._build_system_info()
        self.view = MainView(root, self.system_info, self.dataset_model.get_field_specs())
        self.view.bind_actions(self)

        self.dataset_metadata: dict | None = None
        self.current_student_values: dict | None = None
        self.current_evaluation: dict | None = None
        self.current_report: dict | None = None
        self.current_wrapper: dict | None = None
        self.output_sections = {
            "overview": "",
            "report": "",
            "security": "",
        }
        self.field_labels = {
            spec["name"]: spec["label"] for spec in self.dataset_model.get_field_specs()
        }
        self.view.set_status("Home screen ready. Review the overview or select Start Evaluation to continue.")

    def show_landing_page(self) -> None:
        self.view.show_landing_page()
        self.view.set_status("Home screen ready. Review the overview or select Start Evaluation to continue.")

    def show_evaluation_page(self) -> None:
        self.view.show_evaluation_page()
        if self.dataset_metadata is None:
            self.load_dataset()
            if self.dataset_metadata is None:
                return
        elif not self.output_sections["overview"]:
            self.output_sections["overview"] = self._format_dataset_section(self.dataset_metadata)
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

        self.view.set_categorical_options(self.dataset_metadata["categorical_options"])
        self.output_sections["overview"] = self._format_dataset_section(self.dataset_metadata)
        self.output_sections["report"] = ""
        self.output_sections["security"] = ""
        self._refresh_output()
        self.view.set_status("Dataset loaded successfully.")

    def evaluate_student(self) -> None:
        if self.dataset_metadata is None:
            self.view.show_error("Load the dataset before evaluating a student.")
            return

        try:
            student_values = self.dataset_model.validate_student_values(self.view.get_student_inputs())
            evaluation = self.rule_engine_model.evaluate(student_values)
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Evaluation failed.")
            return

        self.current_student_values = student_values
        self.current_evaluation = evaluation
        self.current_report = None
        self.current_wrapper = None
        self.view.set_student_inputs(student_values)

        self.output_sections["overview"] = self._format_overview_section(student_values, evaluation)
        self.output_sections["report"] = ""
        self.output_sections["security"] = ""
        self._refresh_output()
        self.view.set_status(f"Student evaluated: {evaluation['risk_level']}")
        self.view.show_output_tab("overview")

    def generate_report(self) -> None:
        if self.current_student_values is None or self.current_evaluation is None:
            self.view.show_error("Evaluate a student before generating a report.")
            return

        self.current_report = self.report_model.create_report(self.current_student_values, self.current_evaluation)
        self.current_wrapper = None

        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["security"] = self._format_security_section(
            crypto_message="Report generated locally and ready for encryption.",
            verification=None,
            wrapper=None,
            report=self.current_report,
        )
        self._refresh_output()
        self.view.set_status("Report generated and ready for preview or saving.")
        self.view.show_output_tab("report")

    def save_encrypted_report(self) -> None:
        if self.current_report is None:
            self.view.show_error("Generate a report before saving it.")
            return

        passphrase = self.view.ask_passphrase("Enter a passphrase to encrypt this report:")
        if not passphrase:
            self.view.show_error("A passphrase is required to save an encrypted report.")
            return

        try:
            wrapper, saved_report = self.crypto_model.encrypt_report(self.current_report, passphrase)
            saved_path = save_encrypted_wrapper(self.records_dir, wrapper)
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Encrypted report save failed.")
            return

        self.current_report = saved_report
        self.current_wrapper = wrapper
        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["security"] = self._format_security_section(
            crypto_message=f"Encrypted report saved to: {saved_path}",
            verification=self.report_model.verify_report(
                self.current_report, stored_hash=wrapper["stored_integrity_hash"]
            ),
            wrapper=wrapper,
            report=self.current_report,
        )
        self._refresh_output()
        self.view.set_status("Encrypted report saved successfully.")
        self.view.show_info(f"Encrypted report saved to:\n{saved_path}")
        self.view.show_output_tab("security")

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
        self.current_student_values = self.current_report.get("raw_student_values") or self.current_report.get(
            "selected_student_values"
        )
        self.current_evaluation = None

        if self.current_student_values:
            self.view.set_student_inputs(self.current_student_values)

        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["security"] = self._format_security_section(
            crypto_message=f"Decrypted saved report from: {selected_path}",
            verification=result["verification"],
            wrapper=wrapper,
            report=self.current_report,
        )
        self.output_sections["overview"] = self._format_opened_report_overview(self.current_report)
        self._refresh_output()
        self.view.show_evaluation_page()
        self.view.show_output_tab("report")

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
        existing_security = self.output_sections["security"]
        crypto_message = "Integrity check completed for the current in-memory report."
        if self.current_wrapper is not None:
            crypto_message = existing_security.split("\n", 2)[1] if "\n" in existing_security else crypto_message
        self.output_sections["security"] = self._format_security_section(
            crypto_message=crypto_message,
            verification=verification,
            wrapper=self.current_wrapper,
            report=self.current_report,
        )
        self._refresh_output()
        self.view.set_status("Integrity verification completed.")
        self.view.show_output_tab("security")

    def _refresh_output(self) -> None:
        self.view.set_overview_output(self.output_sections["overview"])
        self.view.set_report_output(self.output_sections["report"])
        self.view.set_security_output(self.output_sections["security"])

    def _build_system_info(self) -> dict:
        return {
            "title": "EduGuide: Rule-Based Academic Advising Expert System",
            "subtitle": (
                "A forward-chaining student advising system with expanded academic risk analysis, "
                "explanation trace, report handling, and SHA-256-based record security."
            ),
            "overview": (
                "EduGuide evaluates student performance through explicit IF-THEN rules instead of machine learning. "
                "The system validates 19 dataset-backed factors, converts them into symbolic categories, derives "
                "intermediate knowledge groups through forward chaining, classifies risk, generates recommendations, "
                "and produces a report that can be encrypted, reopened, and verified for integrity. "
                "Previous_Scores and Exam_Score are handled as percentages, and anomalous exam percentages above 100 are capped to 100."
            ),
            "variables_intro": (
                "The live system uses 19 variables from StudentPerformanceFactors.csv, excluding Gender from the rule base. "
                "The same fields drive validation, category derivation, rule evaluation, and report generation. "
                "Previous Score Percentage and Exam Score Percentage both use a 0 to 100 interpretation."
            ),
            "variables": [
                {
                    "name": item["label"],
                    "description": f"Used as a {'numeric' if item['input_type'] == 'entry' else 'categorical'} fact within preprocessing, forward chaining, and reporting."
                }
                for item in self.dataset_model.get_field_specs()
            ],
            "modules": [
                {
                    "name": "User Input Module",
                    "description": "Collects the expanded student factor set and rehydrates saved records into the evaluation workspace.",
                },
                {
                    "name": "Preprocessing Module",
                    "description": "Validates dataset-backed ranges, normalizes categorical values, and maps numeric values into rule-ready bands.",
                },
                {
                    "name": "Rule Base and Inference Module",
                    "description": "Applies 20 hand-authored IF-THEN rules with forward chaining to derive intermediate and final conclusions.",
                },
                {
                    "name": "Risk Classification Module",
                    "description": "Assigns Low Risk, Moderate Risk, or High Risk using deterministic severity priority and fallback handling.",
                },
                {
                    "name": "Recommendation Module",
                    "description": "Generates recommendation text from the final risk level and includes it in the explanation trace.",
                },
                {
                    "name": "Report Generation Module",
                    "description": "Builds a report with raw values, categorized inputs, intermediate facts, triggered rules, risk level, and explanation trace.",
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
                f"The current system uses {self.rule_engine_model.rule_count} explicit rules across intermediate analysis, risk classification, and recommendation generation, and it evaluates them in a forward-chaining sequence."
            ),
            "security_text": (
                "The project includes a SHA-256 implementation written from scratch in pure Python. That hash is used for report integrity checking and also participates in the protected report workflow by deriving keystream blocks for the reversible encryption layer. SHA-256 itself is still a one-way hash, so it does not perform reversible decryption on its own."
            ),
            "workflow_intro": (
                "Use the landing page as the entry point for system overview and navigation, then move into the evaluation workspace when you are ready to enter data or inspect a saved report."
            ),
            "workflow_steps": [
                "Select Start Evaluation to open the advising workspace inside the same window.",
                "Load the dataset and review the form guidance, dataset ranges, and category bands.",
                "Enter the student factors and evaluate the case to derive categorized inputs, intermediate facts, and the final risk level.",
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
            band_text = ", ".join(
                f"{band}: {range_text}" for band, range_text in metadata["banding_rules"].get(field, {}).items()
            )
            suffix = ""
            if field in {"Previous_Scores", "Exam_Score"}:
                suffix = " | accepted input: 0-100 percentage"
            numeric_lines.append(
                f"- {self._display_label(field)}: min {summary['min']}, max {summary['max']}, mean {summary['mean']}"
                + (f" | bands: {band_text}" if band_text else "")
                + suffix
            )

        categorical_lines = []
        for field, values in metadata["categorical_options"].items():
            categorical_lines.append(f"- {self._display_label(field)}: {', '.join(values)}")

        section = (
            "DATASET OVERVIEW\n"
            f"- Source: {metadata['dataset_path']}\n"
            f"- Rows loaded: {metadata['row_count']}\n"
            f"- Active fields: {len(metadata['selected_columns'])}\n"
            f"- Included columns: {', '.join(self._display_label(field) for field in metadata['selected_columns'])}\n"
            "\nNUMERIC INPUT GUIDANCE\n"
            + "\n".join(numeric_lines)
            + "\n\nCATEGORICAL OPTIONS\n"
            + "\n".join(categorical_lines)
        )

        normalization_notes = metadata.get("normalization_notes", [])
        if normalization_notes:
            section += "\n\nSCORE NORMALIZATION NOTES\n" + "\n".join(
                f"- {note}" for note in normalization_notes
            )

        return section

    def _format_overview_section(self, student_values: dict, evaluation: dict) -> str:
        dataset_section = self._format_dataset_section(self.dataset_metadata) if self.dataset_metadata else ""
        input_lines = self._format_key_value_lines(student_values)
        category_lines = self._format_key_value_lines(evaluation["categorized_inputs"])
        intermediate_lines = self._format_key_value_lines(evaluation["intermediate_facts"])
        triggered_table = self.report_model.format_rule_table(
            evaluation["triggered_rules"],
            label_resolver=self._display_label,
        )
        explanation_lines = [f"- {entry}" for entry in evaluation["explanation_trace"]]
        evaluation_section = (
            "EVALUATION SUMMARY\n"
            f"Risk level: {evaluation['risk_level']}\n"
            f"Summary: {evaluation['explanation_text']}\n"
            "\nRECOMMENDED ACTIONS\n"
            + "\n".join(self._format_sentence_list(evaluation["recommendation"]))
            + "\n\nSTUDENT INPUTS\n"
            + "\n".join(input_lines)
            + "\n\nCATEGORIZED PROFILE\n"
            + "\n".join(category_lines)
            + "\n\nDERIVED FINDINGS\n"
            + "\n".join(intermediate_lines)
            + "\n\nRULES THAT FIRED\n"
            + triggered_table
            + "\n\nEXPLANATION TRACE\n"
            + "\n".join(explanation_lines)
        )

        if dataset_section:
            return evaluation_section + "\n\nDATASET REFERENCE\n" + dataset_section
        return evaluation_section

    def _format_opened_report_overview(self, report: dict) -> str:
        dataset_section = self._format_dataset_section(self.dataset_metadata) if self.dataset_metadata else ""
        recommendation = report.get("recommendation") or " ".join(report.get("recommendations", []))
        report_section = (
            "OPENED REPORT SUMMARY\n"
            f"Report ID: {report.get('report_id', 'Unknown')}\n"
            f"Timestamp: {report.get('timestamp', 'Unknown')}\n"
            f"Risk level: {report.get('final_risk_level') or report.get('assigned_risk_level', 'Unknown')}\n"
            f"Summary: {report.get('explanation_text') or report.get('explanation', '')}\n"
            "\nRECOMMENDED ACTIONS\n"
            + "\n".join(self._format_sentence_list(recommendation))
        )

        if dataset_section:
            return report_section + "\n\nDATASET REFERENCE\n" + dataset_section
        return report_section

    def _format_report_section(self, report: dict) -> str:
        return self.report_model.preview_text(report)

    def _format_security_section(
        self,
        crypto_message: str,
        verification: dict | None,
        wrapper: dict | None,
        report: dict | None,
    ) -> str:
        lines = ["SECURITY AND INTEGRITY", f"Status summary: {crypto_message}"]

        if report is not None:
            lines.extend(
                [
                    "",
                    "REPORT SECURITY DETAILS",
                    f"- SHA-256 integrity hash: {report.get('integrity_hash', '')}",
                    f"- Nonce: {report.get('nonce', 'Not attached')}",
                ]
            )

        if wrapper is not None:
            lines.extend(
                [
                    "",
                    "ENCRYPTED FILE DETAILS",
                    f"- Encryption scheme: {wrapper['encryption_scheme']}",
                    f"- Wrapper nonce: {wrapper['nonce']}",
                    f"- Stored integrity hash: {wrapper['stored_integrity_hash']}",
                    f"- Notice: {wrapper['educational_notice']}",
                ]
            )

        if verification is not None:
            lines.extend(
                [
                    "",
                    "INTEGRITY CHECK",
                    f"- Result: {'PASSED' if verification['passed'] else 'FAILED'}",
                    f"- Computed hash: {verification['computed_hash']}",
                    f"- Report hash: {verification['report_hash']}",
                ]
            )
            if verification.get("stored_hash") is not None:
                lines.append(f"- Wrapper stored hash: {verification['stored_hash']}")

        return "\n".join(lines)

    def _display_label(self, field: str) -> str:
        return self.field_labels.get(field, field.replace("_", " "))

    def _format_key_value_lines(self, values: dict) -> list[str]:
        return [f"- {self._display_label(field)}: {value}" for field, value in values.items()]

    @staticmethod
    def _format_sentence_list(text: str) -> list[str]:
        if not text:
            return ["- No recommendation available."]

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]
        return [f"- {sentence}" for sentence in sentences]