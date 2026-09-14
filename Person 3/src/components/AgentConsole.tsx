import { useState, useEffect, useRef } from 'react';
import type { TranscriptUpdateEvent, ActionUpdateEvent, ActionState, HandoffReceivedEvent } from '../types/contract';
import { Lock, ShieldAlert, CheckCircle2, Clock, VolumeX, Eye, AlertTriangle, Send } from 'lucide-react';
import type { ChatMessage } from '../App';

interface AgentConsoleProps {
  currentUpdate: TranscriptUpdateEvent | null;
  currentAction: ActionUpdateEvent | null;
  handoffData?: HandoffReceivedEvent | null;
  isChatMode?: boolean;
  chatMessages?: ChatMessage[];
  onSendMessage?: (text: string) => void;
  onTriggerSilentSOS?: () => void;
  onAdjustConfidence?: (conf: number) => void;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({
  currentUpdate,
  currentAction,
  handoffData,
  isChatMode = false,
  chatMessages = [],
  onSendMessage,
  onAdjustConfidence
}) => {
  const [transcriptHistory, setTranscriptHistory] = useState<{ text: string; time: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [actions, setActions] = useState<Record<string, ActionState>>({
    counseling_referral: { action: 'counseling_referral', state: 'not_requested', requires_senior: false },
    legal_aid: { action: 'legal_aid', state: 'not_requested', requires_senior: false },
    police_intervention: { action: 'police_intervention', state: 'awaiting_senior', requires_senior: true },
    witness_protection: { action: 'witness_protection', state: 'awaiting_senior', requires_senior: true },
    emergency_escalation: { action: 'emergency_escalation', state: 'awaiting_senior', requires_senior: true }
  });

  const [timeline, setTimeline] = useState<{ time: string; text: string }[]>([]);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  
  const backendConfidence = currentUpdate?.overall_confidence ?? 90;
  const [localConfidence, setLocalConfidence] = useState<number>(backendConfidence);

  // Sync local confidence when backend confidence updates significantly, 
  // but allow user to slide it for testing
  useEffect(() => {
    setLocalConfidence(backendConfidence);
  }, [backendConfidence]);

  useEffect(() => {
    if (currentUpdate) {
      if (currentUpdate.text) {
        setTranscriptHistory(prev => {
          // Prevent exact duplicates caused by React StrictMode double-firing
          const isDuplicate = prev.length > 0 && prev[prev.length - 1].text === currentUpdate.text;
          if (isDuplicate) return prev;
          
          return [
            ...prev,
            { text: currentUpdate.text, time: currentUpdate.timestamp || new Date().toLocaleTimeString() }
          ];
        });
      }

      const timeStr = currentUpdate.timestamp || new Date().toLocaleTimeString();
      const sviVal = currentUpdate.svi?.value || 0;
      if (sviVal > 75) {
        setTimeline(prev => [...prev, { time: timeStr, text: `Critical risk detected (SVI: ${sviVal})` }]);
      } else if (sviVal > 50) {
        setTimeline(prev => [...prev, { time: timeStr, text: `High risk distress detected (SVI: ${sviVal})` }]);
      } else if (sviVal > 25) {
        setTimeline(prev => [...prev, { time: timeStr, text: `Moderate risk signals detected` }]);
      }
    }
  }, [currentUpdate]);

  useEffect(() => {
    if (currentAction) {
      setActions(prev => ({
        ...prev,
        [currentAction.action.action]: currentAction.action
      }));
    }
  }, [currentAction]);

  // ── Handoff received: pre-populate all panels instantly ────────────────────
  const [handoffApplied, setHandoffApplied] = useState(false);

  useEffect(() => {
    if (!handoffData || handoffApplied) return;

    // 1. System note in transcript
    const noteTime = new Date().toLocaleTimeString();
    setTranscriptHistory(prev => [
      ...prev,
      {
        text: `\u26A0\uFE0F Call transferred from Agent ${handoffData.from_agent} \u2014 reason: ${handoffData.reason}`,
        time: noteTime,
      },
    ]);

    // 2. Pre-fill timeline
    if (handoffData.timeline && handoffData.timeline.length > 0) {
      const timelineEntries = handoffData.timeline.map((entry) => {
        if (typeof entry === 'string') {
          const parts = entry.split(' \u2014 ');
          return { time: parts[0] || noteTime, text: parts[1] || entry };
        }
        return entry as { time: string; text: string };
      });
      // Add a handoff event to the timeline
      timelineEntries.push({
        time: noteTime,
        text: `Call handed off from Agent ${handoffData.from_agent} to receiving agent`,
      });
      setTimeline(timelineEntries);
    }

    // 3. Synthesize a TranscriptUpdateEvent so risk bars / SVI / evidence render
    const syntheticUpdate: TranscriptUpdateEvent = {
      type: 'transcript_update',
      text: '',
      timestamp: noteTime,
      risk_vector: {
        scores: handoffData.risk_vector?.scores || ({} as any),
        confidence: handoffData.risk_vector?.confidence || {},
        matched_evidence: handoffData.evidence || {},
        overall_confidence: handoffData.risk_vector?.confidence
          ? Math.round(Math.min(...Object.values(handoffData.risk_vector.confidence).filter((v): v is number => v != null)) * 100)
          : 85,
      },
      svi: handoffData.svi || { value: 0, bucket: 'low' as const },
      silence_events: handoffData.silence_events || [],
    };
    setCurrentUpdate(syntheticUpdate);

    setHandoffApplied(true);
  }, [handoffData, handoffApplied]);

  // Allow parent to push synthetic updates from handoff
  const [overrideUpdate, setOverrideUpdate] = useState<TranscriptUpdateEvent | null>(null);
  const setCurrentUpdate = (update: TranscriptUpdateEvent) => setOverrideUpdate(update);
  const effectiveUpdate = overrideUpdate || currentUpdate;

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptHistory]);

  const scores = effectiveUpdate?.risk_vector?.scores || {
    acute_distress: 0,
    depression: 0,
    self_harm_risk: 0,
    fear_of_retaliation: 0,
    intimidation: 0,
    dissociation: 0,
    social_isolation: 0,
    chronic_trauma_indicators: 0
  };

  const confidenceMap = effectiveUpdate?.risk_vector?.confidence || {};
  const matchedEvidence = effectiveUpdate?.risk_vector?.matched_evidence || {};

  const sviValue = effectiveUpdate?.svi?.value || 0;
  // Use localConfidence for UI display to prevent it getting stuck
  const displayConfidence = localConfidence;

  const getSviBadgeStyle = (val: number) => {
    if (val >= 76) return { bg: 'bg-red-500/20 border-red-500/50 text-red-400', label: 'CRITICAL', ring: 'ring-red-500/40' };
    if (val >= 51) return { bg: 'bg-orange-500/20 border-orange-500/50 text-orange-400', label: 'HIGH', ring: 'ring-orange-500/40' };
    if (val >= 26) return { bg: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400', label: 'MODERATE', ring: 'ring-yellow-500/40' };
    return { bg: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400', label: 'LOW', ring: 'ring-emerald-500/40' };
  };

  const sviStyle = getSviBadgeStyle(sviValue);

  const silenceAlert = effectiveUpdate?.silence_events?.find(
    s => s.placement === 'mid_sentence' && s.duration_sec > 2
  );

  const isSilentSOS = effectiveUpdate?.silent_sos_alert || effectiveUpdate?.text?.includes("SILENT SOS");

  const getConfBadge = (confPercent: number = 85) => {
    if (confPercent >= 80) return { color: 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40', text: `${confPercent}%` };
    if (confPercent >= 50) return { color: 'text-yellow-400 border-yellow-500/30 bg-yellow-950/40', text: `${confPercent}%` };
    return { color: 'text-red-400 border-red-500/30 bg-red-950/40', text: `${confPercent}%` };
  };

  const dimensionList = [
    { key: 'acute_distress', label: 'Acute Distress' },
    { key: 'depression', label: 'Depression' },
    { key: 'self_harm_risk', label: 'Self-Harm Risk' },
    { key: 'fear_of_retaliation', label: 'Fear of Retaliation' },
    { key: 'intimidation', label: 'Intimidation' },
    { key: 'dissociation', label: 'Dissociation' },
    { key: 'social_isolation', label: 'Social Isolation' },
    { key: 'chronic_trauma_indicators', label: 'Chronic Trauma' }
  ] as const;

  const suggestedActionRows = [
    { key: 'counseling_referral', label: 'Counseling', requiresSenior: false },
    { key: 'legal_aid', label: 'Legal Aid', requiresSenior: false },
    { key: 'police_intervention', label: 'Police Intervention', requiresSenior: true },
    { key: 'witness_protection', label: 'Witness Protection', requiresSenior: true },
    { key: 'emergency_escalation', label: 'Emergency Escalation', requiresSenior: true }
  ];

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto animate-fade-in-up">
      {silenceAlert && (
        <div className="bg-amber-950/90 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-lg flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-3">
            <VolumeX className="w-6 h-6 text-amber-400 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-amber-200">Silence Alert Triggered</h4>
              <p className="text-xs text-amber-300/80">Unusual mid-narrative silence detected ({silenceAlert.duration_sec}s pause mid-sentence)</p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-mono px-2 py-1 bg-amber-900/60 border border-amber-500/40 rounded text-amber-300">Dissociation Signal</span>
        </div>
      )}

      {isSilentSOS && (
        <div className="bg-red-500/20 border border-red-500/50 p-4 rounded-xl flex items-center gap-4 animate-bounce shadow-[0_0_20px_rgba(239,68,68,0.3)]">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-7 h-7 text-red-500 flex-shrink-0" />
            <div>
              <h4 className="text-base font-extrabold text-red-100 uppercase tracking-wide">Silent SOS Triggered</h4>
              <p className="text-xs text-red-300">Caller activated duress signal. Speaker cannot talk freely. High threat level active.</p>
            </div>
          </div>
          <span className="text-xs font-bold px-3 py-1.5 bg-red-600 text-white rounded-lg shadow">IMMEDIATE ATTENTION REQUIRED</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className={`glass-panel p-5 rounded-2xl border flex flex-col justify-between transition-colors duration-500 hover-lift ${sviStyle.bg}`}>
          <div>
            <span className="text-xs uppercase tracking-wider text-gray-400 font-medium">Stress Vulnerability Index</span>
            <div className="text-4xl font-extrabold font-mono tracking-tight mt-1 flex items-baseline gap-2">
              <span>{sviValue}</span>
              <span className="text-sm font-sans font-normal text-gray-400">/ 100</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${sviStyle.bg}`}>
              {sviStyle.label} RISK
            </span>
            <span className="text-[11px] text-gray-400 font-mono">Weighted 8-Dim Matrix</span>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between hover-lift md:col-span-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">System-wide AI Confidence</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Test confidence:</span>
              <input
                type="range"
                min="30"
                max="99"
                value={localConfidence}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setLocalConfidence(val);
                  onAdjustConfidence && onAdjustConfidence(val);
                }}
                className="w-24 accent-blue-500 cursor-pointer"
              />
              <span className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono border transition-colors ${getConfBadge(localConfidence).color}`}>
                {localConfidence}%
              </span>
            </div>
          </div>

          <div className="mt-2">
            {localConfidence < 50 ? (
              <div className="p-2.5 bg-red-950/80 border border-red-600/60 rounded-lg flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <span className="text-xs font-semibold text-red-300">
                  Low confidence -- this recommendation should not be used for high-stakes action alone
                </span>
              </div>
            ) : (
              <p className="text-xs text-gray-400">
                Confidence rating calibrated across NLP lexical vectors, acoustic pitch variance, and speech pause analysis.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 flex flex-col gap-6">
          {isChatMode ? (
            <div className="glass-panel rounded-2xl flex flex-col h-[360px] animate-fade-in-up stagger-1 scroll-reveal overflow-hidden border-blue-900/50">
              <div className="flex items-center justify-between border-b border-gray-800 p-3 bg-blue-950/40">
                <h3 className="text-sm font-bold text-blue-300 uppercase tracking-wide flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span> Active SOS Text Session
                </h3>
                <span className="text-[10px] text-gray-500 font-mono">End-to-End Encrypted</span>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-3 font-sans text-sm bg-gray-950/50">
                {chatMessages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.sender === 'agent' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] rounded-2xl px-4 py-2 ${msg.sender === 'agent' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-gray-800 text-gray-200 rounded-bl-sm border border-gray-700'}`}>
                      <p>{msg.text}</p>
                      <span className={`text-[10px] mt-1 block ${msg.sender === 'agent' ? 'text-blue-200' : 'text-gray-500'}`}>{msg.timestamp}</span>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              <div className="p-3 border-t border-gray-800 bg-gray-900/50 flex gap-2">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && chatInput.trim()) {
                      onSendMessage?.(chatInput.trim());
                      setChatInput("");
                    }
                  }}
                  placeholder="Type reply to victim..."
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-full px-4 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
                />
                <button 
                  onClick={() => {
                    if (chatInput.trim()) {
                      onSendMessage?.(chatInput.trim());
                      setChatInput("");
                    }
                  }}
                  className="w-10 h-10 bg-blue-600 hover:bg-blue-500 text-white rounded-full flex items-center justify-center transition"
                >
                  <Send className="w-4 h-4 ml-1" />
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-5 rounded-2xl flex flex-col h-[360px] animate-fade-in-up stagger-1 scroll-reveal">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-3">
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span> Live Audio Transcript
                </h3>
                <span className="text-[10px] text-gray-500 font-mono">Real-time Stream</span>
              </div>
  
              <div className="flex-1 overflow-y-auto pr-2 space-y-3 font-sans text-sm">
                {transcriptHistory.length === 0 ? (
                  <div className="text-center text-gray-500 pt-16 text-xs italic">
                    Waiting for incoming caller speech stream...
                  </div>
                ) : (
                  transcriptHistory.map((item, idx) => (
                    <div key={idx} className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-3">
                      <div className="text-[10px] text-blue-400 font-mono mb-1">{item.time}</div>
                      <div className="text-gray-200 leading-relaxed text-xs">{item.text}</div>
                    </div>
                  ))
                )}
                <div ref={transcriptEndRef} />
              </div>
            </div>
          )}

          <div className="glass-panel p-5 rounded-2xl flex flex-col h-[220px]">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2 mb-3">
              <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-blue-400" /> Case Timeline Events
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 text-xs font-mono pr-1">
              {timeline.length === 0 ? (
                <div className="text-gray-500 text-[11px] italic">No significant events logged yet</div>
              ) : (
                timeline.map((evt, i) => (
                  <div key={i} className="flex items-center gap-2 text-gray-300 border-b border-gray-800/40 pb-1.5">
                    <span className="text-blue-400 font-bold">{evt.time}</span>
                    <span>--</span>
                    <span className="text-gray-300">{evt.text}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="glass-panel p-5 rounded-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
                8 Observable Risk Dimensions
              </h3>
              <span className="text-[10px] text-gray-400">Score & Confidence</span>
            </div>

            <div className="grid grid-cols-1 gap-3.5">
              {dimensionList.map(({ key, label }) => {
                const rawVal = scores[key] || 0;
                // Normalize: backend sends 0.0–1.0; mock generator sends 0–100
                const val = rawVal <= 1.0 ? rawVal * 100 : rawVal;
                const rawConf = confidenceMap[key];
                // Confidence: backend sends 0.0–1.0, default 85
                const confVal = rawConf == null ? 85 : rawConf <= 1.0 ? Math.round(rawConf * 100) : rawConf;
                const evidenceList = matchedEvidence[key] || [];

                return (
                  <div key={key} className="flex flex-col gap-1 bg-gray-900/40 p-2.5 rounded-xl border border-gray-800/60 hover-lift hover:bg-gray-800/50 transition-all">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-gray-200">{label}</span>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 text-[10px] font-mono rounded border ${getConfBadge(confVal).color}`}>
                          Conf: {confVal}%
                        </span>
                        <span className="font-mono font-bold text-gray-300 w-10 text-right">{Math.round(val)}%</span>
                      </div>
                    </div>

                    <div className="w-full bg-gray-950 rounded-full h-2 overflow-hidden border border-gray-800">
                      <div
                        className={`h-full transition-all duration-700 rounded-full ${
                          val >= 75 ? 'bg-red-500 shadow-sm shadow-red-500/50' :
                          val >= 50 ? 'bg-orange-500' :
                          val >= 25 ? 'bg-yellow-500' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(val > 0 ? 3 : 0, val))}%` }}
                      />
                    </div>

                    {val > 0 && evidenceList.length > 0 && (
                      <div className="mt-1 text-[11px] text-blue-300/90 bg-blue-950/30 px-2 py-1 rounded border border-blue-800/30 flex items-start gap-1">
                        <span className="font-semibold text-blue-400">Evidence:</span>
                        <span>"{evidenceList.join(', ')}"</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
                Suggested Actions Panel
              </h3>
              <span className="text-[10px] text-gray-400">Human-Gated Approval</span>
            </div>

            <div className="flex flex-col gap-2.5">
              {suggestedActionRows.map(({ key, label, requiresSenior }) => {
                const actionData = actions[key] || { state: 'not_requested' };
                const isNotRequested = actionData.state === 'not_requested';
                const isBlocked = requiresSenior && actionData.state !== 'approved';
                const isDisabled = isNotRequested || isBlocked;

                return (
                  <div
                    key={key}
                    className={`p-3.5 rounded-xl border flex items-center justify-between transition-all hover-lift ${
                      isNotRequested
                        ? 'bg-gray-950/40 border-gray-800/50 text-gray-600 opacity-60'
                        : isBlocked
                        ? 'bg-gray-950/60 border-gray-800/80 text-gray-500 opacity-75'
                        : 'bg-gray-900/80 border-blue-500/30 text-gray-200 hover:border-blue-500/60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {isNotRequested ? (
                        <div className="w-4 h-4 rounded-full border border-gray-600" />
                      ) : isBlocked ? (
                        <Lock className="w-4 h-4 text-amber-500/70" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      )}
                      <div>
                        <div className="text-xs font-semibold">{label}</div>
                        {isBlocked && !isNotRequested && (
                          <div className="text-[10px] font-bold text-amber-400/90 tracking-wider mt-0.5">
                            REQUIRES SENIOR APPROVAL
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <span className={`px-2.5 py-1 text-[10px] font-bold uppercase rounded border ${
                        isNotRequested
                          ? 'bg-gray-900/50 text-gray-500 border-gray-700/50'
                          : isBlocked
                          ? 'bg-amber-950/40 text-amber-400 border-amber-500/30'
                          : 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30'
                      }`}>
                        {isNotRequested ? 'Not Suggested' : isBlocked ? 'Awaiting Senior Sign-Off' : 'Ready / Agent Confirmed'}
                      </span>
                      {!isDisabled && (
                        <div className="bg-blue-950/40 border border-blue-500/30 rounded-lg p-2 flex flex-col gap-1 items-end mt-1 animate-fade-in-up">
                          <span className="text-[10px] text-blue-300 font-semibold">
                            Next Available Slot: Today, 4:30 PM
                          </span>
                          <button className="text-[10px] bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded transition-colors shadow-sm">
                            Book Warm Hand-off
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
