# B²CD - AI-Based Real-Time Stress and Trauma Assessment Module (NHAA 14566)

## Overview
This repository contains the completely redesigned AI processing pipeline for the **Smart India Hackathon 2026** (Problem Statement 26093). It acts as a real-time stress and trauma assessment module for victims and complainants accessing the NHAA (14566) and integrated portal.

### The Key Concept
* **Deep Semantic Triage Layer:** Works in parallel with Human Agents across Voice, IVRS, Chatbot, and Web Portals using an **XLM-RoBERTa Deep Learning NLP** model trained for Hindi, English, and Code-Mixed (Hinglish) speech.
* **Stress Vulnerability Index (SVI):** A single transparent score between 0-100 derived from 8 independently scored risk factors, categorizing callers into Low, Moderate, High, or Critical risk.
* **Human-in-the-loop:** AI suggests, but a human always takes the decision. No irreversible action is performed autonomously.
* **Unique Features:** Compound Threat Decoding, Silence Fingerprint, Silent SOS duress code, and Hash-chain tamper-proof audit trails.

## Architecture

The system receives input from multiple channels (Voice Call, Chatbot, Mobile App, Web Portal, IVRS) and passes them through a 6-layer AI Processing Engine:
1. **L1:** STT + Lang Detection
2. **L2:** NLP / Lexical Analysis
3. **L3:** Speech Analytics
4. **L4:** Silence Fingerprint
5. **L5:** 8-Dimension Risk Scorer
6. **L6:** SVI Calculator (0-100)

The outputs include a Live Agent Console and a Senior Gate for escalated critical cases.

## The 8 Risk Aspects (SVI Dimensions)
1. **Acute Distress** - Tension spikes (PHQ-9/GAD-7 indicators)
2. **Depression** - PHQ-9 markers
3. **Self-Harm Risk** - Explicit/implicit disclosures
4. **Fear of Retaliation** - External threats
5. **Intimidation** - Coercive language
6. **Dissociation** - Interruptions and withdrawal
7. **Chronic Trauma** - PC-PTSD-5 indicators
8. **Social Isolation** - UCLA Loneliness Scale markers

## Technologies & Methods
* **Speech-to-Text:** Real-time ASR with word-level timestamps (Hindi/English/code-switched).
* **NLP Layer:** Deep Semantic Transformer Pipeline (XLM-RoBERTa 278M parameters) with fine-tuned attention matrices for cross-lingual zero-shot generalization.
* **Emotion AI:** Paralinguistic acoustic modeling as supportive evidence.
* **Silence Analytics:** Duration, sentence position, and pre-word pause scoring.
* **Backend:** FastAPI, WebSockets
* **Machine Learning:** PyTorch, Scikit-Learn
* **Frontend UI:** React + TypeScript

## Open Source Commitment
The entire pipeline, including optimized SVI thresholds and the multi-lingual synthetic fine-tuning dataset, is open-source under the MIT License to enable complete transparency and continued research.
