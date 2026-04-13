# EduGuide

EduGuide is a local desktop application for rule-based student advising. It combines a Tkinter interface, a structured MVC layout, a hand-authored expert-system rule base, a custom SHA-256 implementation, and encrypted report storage so that academic evaluations can be entered, reviewed, saved, and reopened within a single workflow.

## Project Overview

The application supports the following end-to-end process:

1. Load the dataset from `data/StudentPerformanceFactors.csv`.
2. Detect the fields used by the advising workflow and summarize valid input ranges.
3. Accept student values through the desktop interface.
4. Convert those values into profile bands used by the rule engine.
5. Evaluate the case with explicit IF-THEN rules.
6. Display the triggered rules, assigned risk level, recommendations, and explanation.
7. Generate a structured report and compute a SHA-256 integrity hash using the custom implementation.
8. Save the report as encrypted JSON, then reopen it later and verify that the stored content has not been altered.

## Architecture

EduGuide follows a small MVC-style structure so UI logic, business rules, and data handling stay separated.

- `models/`
  - `dataset_model.py`: loads the CSV dataset with pandas, validates required columns, and checks student input against dataset-backed ranges and categories.
  - `rule_engine_model.py`: defines the expert-system rules, derives the student profile, determines the final risk level, and produces recommendations.
  - `report_model.py`: builds report payloads, calculates integrity hashes, and verifies stored report content.
  - `crypto_model.py`: wraps report encryption and decryption using the custom SHA-256-based keystream workflow.
- `views/`
  - `main_view.py`: renders the Tkinter interface, landing page, evaluation form, and output areas.
- `controllers/`
  - `app_controller.py`: coordinates user actions, data loading, evaluation, report generation, and view updates.
- `utils/`
  - `sha256_scratch.py`: full SHA-256 implementation written from scratch.
  - `encryption_utils.py`: nonce generation, keystream derivation, XOR helpers, and text encryption utilities.
  - `file_utils.py`: dataset-path resolution and encrypted report file handling.

## Selected Dataset Fields

The source dataset contains many columns, but EduGuide focuses on eight fields that map directly to advising decisions:

- `Attendance`
- `Hours_Studied`
- `Previous_Scores`
- `Tutoring_Sessions`
- `Parental_Involvement`
- `Access_to_Resources`
- `Internet_Access`
- `Exam_Score`

These fields were chosen because they support clear validation rules, interpretable student profiles, and explainable decision logic.

## Rule-Based Evaluation

EduGuide uses 9 explicit IF-THEN rules. Each rule produces a risk level when its conditions match the derived student profile. The system evaluates all rules, records every match, and assigns the highest-severity result among the triggered rules.

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

If no rule matches exactly, the system applies a deterministic fallback policy and assigns `Moderate Risk` for review.

## Custom SHA-256 Implementation

The SHA-256 implementation in `utils/sha256_scratch.py` covers the main stages of the algorithm:

- message preprocessing and padding
- 512-bit block parsing
- 64-word message schedule expansion
- round constants and working variables
- compression rounds
- final digest generation as bytes and hexadecimal text

The implementation does not rely on `hashlib`, external cryptography packages, or built-in SHA helper functions.

## Report Protection Workflow

SHA-256 is a one-way hash, so it cannot decrypt data on its own. In EduGuide, it is used as the hashing primitive for a reversible keystream-based report protection workflow:

1. The user enters a passphrase when saving a report.
2. The application generates a random nonce.
3. The report is serialized as JSON.
4. A keystream is derived by repeatedly hashing `passphrase + nonce + counter` with the custom SHA-256 implementation.
5. The plaintext bytes are XORed with the keystream bytes to produce ciphertext.
6. The application stores the nonce, ciphertext, integrity hash, and related metadata inside a JSON wrapper in `records/`.
7. When reopening a report, the application rebuilds the same keystream, decrypts the payload, and verifies the stored integrity hash.

### Important Notice

This encryption workflow is intended for instructional use and is not production-grade cryptography. It should not be used for security-sensitive deployments.

## Report Contents

Each generated report includes at least the following information:

- `report_id`
- `timestamp`
- selected student values
- derived profile bands
- triggered rules
- assigned risk level
- recommendation list
- explanation text
- SHA-256 integrity hash
- nonce used when the report is saved in encrypted form

## Installation and Run

1. Create or activate a Python 3 environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the desktop application:

   ```bash
   python main.py
   ```

## Usage Flow

1. Start the app.
2. Click `Load Dataset`.
3. Enter the student values.
4. Click `Evaluate Student`.
5. Review the triggered rules, risk level, explanation, and recommendations.
6. Click `Generate Report`.
7. Review the report and SHA-256 integrity hash.
8. Click `Save Encrypted Report` and enter a passphrase.
9. Later, click `Open Encrypted Report`, select the saved file, and enter the passphrase.
10. Review the decrypted report and the integrity verification result.

## Example Scenario

Use the following values from the dataset ranges:

- Attendance: `68`
- Hours Studied: `10`
- Previous Scores: `60`
- Exam Score: `59`
- Tutoring Sessions: `0`
- Parental Involvement: `Low`
- Access to Resources: `Low`
- Internet Access: `No`

Expected behavior:

- Likely triggered rules: `R1`, `R2`, `R3`, and `R4`
- Assigned risk level: `High Risk`
- Recommendations: adviser consultation, attendance improvement, tutoring support, and a structured study plan

## Key Notes

- EduGuide is a rule-based expert system, not a machine learning model.
- The decision logic is explicit, readable, and deterministic.
- The custom SHA-256 implementation supports both integrity verification and the keystream generation used for encrypted report storage.
- The interface is intentionally straightforward so the evaluation and reporting steps remain easy to follow.