# Safety-Critical Thinking – Gray Mobility Smart Ambulance

*Gray Mobility AI/ML Engineer Assignment – Part 5*
*Candidate analysis | Max 2 pages*

---

## 1. Most Dangerous Failure Mode of This System

The single most dangerous failure mode is a **silent false negative during rapid patient deterioration** — specifically, missing a critical event (e.g., sudden haemodynamic collapse or hypoxic crisis) when the patient's vitals transition from borderline to life-threatening within a 30–60 second window.

**Why it is the worst case:**

The ensemble model (Isolation Forest + OneClassSVM) is trained on a static baseline distribution. When a patient deteriorates *gradually*, each individual time-step may look only marginally abnormal, never crossing the anomaly threshold. The model sees "slightly low SpO₂ + slightly elevated HR" individually and scores them benign — but their *co-occurrence and trend* over time is the true signal. Without windowed trend features (rate-of-change, rolling statistics), the detector is essentially blind to gradual-onset events.

The consequence: the paramedic receives no alert, does not intervene early, and the patient arrives at hospital in a far worse state than necessary. In a life-critical system, this is **more dangerous than any false positive**.

**Concrete scenario:** A patient with internal bleeding has SBP slowly falling from 110 → 85 mmHg over 4 minutes. Each second-by-second measurement is individually within the model's "tolerable deviation" range. No alert fires. Shock index (HR/SBP) crosses 1.0 at minute 5, but by then intervention options are severely limited.

---

## 2. How to Reduce False Alerts Without Missing Deterioration

Reducing false alerts (alarm fatigue) while preserving recall requires a **multi-layer alert strategy**, not a single threshold:

### Layer 1 – Signal Quality Gating
Before any anomaly score is computed, check the Signal Quality Index (SQI). If `hr_sqi < 0.5` or `spo2_sqi < 0.5`, suppress the alert and flag the data as "low confidence measurement". Alerts fired on motion-corrupted data are the leading source of false positives.

### Layer 2 – Temporal Hysteresis (Persistence Filter)
Do not alert on a single anomalous time-step. Require the anomaly flag to be `True` for **≥ N consecutive seconds** (e.g., N = 5) before triggering an alert. Single-point spikes are almost always artifacts; genuine deterioration is persistent.

### Layer 3 – Multi-Modal Confirmation
Require that at least **two independent signals** are simultaneously abnormal:
- Anomaly detector flag AND MEWS ≥ 3, OR
- Anomaly detector flag AND Shock Index ≥ 0.9

This exploits the redundancy of vitals. A single rogue SpO₂ reading is not enough; if HR is also responding, the signal is more credible.

### Layer 4 – Trend Amplification for Recall
To avoid missing slow-onset deterioration, add a **falling-trend feature**: if SpO₂ has decreased by ≥ 3% in the last 60 seconds OR SBP has fallen ≥ 15 mmHg, lower the anomaly threshold temporarily (make the detector more sensitive). This way, the system becomes *more alert* as a patient deteriorates, not less.

**The key insight:** false positive reduction and high recall are not fundamentally in conflict — they are in conflict only when a single threshold is used. A layered strategy achieves both.

---

## 3. What Should Never Be Fully Automated in Medical AI Systems

### Never Automate: Treatment Decisions and Irreversible Actions

An AI system for ambulance monitoring should remain firmly in the **decision-support** role. The following categories must always require human confirmation:

**a) Drug Administration or Dosing**
No algorithm should autonomously trigger medication delivery (e.g., adrenaline, morphine). A wrong dose in the wrong context is fatal. The AI can recommend ("consider 0.5mg adrenaline — shock index 1.2, MEWS 6"), but a trained paramedic must confirm and administer.

**b) Destination Routing Decisions with Clinical Consequences**
Choosing between a trauma centre and a community hospital has lifelong implications. The AI can calculate Green Corridor ETA and flag hospital suitability, but the final routing decision belongs to the paramedic or medical control physician.

**c) Termination of Resuscitation Recommendations**
No system should ever output "stop CPR" or similar. Even with high-confidence models, the cost of a wrong decision is irreversible.

**d) Alert Suppression at the Paramedic's Request**
Allowing a human to "snooze" all alerts is dangerous. The system may suppress noisy alerts but must never suppress all alerts, and must log every suppression with a timestamp for accountability and post-incident review.

### The Principle
Medical AI systems in safety-critical settings should follow the **"Human in the Loop for Consequential Decisions"** principle: automation is appropriate for *monitoring*, *anomaly flagging*, and *information surfacing*. It is inappropriate for *decisions that cannot be undone*. The AI raises the alarm; the human decides and acts.

---

*End of Safety-Critical Thinking section.*
