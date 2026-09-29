import type { SharedContractMessage, TranscriptUpdateEvent, ActionUpdateEvent } from '../types/contract';

const SAMPLE_TRANSCRIPT_STEPS = [
  {
    text: "Namaste, I am calling from a village in District B. Things are getting very difficult here...",
    scores: { acute_distress: 15, depression: 10, self_harm_risk: 0, fear_of_retaliation: 20, intimidation: 10, dissociation: 5, social_isolation: 15, chronic_trauma_indicators: 25 },
    evidence: { acute_distress: ["difficult here"], fear_of_retaliation: ["village situation"] },
    silence: []
  },
  {
    text: "They have threatened our family after we registered the complaint at the local office.",
    scores: { acute_distress: 35, depression: 20, self_harm_risk: 5, fear_of_retaliation: 55, intimidation: 60, dissociation: 10, social_isolation: 30, chronic_trauma_indicators: 40 },
    evidence: { fear_of_retaliation: ["threatened our family"], intimidation: ["registered the complaint"] },
    silence: [{ start_sec: 12.4, duration_sec: 2.8, placement: 'mid_sentence' as const }]
  },
  {
    text: "Some men are standing outside our house right now. I don't know who to turn to...",
    scores: { acute_distress: 70, depression: 35, self_harm_risk: 15, fear_of_retaliation: 85, intimidation: 90, dissociation: 45, social_isolation: 60, chronic_trauma_indicators: 50 },
    evidence: { acute_distress: ["don't know who to turn to"], intimidation: ["standing outside our house right now"], fear_of_retaliation: ["standing outside"] },
    silence: []
  },
  {
    text: "I feel completely hopeless and scared... [Silence] ...Please send someone immediately.",
    scores: { acute_distress: 90, depression: 75, self_harm_risk: 45, fear_of_retaliation: 95, intimidation: 95, dissociation: 80, social_isolation: 80, chronic_trauma_indicators: 75 },
    evidence: { acute_distress: ["scared", "immediately"], depression: ["completely hopeless"], intimidation: ["send someone immediately"] },
    silence: [{ start_sec: 28.1, duration_sec: 3.5, placement: 'mid_sentence' as const }]
  }
];

export class MockDataGenerator {
  private stepIndex = 0;
  private intervalId: number | null = null;
  private listeners: ((msg: SharedContractMessage) => void)[] = [];
  private isRunning = false;
  private overallConfidence = 92;

  public subscribe(callback: (msg: SharedContractMessage) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  private emit(msg: SharedContractMessage) {
    this.listeners.forEach(l => l(msg));
  }

  public setOverallConfidence(conf: number) {
    this.overallConfidence = conf;
    this.emitCurrentStep();
  }

  public start() {
    if (this.isRunning) return;
    this.isRunning = true;
    this.stepIndex = 0;
    this.emitCurrentStep();

    this.intervalId = window.setInterval(() => {
      this.stepIndex = (this.stepIndex + 1) % SAMPLE_TRANSCRIPT_STEPS.length;
      this.emitCurrentStep();
    }, 2000);
  }

  public stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
  }

  public triggerSilentSOS() {
    const sosMessage: SharedContractMessage = {
      type: 'transcript_update',
      text: "[SILENT SOS DURESS SIGNAL DETECTED VIA KEYPAD / DTMF]",
      timestamp: new Date().toLocaleTimeString(),
      risk_vector: {
        scores: {
          acute_distress: 95,
          depression: 50,
          self_harm_risk: 80,
          fear_of_retaliation: 100,
          intimidation: 100,
          dissociation: 70,
          social_isolation: 90,
          chronic_trauma_indicators: 85
        },
        confidence: {
          acute_distress: 99,
          fear_of_retaliation: 99,
          intimidation: 99
        },
        matched_evidence: {
          intimidation: ["Duress key combination 999# pressed"],
          fear_of_retaliation: ["High-risk silent distress signal active"]
        }
      },
      svi: {
        value: 98,
        bucket: 'critical'
      },
      silence_events: [{ start_sec: 0, duration_sec: 10, placement: 'mid_sentence' }],
      overall_confidence: this.overallConfidence
    };
    this.emit(sosMessage);

    const actionMsg: ActionUpdateEvent = {
      type: 'action_update',
      action: {
        action: 'police_intervention',
        state: 'awaiting_senior',
        requires_senior: true
      }
    };
    this.emit(actionMsg);
  }

  private emitCurrentStep() {
    const current = SAMPLE_TRANSCRIPT_STEPS[this.stepIndex];

    const weights = {
      acute_distress: 0.15,
      depression: 0.10,
      self_harm_risk: 0.20,
      fear_of_retaliation: 0.15,
      intimidation: 0.20,
      dissociation: 0.05,
      social_isolation: 0.05,
      chronic_trauma_indicators: 0.10
    };

    let sviValue = Math.round(
      current.scores.acute_distress * weights.acute_distress +
      current.scores.depression * weights.depression +
      current.scores.self_harm_risk * weights.self_harm_risk +
      current.scores.fear_of_retaliation * weights.fear_of_retaliation +
      current.scores.intimidation * weights.intimidation +
      current.scores.dissociation * weights.dissociation +
      current.scores.social_isolation * weights.social_isolation +
      current.scores.chronic_trauma_indicators * weights.chronic_trauma_indicators
    );

    const baselineSvi = [20, 48, 72, 88][this.stepIndex];
    sviValue = Math.max(sviValue, baselineSvi);

    let bucket: 'low' | 'moderate' | 'high' | 'critical' = 'low';
    if (sviValue >= 76) bucket = 'critical';
    else if (sviValue >= 51) bucket = 'high';
    else if (sviValue >= 26) bucket = 'moderate';

    const confidenceObj: Record<string, number> = {};
    Object.keys(current.scores).forEach(key => {
      confidenceObj[key] = Math.floor(75 + Math.random() * 20);
    });

    const updateEvent: TranscriptUpdateEvent = {
      type: 'transcript_update',
      text: current.text,
      timestamp: new Date().toLocaleTimeString(),
      risk_vector: {
        scores: current.scores,
        confidence: confidenceObj,
        matched_evidence: current.evidence
      },
      svi: {
        value: sviValue,
        bucket
      },
      silence_events: current.silence,
      overall_confidence: this.overallConfidence
    };

    this.emit(updateEvent);
  }
}

export const globalMockGenerator = new MockDataGenerator();
