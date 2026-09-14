# README_interfaces.md -- NHAA 14566 Interfaces & Front-end Build Specification

## Overview
This repository contains the standalone front-end implementation for **Person 3 (Interfaces & Dashboards)** of the **NHAA (14566) Real-Time Trauma Triage System**.

It provides complete, zero-dependency visual components and simulation screens built against the exact contract specified in `person3_interfaces.pdf` and aligned with the architectural design in `NHAA_Solution_Revision8_Final_with_Novelty.pdf`.

---

## Shared Contract Schema
All UI components render dynamically from messages conforming to the shared WebSocket schema:

```json
{
  "type": "transcript_update",
  "text": "string",
  "risk_vector": {
    "scores": {
      "acute_distress": 0.0,
      "depression": 0.0,
      "self_harm_risk": 0.0,
      "fear_of_retaliation": 0.0,
      "intimidation": 0.0,
      "dissociation": 0.0,
      "social_isolation": 0.0,
      "chronic_trauma_indicators": 0.0
    },
    "confidence": {
      "acute_distress": 0.0
    },
    "matched_evidence": {
      "acute_distress": ["example phrase"]
    }
  },
  "svi": {
    "value": 0.0,
    "bucket": "low | moderate | high | critical"
  },
  "silence_events": [
    {
      "start_sec": 0.0,
      "duration_sec": 0.0,
      "placement": "mid_sentence"
    }
  ]
}
```

And action updates:
```json
{
  "type": "action_update",
  "action": {
    "action": "police_intervention",
    "state": "awaiting_senior",
    "requires_senior": true
  }
}
```

---

## Built Components & Phases

### 1. Mock Data Generator (`src/services/mockGenerator.ts`)
- Simulates an escalating voice call where SVI climbs from 20 to 88 over updates.
- Emits contract-compliant messages every 2 seconds.

### 2. Caller IVR-sim UI (`src/components/IVRSimUI.tsx`)
- Header: `NHAA 14566 -- incoming`
- Language Selector: Hindi / English / Hinglish
- Receive Call / End Call toggle & Live call timer
- Animated CSS audio waveform equalizer
- Informed consent panel with checkboxes:
  - "I agree to recording"
  - "I agree the AI can look at it"
  - "I agree to help improve the system later (you can say no to this one)"
  - Buttons: "Decline all" and "Accept selected"

### 3. Agent Console (`src/components/AgentConsole.tsx`)
- **Live Transcript Area**: Appends real-time incoming caller speech.
- **8 Labeled Horizontal Progress Bars**:
  1. Acute Distress
  2. Depression
  3. Self-Harm Risk
  4. Fear of Retaliation
  5. Intimidation
  6. Dissociation
  7. Social Isolation
  8. Chronic Trauma
- **Explainability "Why" Panel**: Displays `matched_evidence` next to dimension bars when score > 0.
- **Confidence Indicator per dimension**: Percentage & color badge (Green >80%, Yellow 50-80%, Red <50%).
- **System-wide AI Confidence Indicator**: Interactive slider and banner. Displays `"Low confidence -- this recommendation should not be used for high-stakes action alone"` in red when confidence < 50%.
- **SVI Badge**: Color coded (Green 0-25 / Yellow 26-50 / Orange 51-75 / Red 76-100).
- **Case Timeline**: Log of timestamps and score threshold events.
- **Alert Banners**:
  - Silence Alert: Triggered when `silence_events` mid_sentence duration > 2s (`"Unusual mid-narrative silence detected"`).
  - Silent SOS Alert: Triggered when keypad duress (999#) is activated.
- **Suggested Actions Panel (5 Rows)**:
  1. Counseling
  2. Legal Aid
  3. Police Intervention (Greyed out: "REQUIRES SENIOR APPROVAL")
  4. Witness Protection (Greyed out: "REQUIRES SENIOR APPROVAL")
  5. Emergency Escalation (Greyed out: "REQUIRES SENIOR APPROVAL")

### 4. WebSocket Backend Integration Variable (`src/App.tsx`)
- Toggle switch between `Mock Data Generator` and `Phase 3 Real WS Connection`.
- Environment Variable: `VITE_WS_URL`
- Default fallback URL: `ws://localhost:8000/ws/triage`

### 5. Administrator Dashboard (`src/components/AdminDashboard.tsx`)
- Total case count & Key Metrics
- Risk-bucket distribution bar chart (Low/Moderate/High/Critical)
- Language distribution bar chart
- Referral volume counts
- Supervisor Review Queue table with "Mark reviewed" actions
- **Privacy Rule**: Any displayed count under 5 renders `"insufficient data"`.

### 6. Accessibility Bridge UI (`src/components/AccessibilityBridgeUI.tsx`)
- Non-verbal text chat interface reusing identical risk-panel and action-panel components as the voice agent console.

### 7. Agent Wellbeing Panel (`src/components/AgentWellbeingPanel.tsx`)
- Supervisor Wellbeing gauge labeled `"Wellbeing Signal (not a performance score)"`.

---

## How to Run & Build

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Production build
npm run build
```
