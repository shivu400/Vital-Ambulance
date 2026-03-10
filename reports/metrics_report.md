# Smart Ambulance – Alert Quality Metrics Report

Evaluation set: **1800 samples** (separate seed from training)

## Overall Metrics

| Metric | Value |
|--------|-------|
| Precision | 0.568 |
| Recall | 1.000 |
| F1-Score | 0.725 |
| False Alert Rate | 0.309 |
| Alert Latency (s) | 0.0 |
| True Positives | 520 |
| False Positives | 395 |
| False Negatives | 0 |

### Error Acceptability in an Ambulance Context
- **False negatives (missed anomalies)** are the most dangerous failure: a critical event goes undetected, delaying intervention. Target recall >= 0.85.
- **False positives (over-alerting)** cause alarm fatigue but are tolerable if the false alert rate stays below ~15%. We prioritise recall over precision.

## Per-Phase Metrics

| Phase | Precision | Recall | F1 | False Alert Rate |
|-------|-----------|--------|----|-----------------|
| Normal | 0.000 | 0.000 | 0.000 | 0.017 |
| Distress | 0.382 | 1.000 | 0.552 | 1.000 |
| Critical | 0.872 | 1.000 | 0.932 | 1.000 |

## Failure Case Analysis

### Case 1: False Positive from Motion Artifact
**Occurrences:** 14
**Example vitals:** {'hr': 84.31, 'spo2': 88.85, 'motion': 0.88}
**What failed:** Alert fired on a normal patient during a vehicle bump.
**Why:** SpO2 and HR were transiently inflated/deflated by motion artifacts before artifact filtering was applied, pushing the combined score past the threshold.
**Improvement:** Gate alerts on SQI: suppress anomaly flag when hr_sqi or spo2_sqi < 0.5. Additionally apply artifact cleaning before passing data to the detector.

### Case 2: Over-alerting on Normal Phase (Non-motion FP)
**Occurrences:** 1
**Example vitals:** {'hr': 75.22, 'spo2': 100.0, 'sbp': 116.41, 'rr': 15.82}
**What failed:** Detector triggered on a normal patient with no obvious artifact.
**Why:** Gaussian noise in the generator occasionally pushes multiple vitals to their plausible extremes simultaneously, creating a rare but valid-looking anomalous multi-variate pattern.
**Improvement:** Require co-occurrence: only alert if anomaly is flagged in >=2 consecutive windows AND MEWS >= 2 simultaneously (alert hysteresis).
