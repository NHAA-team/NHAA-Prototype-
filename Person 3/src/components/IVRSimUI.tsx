import React, { useState, useEffect, useRef } from 'react';
import { Phone, Globe, Shield, Volume2, AlertTriangle, Send } from 'lucide-react';
import type { ChatMessage } from '../App';

interface IVRSimProps {
  callActive?: boolean;
  isLiveVoiceActive?: boolean;
  isChatMode?: boolean;
  chatMessages?: ChatMessage[];
  onSendMessage?: (text: string) => void;
  onCallStateChange?: (active: boolean) => void;
  onSilentSOSTrigger?: () => void;
  onLiveVoiceTrigger?: (lang: 'Hindi' | 'English' | 'Hinglish') => void;
}

export const IVRSimUI: React.FC<IVRSimProps> = ({ 
  callActive = false, 
  isLiveVoiceActive = false, 
  isChatMode = false,
  chatMessages = [],
  onSendMessage,
  onCallStateChange, 
  onSilentSOSTrigger, 
  onLiveVoiceTrigger 
}) => {
  const [language, setLanguage] = useState<'Hindi' | 'English' | 'Hinglish'>('Hindi');
  const [seconds, setSeconds] = useState<number>(0);
  const [chatInput, setChatInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  const [recordingConsent, setRecordingConsent] = useState<boolean>(true);
  const [aiConsent, setAiConsent] = useState<boolean>(true);
  const [improveConsent, setImproveConsent] = useState<boolean>(false);

  useEffect(() => {
    let timer: number;
    if (callActive) {
      timer = window.setInterval(() => {
        setSeconds(prev => prev + 1);
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => clearInterval(timer);
  }, [callActive]);

  const handleStartCall = () => {
    if (onCallStateChange) onCallStateChange(true);
  };

  const handleEndCall = () => {
    if (onCallStateChange) onCallStateChange(false);
  };

  const handleDeclineAll = () => {
    setRecordingConsent(false);
    setAiConsent(false);
    setImproveConsent(false);
  };

  const handleAcceptSelected = () => {
  };

  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="glass-panel p-6 shadow-2xl border border-blue-500/20 rounded-2xl flex flex-col gap-6 max-w-md mx-auto">
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-blue-400 font-semibold">IVR Call Simulator</span>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            NHAA 14566 -- incoming
          </h2>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ${callActive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse' : 'bg-gray-800 text-gray-400'}`}>
          <span className={`w-2 h-2 rounded-full ${callActive ? 'bg-emerald-400' : 'bg-gray-500'}`}></span>
          {callActive ? 'LIVE CALL' : 'STANDBY'}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-gray-400 flex items-center gap-1">
          <Globe className="w-3.5 h-3.5 text-blue-400" /> Caller Language Selection
        </label>
        <select 
          value={language}
          onChange={(e) => setLanguage(e.target.value as any)}
          disabled={callActive}
          className="bg-gray-900/80 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
        >
          <option value="Hindi">Hindi (हिन्दी)</option>
          <option value="English">English</option>
          <option value="Hinglish">Hinglish (Code-switched)</option>
        </select>
      </div>

      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 flex flex-col gap-3 animate-fade-in-up stagger-1">
        <div className="flex items-center justify-between border-b border-gray-800 pb-2">
          <span className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-blue-400" /> Pre-Call Upfront Consent
          </span>
          <span className="text-[10px] text-gray-500">Required Gate</span>
        </div>

        <div className="text-[11px] text-gray-400 leading-relaxed italic bg-gray-950/50 p-3 rounded-lg border border-gray-800/80">
          "Welcome to the NHAA 14566 helpline. To help us support you better, this call may be recorded and analysed by an AI assistant to ensure we don't miss any important details. 
          <br/><br/>
          <strong className="text-gray-300">If you are in a situation where you cannot speak freely, you may enter 9631 on your keypad at any time without saying anything.</strong>"
        </div>

        <div className="flex flex-col gap-2 text-xs mt-1">
          <label className="flex items-center gap-2 text-gray-300 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={recordingConsent} 
              onChange={(e) => setRecordingConsent(e.target.checked)}
              disabled={callActive}
              className="accent-blue-500 rounded"
            />
            <span>I consent to recording and AI analysis</span>
          </label>

          <label className="flex items-center gap-2 text-gray-400 cursor-pointer hover:text-gray-300 transition-colors">
            <input 
              type="checkbox" 
              checked={improveConsent} 
              onChange={(e) => setImproveConsent(e.target.checked)}
              disabled={callActive}
              className="accent-blue-500 rounded"
            />
            <span>I consent to anonymised data being used to improve this system</span>
          </label>
        </div>

        <div className="flex gap-2 pt-2">
          <button 
            type="button" 
            onClick={handleDeclineAll}
            disabled={callActive}
            className="flex-1 py-2 px-3 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 rounded-lg text-xs font-semibold transition-all hover-lift"
          >
            Decline
          </button>
          <button 
            type="button" 
            onClick={handleAcceptSelected}
            disabled={callActive || !recordingConsent}
            className="flex-1 py-2 px-3 bg-blue-600/30 border border-blue-500/40 hover:bg-blue-600/50 text-blue-300 rounded-lg text-xs font-semibold transition-all hover-lift disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Accept & Continue
          </button>
        </div>
      </div>

      {isChatMode ? (
        <div className="flex flex-col h-[500px] bg-gray-950/70 border border-gray-800 rounded-xl overflow-hidden mt-2">
          <div className="bg-blue-900/40 p-3 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span className="font-semibold text-gray-200 text-sm">Secure SOS Text Channel</span>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.map(msg => (
              <div key={msg.id} className={`flex ${msg.sender === 'victim' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${msg.sender === 'victim' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-gray-800 text-gray-200 rounded-bl-sm border border-gray-700'}`}>
                  <p>{msg.text}</p>
                  <span className={`text-[10px] mt-1 block ${msg.sender === 'victim' ? 'text-blue-200' : 'text-gray-500'}`}>{msg.timestamp}</span>
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
              placeholder="Type your message..."
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
        <>
          <div className="bg-gray-950/70 border border-gray-800 rounded-xl p-4 flex flex-col items-center justify-center gap-3 min-h-[110px]">
            <div className="text-3xl font-mono font-bold text-gray-200 tracking-wider">
              {formatTimer(seconds)}
            </div>

            {callActive ? (
              <div className="flex items-center justify-center gap-1.5 h-8 w-full">
                {[40, 70, 30, 90, 60, 85, 45, 95, 30, 75, 50, 80].map((heightPercent, idx) => (
                  <span
                    key={idx}
                    className="wave-bar bg-gradient-to-t from-blue-500 to-cyan-400 w-1.5 rounded-full"
                    style={{ height: `${heightPercent}%` }}
                  ></span>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-500 flex items-center gap-1">
                <Volume2 className="w-3.5 h-3.5 opacity-40" /> Audio stream inactive
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3">
            {!callActive ? (
              <div className="flex gap-2">
                <button
                  onClick={handleStartCall}
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition transform active:scale-95"
                >
                  <Phone className="w-5 h-5 fill-current" /> Receive call
                </button>
                <button
                  onClick={() => onLiveVoiceTrigger?.(language)}
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/30 transition transform active:scale-95"
                >
                  <Volume2 className="w-5 h-5" /> Live Voice Demo
                </button>
              </div>
            ) : (
              <button
                onClick={handleEndCall}
                className="w-full py-3 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30 transition transform active:scale-95"
              >
                <Phone className="w-5 h-5 fill-current rotate-[135deg]" /> End {isLiveVoiceActive ? "Live Voice" : "Call"}
              </button>
            )}
          </div>
        </>
      )}

      {onSilentSOSTrigger && !isChatMode && (
        <div className="pt-2 border-t border-gray-800/80">
          <button
            onClick={onSilentSOSTrigger}
            className="w-full py-2.5 bg-red-950/80 border border-red-600/50 hover:bg-red-900/80 active:scale-95 text-red-300 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all"
          >
            <AlertTriangle className="w-4 h-4 text-red-400" />
            Simulate Silent SOS Keypad Duress (9631)
          </button>
          {!callActive && (
            <p className="text-[10px] text-gray-600 text-center mt-1.5">
              (Trigger SOS before or after receiving a call)
            </p>
          )}
        </div>
      )}
    </div>
  );
};
