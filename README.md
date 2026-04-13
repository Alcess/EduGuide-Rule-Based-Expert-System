# EduGuide

EduGuide is a local desktop prototype of a rule-based expert system for student advising. It uses a real uploaded dataset, a Tkinter graphical interface, an MVC structure, a hand-authored rule base, a from-scratch SHA-256 implementation, and demo-only encrypted report storage for academic presentation.

## Project Overview

The prototype demonstrates the following flow:

1. Load the dataset from `data/StudentPerformanceFactors.csv`
2. Detect and display the relevant dataset columns used by the advising system
3. Accept student values through the GUI
4. Evaluate the student using explicit IF-THEN rules
5. Show triggered rules, the assigned risk level, recommendations, and a readable report
6. Compute a SHA-256 integrity hash using a custom implementation written entirely in Python
7. Save the report as encrypted JSON using a demo-only XOR keystream derived from the custom SHA-256
8. Open a saved report later, decrypt it, and verify the stored report integrity

## MVC Structure

- `models/`
  - `dataset_model.py`: loads the CSV with pandas and validates student input
  - `rule_engine_model.py`: contains the explicit rule base and recommendation logic
  - `report_model.py`: creates report objects and computes integrity hashes
  - `crypto_model.py`: encrypts and decrypts reports using the custom SHA-256 keystream design
- `views/`
  - `main_view.py`: Tkinter interface for the prototype workflow
- `controllers/`
  - `app_controller.py`: coordinates user actions, model calls, and GUI updates
- `utils/`
  - `sha256_scratch.py`: complete SHA-256 implementation from scratch
  - `encryption_utils.py`: nonce generation, keystream derivation, and XOR encryption helpers
  - `file_utils.py`: dataset path resolution and encrypted report file handling

## Selected Dataset Fields

The uploaded dataset contains many variables. The prototype intentionally uses a small set of clearly relevant real columns:

- `Attendance`
- `Hours_Studied`
- `Previous_Scores`
- `Tutoring_Sessions`
- `Parental_Involvement`
- `Access_to_Resources`
- `Internet_Access`
- `Exam_Score`

These were selected because they map cleanly to student advising decisions and can support deterministic, human-readable rules.

## Rule-Based Design

EduGuide uses a hand-authored rule base with 9 explicit IF-THEN rules, which stays within the required maximum of 10 rules. The engine evaluates all rules, collects the triggered ones, and assigns the highest severity among them.

### Risk Levels

- Low Risk
- Moderate Risk
- High Risk

### Rule Set

1. IF attendance is low AND study hours is low AND exam score is low THEN risk = High Risk
2. IF attendance is low AND previous scores is low THEN risk = High Risk
3. IF exam score is low AND access to resources is low AND internet access is no THEN risk = High Risk
4. IF exam score is low AND parental involvement is low AND tutoring sessions is none THEN risk = High Risk
5. IF attendance is medium AND exam score is medium THEN risk = Moderate Risk
6. IF previous scores is medium AND study hours is medium THEN risk = Moderate Risk
7. IF exam score is medium AND tutoring sessions is none THEN risk = Moderate Risk
8. IF attendance is high AND study hours is high AND exam score is high THEN risk = Low Risk
9. IF previous scores is high AND attendance is high AND tutoring support is active THEN risk = Low Risk

If no explicit rule matches exactly, the system applies a deterministic fallback policy and assigns `Moderate Risk` for review.

## From-Scratch SHA-256 Implementation

The custom SHA-256 implementation in `utils/sha256_scratch.py` includes all major algorithm stages:

- message preprocessing and padding
- 512-bit block parsing
- 64-word message schedule expansion
- SHA-256 round constants
- compression rounds with the working variables
- final digest generation as raw bytes and hexadecimal text

The implementation does not use `hashlib`, external cryptography packages, or built-in SHA helpers.

## Report Encryption and Decryption

SHA-256 is one-way, so it cannot decrypt data by itself. To satisfy the prototype requirement for reversible encrypted reports, EduGuide uses this demo-only design:

1. The user enters a passphrase when saving a report.
2. A random nonce is generated.
3. The report is serialized as JSON.
4. A keystream is created by repeatedly hashing `passphrase + nonce + counter` with the custom SHA-256.
5. The plaintext bytes are XORed with the keystream bytes to produce ciphertext.
6. The app stores the nonce, ciphertext, integrity hash, and minimal metadata inside a JSON wrapper in `records/`.
7. When opening a report, the app rebuilds the same keystream, decrypts the JSON, and recomputes the integrity hash.

### Important Notice

This encryption approach is only for educational prototype use. It is not production-grade cryptography and should not be used for real security-sensitive systems.

## Report Contents

Each generated report contains at least:

- `report_id`
- `timestamp`
- selected student values
- derived profile bands
- triggered rules
- assigned risk level
- recommendation list
- explanation text
- SHA-256 integrity hash
- nonce used for encryption once the report is saved

## Installation and Run

1. Create or activate a Python 3 environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the desktop prototype:

   ```bash
   python main.py
   ```

## Demo Flow

1. Start the app.
2. Click `Load Dataset`.
3. Enter student values.
4. Click `Evaluate Student`.
5. Review the triggered rules, risk level, and recommendations.
6. Click `Generate Report`.
7. Review the report and SHA-256 integrity hash.
8. Click `Save Encrypted Report` and enter a passphrase.
9. Later, click `Open Encrypted Report`, select the saved file, and enter the passphrase.
10. Review the decrypted report and the integrity verification result.

## Sample Demo Scenario

Use the following realistic values from the dataset ranges:

- Attendance: `68`
- Hours Studied: `10`
- Previous Scores: `60`
- Exam Score: `59`
- Tutoring Sessions: `0`
- Parental Involvement: `Low`
- Access to Resources: `Low`
- Internet Access: `No`

Expected prototype behavior:

- Likely triggered rules: `R1`, `R2`, `R3`, and `R4`
- Assigned risk level: `High Risk`
- Recommendations: immediate adviser consultation, attendance improvement, tutoring, and structured study support

## Notes for Academic Presentation

- This is a rule-based expert system, not a machine learning model.
- The rules are explicit, readable, and deterministic.
- The prototype shows how a custom SHA-256 implementation can support both integrity checking and demo-only reversible encryption.
- The interface is intentionally simple so the workflow is easy to demonstrate live.