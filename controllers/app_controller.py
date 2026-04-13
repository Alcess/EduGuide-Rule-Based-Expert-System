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
        self.base_dir = Path(__file__).resolve().parent.parent
        self.records_dir = self.base_dir / "records"

        self.dataset_model = DatasetModel(resolve_dataset_path(self.base_dir))
        self.rule_engine_model = RuleEngineModel()
        self.report_model = ReportModel()
        self.crypto_model = CryptoModel(self.report_model)

        self.view = MainView(root)
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

    def load_dataset(self) -> None:
        try:
            self.dataset_metadata = self.dataset_model.load_dataset()
        except Exception as error:
            self.view.show_error(str(error))
            self.view.set_status("Dataset load failed.")
            return

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
        self.current_student_values = self.current_report.get("selected_student_values")
        self.current_evaluation = None

        self.output_sections["report"] = self._format_report_section(self.current_report)
        self.output_sections["crypto"] = self._format_crypto_section(
            f"Decrypted saved report from: {selected_path}",
            wrapper,
        )
        self.output_sections["verification"] = self._format_verification_section(result["verification"])
        self._refresh_output()

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
        ordered_sections = [
            self.output_sections["dataset"],
            self.output_sections["evaluation"],
            self.output_sections["report"],
            self.output_sections["crypto"],
            self.output_sections["verification"],
        ]
        content = "\n\n".join(section for section in ordered_sections if section.strip())
        self.view.set_output(content)

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
            f"Selected prototype columns: {', '.join(metadata['selected_columns'])}\n"
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