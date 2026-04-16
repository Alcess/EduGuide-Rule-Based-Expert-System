# EduGuide

EduGuide is a local Tkinter desktop application for rule-based academic advising. It preserves the existing MVC layout, the custom SHA-256 implementation written from scratch, and the encrypted save/load workflow, while expanding the original prototype into a fuller forward-chaining expert system built on the StudentPerformanceFactors dataset.

## Project Overview

The upgraded system performs the following end-to-end workflow:

1. Load StudentPerformanceFactors.csv from the project.
2. Validate the required dataset columns used by the expert system.
3. Accept student values through the Tkinter UI.
4. Normalize categorical values and convert numeric inputs into symbolic bands.
5. Apply forward chaining to derive intermediate knowledge groups.
6. Evaluate final risk rules and assign Low Risk, Moderate Risk, or High Risk.
7. Generate recommendation text and an explanation trace.
8. Build a detailed report with integrity hash.
9. Save the report as encrypted JSON or reopen an existing encrypted report.
10. Verify report integrity after decryption or on demand.

## Architecture

EduGuide keeps the original MVC-style structure.

- `models/`
  - `dataset_model.py`: dataset loading, required-column validation, categorical normalization, numeric range checks, and UI field metadata.
  - `rule_engine_model.py`: preprocessing into symbolic categories, forward-chaining inference, 20-rule knowledge base, risk selection, and recommendation generation.
  - `report_model.py`: report construction, integrity hashing with the custom SHA-256 implementation, preview generation, and verification.
  - `crypto_model.py`: report encryption and decryption using the SHA-256-derived XOR keystream workflow.
- `controllers/`
  - `app_controller.py`: orchestration between dataset loading, evaluation, report generation, save/open, and UI updates.
- `views/`
  - `main_view.py`: landing page, evaluation workspace, report preview, and security/integrity panels.
- `utils/`
  - `sha256_scratch.py`: pure-Python SHA-256 implementation from scratch.
  - `encryption_utils.py`: nonce generation, keystream derivation, XOR helpers, and text encryption/decryption.
  - `file_utils.py`: dataset location resolution and encrypted record storage helpers.

## Dataset Fields Used

The rule base uses the following dataset fields. Gender is intentionally excluded from the expert-system logic.

- `Hours_Studied`
- `Attendance`
- `Parental_Involvement`
- `Access_to_Resources`
- `Extracurricular_Activities`
- `Sleep_Hours`
- `Previous_Scores`
- `Motivation_Level`
- `Internet_Access`
- `Tutoring_Sessions`
- `Family_Income`
- `Teacher_Quality`
- `School_Type`
- `Peer_Influence`
- `Physical_Activity`
- `Learning_Disabilities`
- `Parental_Education_Level`
- `Distance_from_Home`
- `Exam_Score`

## Preprocessing and Category Bands

EduGuide validates numeric inputs against the actual dataset ranges and then maps them into symbolic categories used by the rules.

`Previous_Scores` and `Exam_Score` are treated as percentage-based variables with a logical valid range of `0` to `100`, rather than dataset-specific raw-score minimums.

- `Hours_Studied`: Low = 1-15, Moderate = 16-24, High = 25+
- `Attendance`: Low = 60-74, Moderate = 75-89, High = 90+
- `Sleep_Hours`: Inadequate = 4-5, Adequate = 6-8, Excessive = 9+
- `Previous_Scores`: Low = below 60, Average = 60-79, High = 80-100
- `Tutoring_Sessions`: None = 0, Occasional = 1-2, Frequent = 3+
- `Physical_Activity`: Low = 0-1, Moderate = 2-4, High = 5+
- `Exam_Score`: Low = below 60, Average = 60-79, High = 80-100

If the source dataset contains an anomalous `Exam_Score` of `101` or any other value above `100`, EduGuide treats it as a percentage anomaly and caps it to `100` during dataset normalization. User-entered `Exam_Score` values above `100` are also capped to `100` before rule evaluation. Negative score percentages are rejected.

## Forward Chaining Design

The inference process is explicitly forward chaining:

1. Start from validated raw student inputs.
2. Convert them into categorized facts, including percentage-based score categories for `Previous_Scores` and `Exam_Score`.
3. Apply the intermediate rules repeatedly until no new facts are derived.
4. Evaluate the final risk rules against the derived fact set.
5. Resolve conflicts deterministically with severity priority: High Risk > Moderate Risk > Low Risk.
6. If no explicit final risk rule matches, apply Rule 17 fallback and assign Moderate Risk.
7. Fire the recommendation rule associated with the final risk level.
8. Build the explanation trace from the sequence of fired rules.

## Intermediate Knowledge Groups

The expert system derives the following intermediate conclusions before final classification:

- `Academic_Foundation`
- `Engagement_Status`
- `Home_Support`
- `Access_Status`
- `Wellbeing_Status`
- `Support_Need`
- `Learning_Environment`
- `Current_Performance`

## Expanded Rule Base Summary

EduGuide now uses 20 explicit rules:

- Rules `R1-R12`: intermediate analysis rules
- Rules `R13-R16`: final risk classification rules
- Rule `R17`: deterministic fallback risk rule
- Rules `R18-R20`: recommendation rules

### Intermediate Analysis Rules

1. Attendance Low + Hours_Studied Low + Previous_Scores Low percentage => `Academic_Foundation = Weak`
2. Attendance Moderate + Hours_Studied Moderate + Previous_Scores Average percentage => `Academic_Foundation = Average`
3. Attendance High + Hours_Studied High + Previous_Scores High percentage => `Academic_Foundation = Strong`
4. Motivation_Level Low + Peer_Influence Negative + Extracurricular_Activities No => `Engagement_Status = Poor`
5. Motivation_Level High + Peer_Influence Positive + Extracurricular_Activities Yes => `Engagement_Status = Strong`
6. Parental_Involvement Low + Family_Income Low + Parental_Education_Level High School => `Home_Support = Limited`
7. Access_to_Resources Low + Internet_Access No + Distance_from_Home Far => `Access_Status = Barrier`
8. Sleep_Hours Inadequate + Physical_Activity Low => `Wellbeing_Status = At_Risk`
9. Learning_Disabilities Yes + Tutoring_Sessions None => `Support_Need = Unmet`
10. Teacher_Quality Low + School_Type Public + Access_to_Resources Low => `Learning_Environment = Challenging`
11. Exam_Score Low percentage => `Current_Performance = Poor`
12. Exam_Score High percentage + Academic_Foundation Strong => `Current_Performance = Strong`

### Final Risk Rules

13. Academic_Foundation Weak + Current_Performance Poor => `High Risk`
14. Academic_Foundation Weak + any major barrier (`Home_Support`, `Access_Status`, `Support_Need`, `Learning_Environment`, `Wellbeing_Status`) => `High Risk`
15. Academic_Foundation Average + any supporting concern (`Engagement_Status`, `Home_Support`, `Access_Status`, `Wellbeing_Status`, `Learning_Environment`) => `Moderate Risk`
16. Academic_Foundation Strong + Engagement_Status Strong + Current_Performance Strong => `Low Risk`
17. If no explicit final rule matches => `Moderate Risk`

### Recommendation Rules

18. `High Risk` => immediate intervention recommendation
19. `Moderate Risk` => improvement and monitoring recommendation
20. `Low Risk` => maintenance recommendation

## Report Generation Workflow

Each generated report contains:

- `report_id`
- `timestamp`
- raw student input values
- categorized/profile values
- intermediate facts
- triggered rules
- final risk level
- recommendation text
- explanation summary and explanation trace
- SHA-256 integrity hash
- nonce if the report is saved in encrypted form

The report preview labels `Previous_Scores` and `Exam_Score` as percentage-based values so their interpretation is explicit in demos and saved records.

The report preview shown in the UI is formatted for presentation and demo use rather than raw JSON only.

## Custom SHA-256 Implementation

The custom hash implementation in `utils/sha256_scratch.py` remains intact and is still used for:

- report integrity hashing
- the hash primitive inside the reversible report encryption keystream

The project does not replace this with `hashlib`.

## Encrypted Report Workflow

The encryption workflow remains the same educational design used by the original project:

1. Ask the user for a passphrase.
2. Generate a nonce.
3. Serialize the report.
4. Derive a keystream from `passphrase + nonce + counter` using the custom SHA-256 implementation.
5. XOR the plaintext JSON with that keystream.
6. Store the nonce, ciphertext, integrity hash, and metadata in a wrapper JSON file.
7. On load, rebuild the keystream, decrypt the payload, and verify the report hash against the wrapper hash.

This remains instructional and is not production-grade cryptography.

## UI Features

The Tkinter application includes:

- landing page / home screen
- evaluation workspace
- student input form covering the expanded field set
- inference overview panel showing categorized inputs, triggered rules, intermediate facts, final risk, recommendation, and explanation trace
- report preview panel
- security panel showing SHA-256 hash, encryption/decryption status, and integrity verification
- encrypted record open/save workflow
- return to home screen

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

## Sample Usage Flow

1. Start the app and open the evaluation workspace.
2. Click `Load Dataset`.
3. Enter all required student factors.
4. Click `Evaluate Student`.
5. Review categorized values, triggered rules, intermediate conclusions, risk level, recommendation, and explanation trace.
6. Click `Generate Report`.
7. Review the formatted report preview and integrity hash.
8. Click `Save Encrypted Report` to store an encrypted record.
9. Use `Open Encrypted Report` to decrypt a saved record and repopulate the form.
10. Click `Verify Report Integrity` to confirm the current report matches its stored hash.

## Robustness Notes

The upgraded system handles the following without crashing the application:

- missing dataset file
- missing required dataset columns
- missing student form values
- invalid numeric ranges
- score percentages below 0 or above 100
- invalid categorical values
- inconsistent casing or spacing in categorical input
- no explicit final rule match
- corrupt saved record files
- incorrect passphrase or failed decryption
- integrity verification failure

## Key Notes

- EduGuide remains a rule-based expert system.
- The MVC architecture is preserved.
- The custom SHA-256 implementation remains part of both report integrity and encrypted record storage.
- The decision logic is explicit, deterministic, and presentation-ready for demos or coursework.
- `Previous_Scores` and `Exam_Score` now use percentage-based categorization so the rule base is more generalizable across different tests.