"""Encryption and decryption model using the custom SHA-256 keystream design."""

from __future__ import annotations

import base64
import json

from models.report_model import ReportModel
from utils.encryption_utils import decrypt_text, encrypt_text, generate_nonce


class CryptoModel:
    def __init__(self, report_model: ReportModel) -> None:
        self.report_model = report_model

    def encrypt_report(self, report: dict, passphrase: str) -> tuple[dict, dict]:
        nonce_bytes = generate_nonce()
        nonce_text = base64.b64encode(nonce_bytes).decode("ascii")

        report_to_store = self.report_model.attach_nonce_and_refresh_hash(report, nonce_text)
        plaintext_json = json.dumps(report_to_store, indent=2, ensure_ascii=True)
        ciphertext = encrypt_text(plaintext_json, passphrase, nonce_bytes)

        wrapper = {
            "app": "EduGuide",
            "report_id": report_to_store["report_id"],
            "timestamp": report_to_store["timestamp"],
            "nonce": nonce_text,
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "stored_integrity_hash": report_to_store["integrity_hash"],
            "encryption_scheme": "XOR keystream derived from custom SHA-256(passphrase + nonce + counter)",
            "educational_notice": "Educational prototype only. This is not production-grade cryptography.",
        }
        return wrapper, report_to_store

    def decrypt_report(self, wrapper: dict, passphrase: str) -> dict:
        try:
            nonce_bytes = base64.b64decode(wrapper["nonce"])
            ciphertext = base64.b64decode(wrapper["ciphertext"])
        except Exception as error:
            raise ValueError("The saved report is corrupted and cannot be decoded.") from error

        plaintext_json = decrypt_text(ciphertext, passphrase, nonce_bytes)

        try:
            report = json.loads(plaintext_json)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Decryption failed. The passphrase may be incorrect or the file may be corrupted."
            ) from error

        verification = self.report_model.verify_report(report, stored_hash=wrapper.get("stored_integrity_hash"))
        return {
            "report": report,
            "verification": verification,
        }