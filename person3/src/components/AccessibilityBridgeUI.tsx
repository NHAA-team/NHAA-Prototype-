import React, { useState } from 'react';
import type { TranscriptUpdateEvent, ActionUpdateEvent } from '../types/contract';
import { Send, MessageSquareText, VolumeX } from 'lucide-react';
import { AgentConsole } from './AgentConsole';

interface AccessibilityBridgeProps {
  currentUpdate: TranscriptUpdateEvent | null;
  currentAction: ActionUpdateEvent | null;
  onAdjustConfidence?: (conf: number) => void;
  onAnalyzeText?: (text: string) => void;
}

export const AccessibilityBridgeUI: React.FC<AccessibilityBridgeProps> = ({
  currentUpdate,
  currentAction,
  onAdjustConfidence,
  onAnalyzeText
}) => {
  const [messages, setMessages] = useState<{ sender: 'caller' | 'agent'; text: string; time: string }[]>([
    { sender: 'caller', text: 'Namaste, I cannot talk right now due to safety reasons. Typing here...', time: '10:02 AM' },
    { sender: 'agent', text: 'Namaste, we hear you. You are in a safe channel. How can we assist?', time: '10:02 AM' }
  ]);
  const [inputText, setInputText] = useState('');
  const [activeRole, setActiveRole] = useState<'caller' | 'agent'>('caller');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setMessages(prev => [
      ...prev,
      { sender: activeRole, text: inputText, time: new Date().toLocaleTimeString() }
    ]);
    
    // Only analyze the victim's (caller's) messages, not the agent's
    if (activeRole === 'caller' && onAnalyzeText) {
      onAnalyzeText(inputText);
    }
    
    setInputText('');
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto">
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-blue-400 font-semibold">Phase 4 Non-Verbal Disclosure</span>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <MessageSquareText className="w-6 h-6 text-blue-400" /> Accessibility Bridge UI (Text Channel)
          </h2>
        </div>
        <div className="text-xs text-gray-400 font-mono">
          Reusing identical risk-panel & action-panel as voice agent console
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 glass-panel p-5 rounded-2xl flex flex-col h-[580px]">
          <div className="border-b border-gray-800 pb-3 mb-3 flex items-center justify-between">
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
              Caller Text Chat Interface
            </h3>
          </div>

          <div className="bg-amber-950/40 border border-amber-500/30 rounded-lg p-3 mb-4 flex items-start gap-3 animate-fade-in-up">
            <VolumeX className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[11px] font-bold text-amber-400 uppercase tracking-wide">
                Silent Mode Active
              </p>
              <p className="text-[11px] text-amber-200/80 mt-1">
                Caller indicated they are unable to speak freely. Communication shifted to non-verbal text channel to ensure safety.
              </p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex flex-col ${m.sender === 'caller' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] p-3 rounded-2xl ${
                    m.sender === 'caller'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-800 text-gray-200 rounded-bl-none'
                  }`}
                >
                  <p>{m.text}</p>
                </div>
                <span className="text-[10px] text-gray-500 mt-1 font-mono">{m.time}</span>
              </div>
            ))}
          </div>

          <form onSubmit={handleSend} className="mt-3 flex gap-2 pt-2 border-t border-gray-800">
            <select
              value={activeRole}
              onChange={(e) => setActiveRole(e.target.value as 'caller' | 'agent')}
              className="bg-gray-800 border border-gray-700 rounded-xl px-2 py-2 text-xs text-white focus:outline-none"
            >
              <option value="caller">As Caller</option>
              <option value="agent">As Agent</option>
            </select>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Type message as ${activeRole}...`}
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              className={`p-2 ${activeRole === 'caller' ? 'bg-blue-600 hover:bg-blue-500' : 'bg-indigo-600 hover:bg-indigo-500'} text-white rounded-xl transition`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        <div className="lg:col-span-8">
          <AgentConsole
            currentUpdate={currentUpdate}
            currentAction={currentAction}
            onAdjustConfidence={onAdjustConfidence}
          />
        </div>
      </div>
    </div>
  );
};
