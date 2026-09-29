import { useState, useEffect, useRef, useCallback } from 'react';
import type { SharedContractMessage, TranscriptUpdateEvent, ActionUpdateEvent, HandoffReceivedEvent } from './types/contract';
import { globalMockGenerator } from './services/mockGenerator';
import { IVRSimUI } from './components/IVRSimUI';
import { AgentConsole } from './components/AgentConsole';
import { AdminDashboard } from './components/AdminDashboard';
import { AccessibilityBridgeUI } from './components/AccessibilityBridgeUI';
import { AgentWellbeingPanel } from './components/AgentWellbeingPanel';
import {
  Phone, LayoutDashboard, MessageSquareText,
  HeartPulse, Shield, Wifi, WifiOff, AlertTriangle, Activity, RotateCcw
} from 'lucide-react';

export interface ChatMessage {
  id: string;
  sender: 'victim' | 'agent';
  text: string;
  timestamp: string;
}

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.host}/ws/triage`;
const DEMO_TOTAL_STEPS = 4;       // 0, 1, 2, 3
const STEP_INTERVAL_MS  = 4000;   // send next step every 4 seconds
const RECONNECT_DELAY_MS = 3000;

// Type definitions for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function App() {
  const [activeTab, setActiveTab] = useState<'ivr' | 'console' | 'admin' | 'accessibility' | 'wellbeing'>('console');
  const [currentUpdate, setCurrentUpdate] = useState<TranscriptUpdateEvent | null>(null);
  const [currentAction, setCurrentAction] = useState<ActionUpdateEvent | null>(null);
  const [useRealConnection, setUseRealConnection] = useState<boolean>(true);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [contractError, setContractError] = useState<string | null>(null);
  const [demoStep, setDemoStep] = useState<number>(0);           // which step we're on (0-3)
  const [demoComplete, setDemoComplete] = useState<boolean>(false);
  const [callActive, setCallActive] = useState<boolean>(false);  // IVR call state (lifted up)
  const [isLiveVoice, setIsLiveVoice] = useState<boolean>(false); // Live Voice Demo state
  const [handoffData, setHandoffData] = useState<HandoffReceivedEvent | null>(null);

  // Chat Mode State
  const [isChatMode, setIsChatMode] = useState<boolean>(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  const wsRef          = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const stepRef        = useRef<number>(0);         // mirrors demoStep for use inside closures
  const simTimerRef    = useRef<number | null>(null);
  const reconnTimerRef = useRef<number | null>(null);
  const shouldConnRef  = useRef<boolean>(false);
  const pendingDtmfRef = useRef<string>('');
  const callActiveRef  = useRef<boolean>(false);    // mirrors callActive for closures
  const isLiveVoiceRef = useRef<boolean>(false);    // mirrors isLiveVoice for closures

  // Keep stepRef in sync with demoStep state
  useEffect(() => { stepRef.current = demoStep; }, [demoStep]);
  useEffect(() => { callActiveRef.current = callActive; }, [callActive]);
  useEffect(() => { isLiveVoiceRef.current = isLiveVoice; }, [isLiveVoice]);

  const fireSos = useCallback(() => {
    setCurrentUpdate((prev) => {
      const baseScores = prev?.risk_vector?.scores || {
        acute_distress: 0, depression: 0, self_harm_risk: 0,
        fear_of_retaliation: 0, intimidation: 0, dissociation: 0,
        social_isolation: 0, chronic_trauma_indicators: 0,
      };
      const baseConf = prev?.risk_vector?.confidence || {
        acute_distress: 0.85, depression: 0.85, self_harm_risk: 0.85,
        fear_of_retaliation: 0.85, intimidation: 0.85, dissociation: 0.85,
        social_isolation: 0.85, chronic_trauma_indicators: 0.85,
      };
      const baseEvid = prev?.risk_vector?.matched_evidence || {};

      return {
        type: 'transcript_update',
        text: (prev?.text ? prev.text + ' ' : '') + '[SILENT SOS — Duress code 9631 detected via keypad]',
        timestamp: new Date().toLocaleTimeString(),
        risk_vector: {
          scores: {
            ...baseScores,
            acute_distress: Math.max(baseScores.acute_distress, 0.95),
            self_harm_risk: Math.max(baseScores.self_harm_risk, 0.80),
            fear_of_retaliation: Math.max(baseScores.fear_of_retaliation, 1.0),
            intimidation: Math.max(baseScores.intimidation, 1.0),
          },
          confidence: {
            ...baseConf,
            acute_distress: 0.99, fear_of_retaliation: 0.99, intimidation: 0.99,
          },
          matched_evidence: {
            ...baseEvid,
            intimidation: [...(baseEvid.intimidation || []), 'Duress key combination 9631 pressed'],
            fear_of_retaliation: [...(baseEvid.fear_of_retaliation || []), 'High-risk silent distress signal active'],
          },
          overall_confidence: 0.99,
        },
        svi: { value: Math.max(prev?.svi?.value || 0, 98), bucket: 'critical' },
        silence_events: prev?.silence_events || [],
        silent_sos_alert: true
      } as TranscriptUpdateEvent;
    });

    setCurrentAction({
      type: 'action_update',
      action: { action: 'police_intervention', state: 'awaiting_senior', requires_senior: true },
    });
  }, []);

  const handleSilentSOSTrigger = useCallback(() => {
    fireSos();
    
    const wasLiveVoice = isLiveVoiceRef.current;

    // Stop any active calls
    setCallActive(false);
    setIsLiveVoice(false);
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    // Send SOS to backend if real connection AND not in live voice mode
    // (If in live voice, sending simulate_chunk would overwrite our live scores with mock dataset step 0)
    if (wsRef.current?.readyState === WebSocket.OPEN && !wasLiveVoice) {
      pendingDtmfRef.current += '9631';
      wsRef.current.send(JSON.stringify({ type: 'simulate_chunk', step: stepRef.current, dtmf: '9631' }));
    }

    // Switch to Chat Mode
    setIsChatMode(true);
    setChatMessages([
      {
        id: '1',
        sender: 'victim',
        text: 'sos i cant speak right now',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      },
      {
        id: '2',
        sender: 'agent',
        text: 'This is the NHAA Trauma Triage Center. I am here. Are you safe to text?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  }, [fireSos]);

  const handleSendMessage = useCallback((text: string, sender: 'victim' | 'agent') => {
    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      sender,
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, newMsg]);

    // Send victim chat messages to backend for live risk analysis
    if (sender === 'victim') {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'live_transcript', text: text, is_interim: false }));
      }
    }
  }, []);

  // ── Parse incoming WS message ──────────────────────────────────────────────
  const handleIncoming = useCallback((raw: unknown) => {
    if (!raw || typeof raw !== 'object' || !('type' in raw)) return;
    const msg = raw as Record<string, unknown>;
    if (msg.type === 'transcript_update') {
      if (typeof msg.text !== 'string' || !msg.svi) {
        setContractError('[Phase 3 Contract Violation] transcript_update malformed'); return;
      }
      setContractError(null);
      setCurrentUpdate(msg as unknown as TranscriptUpdateEvent);
    } else if (msg.type === 'action_update') {
      if (!msg.action) { setContractError('[Phase 3 Contract Violation] action_update malformed'); return; }
      setContractError(null);
      setCurrentAction(msg as unknown as ActionUpdateEvent);
    } else if (msg.type === 'step_complete') {
      // Backend signals all chunks for the current step are done — auto-end the call
      setCallActive(false);
    } else if (msg.type === 'handoff_received') {
      setContractError(null);
      setHandoffData(msg as unknown as HandoffReceivedEvent);
    }
  }, []);

  // ── Send simulate_chunk for a specific step (does NOT advance) ─────────────
  const sendStep = useCallback((ws: WebSocket, step: number) => {
    if (step >= DEMO_TOTAL_STEPS || ws.readyState !== WebSocket.OPEN) return;
    const dtmf = pendingDtmfRef.current;
    pendingDtmfRef.current = '';
    ws.send(JSON.stringify({ type: 'simulate_chunk', step, dtmf }));
  }, []);

  // ── Advance to the next step (Wait for 'Receive Call' to send) ────────────
  const handleNextStep = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const nextStep = stepRef.current + 1;
    if (nextStep >= DEMO_TOTAL_STEPS) {
      setDemoComplete(true);
      return;
    }
    stepRef.current = nextStep;
    setDemoStep(nextStep);
    
    // Reset state for the next call
    setCurrentUpdate(null);
    setCurrentAction(null);
    setCallActive(false);
    setIsLiveVoice(false);
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  // ── Open WebSocket, start step timer, auto-reconnect on drop ──────────────
  const connect = useCallback(() => {
    if (!shouldConnRef.current) return;
    if (wsRef.current && wsRef.current.readyState < WebSocket.CLOSING) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      setContractError(null);
      // Do NOT send step 0 here — wait for user to click "Receive call"
    };

    ws.onmessage = (e) => {
      try { handleIncoming(JSON.parse(e.data)); }
      catch { /* ignore parse errors */ }
    };

    ws.onclose = () => {
      setWsConnected(false);
      if (simTimerRef.current) { clearInterval(simTimerRef.current); simTimerRef.current = null; }
      if (shouldConnRef.current) {
        reconnTimerRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };

    ws.onerror = () => ws.close();
  }, [handleIncoming, sendStep]);

  // ── Effect: Real WS mode on/off ────────────────────────────────────────────
  useEffect(() => {
    if (!useRealConnection) {
      shouldConnRef.current = false;
      if (reconnTimerRef.current) clearTimeout(reconnTimerRef.current);
      if (simTimerRef.current) clearInterval(simTimerRef.current);
      wsRef.current?.close();
      setWsConnected(false);
      return;
    }

    shouldConnRef.current = true;
    connect();

    return () => {
      shouldConnRef.current = false;
      if (reconnTimerRef.current) clearTimeout(reconnTimerRef.current);
      if (simTimerRef.current) clearInterval(simTimerRef.current);
      wsRef.current?.close();
    };
  }, [useRealConnection, connect]);

  // ── Effect: Mock generator (when real WS is off) ───────────────────────────
  useEffect(() => {
    if (useRealConnection) return;
    globalMockGenerator.start();
    const unsub = globalMockGenerator.subscribe((msg: SharedContractMessage) => {
      if (msg.type === 'transcript_update') setCurrentUpdate(msg);
      else if (msg.type === 'action_update') setCurrentAction(msg);
    });
    return () => { globalMockGenerator.stop(); unsub(); };
  }, [useRealConnection]);

  // ── Reset demo ─────────────────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    // Clear all state first
    stepRef.current = 0;
    setDemoStep(0);
    setDemoComplete(false);
    setCallActive(false);
    setCurrentUpdate(null);
    setCurrentAction(null);
    setIsChatMode(false);
    setChatMessages([]);
    pendingDtmfRef.current = '';
    if (simTimerRef.current) { clearInterval(simTimerRef.current); simTimerRef.current = null; }

    // Close existing WS, then reconnect after a short delay
    shouldConnRef.current = false;
    if (reconnTimerRef.current) { clearTimeout(reconnTimerRef.current); reconnTimerRef.current = null; }
    wsRef.current?.close();
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsLiveVoice(false);

    setTimeout(() => {
      shouldConnRef.current = true;
      connect();
    }, 600);
  }, [connect]);

  // ── Handle IVR call state change (Receive call / End call) ─────────────────
  const handleCallStateChange = useCallback((active: boolean) => {
    setCallActive(active);
    if (active) {
      // User clicked "Receive call" — send the current step now
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        sendStep(ws, stepRef.current);
      }
    } else {
      if (isLiveVoice && recognitionRef.current) {
        recognitionRef.current.stop();
        setIsLiveVoice(false);
      }
    }
  }, [sendStep, isLiveVoice]);

  // ── Handle Live Voice Demo Trigger ─────────────────────────────────────────
  const handleLiveVoiceStart = useCallback((lang: 'Hindi' | 'English' | 'Hinglish') => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support the Web Speech API. Please use Chrome or Edge.");
      return;
    }

    setCallActive(true);
    setIsLiveVoice(true);

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true; // Enable interim results for live transcript updates (especially Hindi)
    
    // Dynamically set language based on UI selection
    if (lang === 'Hindi') {
      recognition.lang = 'hi-IN';
    } else if (lang === 'Hinglish') {
      recognition.lang = 'en-IN';
    } else {
      recognition.lang = 'en-US';
    }

    recognition.onresult = (event: any) => {
      const current = event.resultIndex;
      const result = event.results[current];
      const transcript = result[0].transcript;
      const isFinal = result.isFinal;
      
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'live_transcript', text: transcript, is_interim: !isFinal }));
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error);
    };

    recognition.onend = () => {
      if (callActiveRef.current && isLiveVoice) {
        // Restart if it stopped automatically but call is still active
        try { recognition.start(); } catch (e) {}
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isLiveVoice]);

  const handleAdjustConfidence = (conf: number) => {
    globalMockGenerator.setOverallConfidence(conf);
  };

  const tabs = [
    { id: 'ivr' as const,           label: 'Caller IVR',      icon: Phone },
    { id: 'console' as const,       label: 'Agent Console',   icon: Shield },
    { id: 'admin' as const,         label: 'Admin Dashboard', icon: LayoutDashboard },
    { id: 'accessibility' as const, label: 'Non-Verbal Bridge', icon: MessageSquareText },
    { id: 'wellbeing' as const,     label: 'Wellbeing Signal', icon: HeartPulse },
  ];

  const stepLabel = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'][demoStep] ?? 'CRITICAL';

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-gray-100 flex flex-col font-sans">

      {/* ── Navbar ─────────────────────────────────────────────────────────── */}
      <header className="bg-[#131b2e]/90 border-b border-gray-800 backdrop-blur-md sticky top-0 z-50 px-5 py-3 flex items-center justify-between gap-4">

        <div className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide leading-tight">NHAA 14566 Trauma Triage</h1>
            <span className="text-[10px] text-blue-400 font-mono">Merged Pipeline · Phases 1–5</span>
          </div>
        </div>

        <nav className="flex items-center gap-1 bg-gray-900/80 p-1 rounded-xl border border-gray-800">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} id={`tab-${id}`} onClick={() => setActiveTab(id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                activeTab === id ? 'bg-blue-600 text-white shadow shadow-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2 shrink-0">
          {/* Demo step progress */}
          {useRealConnection && (
            <div className="flex items-center gap-2 bg-gray-900/70 px-3 py-1.5 rounded-lg border border-gray-800">
              {[0,1,2,3].map(s => (
                <div key={s} className={`w-2 h-2 rounded-full transition-all ${
                  s < demoStep ? 'bg-emerald-400' : s === demoStep && !demoComplete ? 'bg-blue-400 animate-pulse' : 'bg-gray-700'
                }`} />
              ))}
              <span className="text-[10px] font-mono text-gray-400 ml-1">
                {demoComplete ? 'SCENARIO COMPLETE' : `Step ${demoStep + 1}/${DEMO_TOTAL_STEPS}`}
              </span>
            </div>
          )}

          {/* Reset */}
          {useRealConnection && (
            <button onClick={handleReset} title="Reset demo scenario"
              className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-white bg-gray-900/60 px-2 py-1.5 rounded-lg border border-gray-800 hover:border-gray-600 transition-all">
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          )}

          {/* Next Step */}
          {useRealConnection && !demoComplete && (
            <button onClick={handleNextStep} title="Advance to next step"
              className="flex items-center gap-1 text-[10px] text-emerald-400 hover:text-emerald-300 bg-gray-900/60 px-2 py-1.5 rounded-lg border border-emerald-800 hover:border-emerald-600 transition-all ml-1">
              Next Step
            </button>
          )}

          {/* WS toggle */}
          <label className="flex items-center gap-2 text-xs text-gray-300 bg-gray-900/60 px-3 py-1.5 rounded-lg border border-gray-800 cursor-pointer select-none">
            <input id="toggle-ws" type="checkbox" checked={useRealConnection}
              onChange={e => setUseRealConnection(e.target.checked)} className="accent-blue-500" />
            <span>Live Backend</span>
          </label>

          {/* Connection badge */}
          {wsConnected ? (
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 border border-emerald-700/50 bg-emerald-950/40 px-2 py-1 rounded">
              <Wifi className="w-3 h-3" />CONNECTED
            </span>
          ) : useRealConnection ? (
            <span className="flex items-center gap-1 text-[10px] font-mono text-amber-400 border border-amber-700/50 bg-amber-950/40 px-2 py-1 rounded">
              <Activity className="w-3 h-3 animate-spin" />RECONNECTING
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] font-mono text-gray-400 border border-gray-700 bg-gray-900/40 px-2 py-1 rounded">
              <WifiOff className="w-3 h-3" />MOCK
            </span>
          )}
        </div>
      </header>

      {/* ── Contract Error Banner ───────────────────────────────────────────── */}
      {contractError && (
        <div className="bg-rose-950/90 border-b border-rose-600/60 px-6 py-2 flex items-center justify-between text-xs text-rose-200 font-mono">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" /><span>{contractError}</span>
          </div>
          <span className="text-[10px] bg-rose-900/80 px-2 py-0.5 rounded text-rose-300">Phase 3 Backend Bug Flagged</span>
        </div>
      )}

      {/* ── Main ───────────────────────────────────────────────────────────── */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {/* Use display:none instead of unmounting to preserve component state across tab switches */}
        <div style={{ display: activeTab === 'ivr' ? 'block' : 'none' }}>
          <IVRSimUI 
            callActive={callActive} 
            isLiveVoiceActive={isLiveVoice} 
            isChatMode={isChatMode}
            chatMessages={chatMessages}
            onSendMessage={(text) => handleSendMessage(text, 'victim')}
            onCallStateChange={handleCallStateChange} 
            onSilentSOSTrigger={handleSilentSOSTrigger} 
            onLiveVoiceTrigger={handleLiveVoiceStart} 
          />
        </div>
        <div style={{ display: activeTab === 'console' ? 'block' : 'none' }}>
          <AgentConsole 
            key={`console-${demoStep}`} 
            currentUpdate={currentUpdate} 
            currentAction={currentAction} 
            handoffData={handoffData} 
            isChatMode={isChatMode}
            chatMessages={chatMessages}
            onSendMessage={(text) => handleSendMessage(text, 'agent')}
            onTriggerSilentSOS={handleSilentSOSTrigger} 
            onAdjustConfidence={handleAdjustConfidence} 
          />
        </div>
        <div style={{ display: activeTab === 'admin' ? 'block' : 'none' }}>
          <AdminDashboard />
        </div>
        <div style={{ display: activeTab === 'accessibility' ? 'block' : 'none' }}>
          <AccessibilityBridgeUI 
            currentUpdate={currentUpdate} 
            currentAction={currentAction} 
            onAdjustConfidence={handleAdjustConfidence}
            onAnalyzeText={(text) => {
              const ws = wsRef.current;
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'live_transcript', text: text, is_interim: false }));
              }
            }}
          />
        </div>
        <div style={{ display: activeTab === 'wellbeing' ? 'block' : 'none' }}>
          <AgentWellbeingPanel />
        </div>
      </main>

      <footer className="border-t border-gray-800 py-3 px-6 text-center text-xs text-gray-500 flex flex-col gap-2">
        <span>NHAA 14566 · Merged Phase 1–5 Pipeline · Strictly adhering to contract schema</span>
        <div id="debug-json" className="text-left text-[10px] text-green-400 font-mono bg-black p-2 overflow-auto max-h-40">
          RAW WS JSON: {currentUpdate ? JSON.stringify(currentUpdate) : "None"}
        </div>
      </footer>
    </div>
  );
}

export default App;
