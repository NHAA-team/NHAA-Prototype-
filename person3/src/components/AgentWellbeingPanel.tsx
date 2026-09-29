import React, { useState, useEffect } from 'react';
import { HeartPulse, Activity, Coffee, Brain, Clock, ShieldCheck } from 'lucide-react';

export const AgentWellbeingPanel: React.FC = () => {
  const [wellbeingScore, setWellbeingScore] = useState(78);
  const [stressLevel, setStressLevel] = useState('Moderate');
  const [sessionTime, setSessionTime] = useState('02:14:35');
  
  // Simulate slow degradation over time (for demo purposes)
  useEffect(() => {
    const interval = setInterval(() => {
      setWellbeingScore(prev => {
        const next = Math.max(40, prev - 1);
        if (next < 60) setStressLevel('High');
        else if (next < 80) setStressLevel('Moderate');
        else setStressLevel('Optimal');
        return next;
      });
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto animate-fade-in-up">
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-purple-400 font-semibold">Phase 4 Supervisor Metrics</span>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <HeartPulse className="w-6 h-6 text-purple-400" /> Agent Secondary-Trauma Shield
          </h2>
        </div>
        <div className="text-xs text-gray-400 font-mono flex items-center gap-2 bg-purple-950/40 border border-purple-500/30 px-3 py-1.5 rounded-lg">
          <ShieldCheck className="w-4 h-4 text-purple-400" /> Supervisor Only Access
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Score Card */}
        <div className="glass-panel p-6 rounded-2xl border border-purple-500/30 flex flex-col justify-between hover-lift shadow-[0_0_15px_rgba(168,85,247,0.1)]">
          <div>
            <div className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center justify-between">
              <span>Real-time Wellbeing Signal</span>
              <Activity className="w-4 h-4 text-purple-400 animate-pulse" />
            </div>
            
            <div className="text-6xl font-extrabold font-mono mt-4 flex items-baseline gap-2">
              <span className={wellbeingScore < 60 ? 'text-red-400' : 'text-purple-300'}>{wellbeingScore}%</span>
            </div>
            
            <div className="mt-4 w-full bg-gray-950 rounded-full h-3 overflow-hidden border border-gray-800">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${
                  wellbeingScore < 60 ? 'bg-gradient-to-r from-red-500 to-orange-400' : 'bg-gradient-to-r from-purple-500 to-indigo-400'
                }`}
                style={{ width: `${wellbeingScore}%` }}
              />
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-gray-800">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Current Status:</span>
              <span className={`font-bold px-2 py-1 rounded ${
                wellbeingScore < 60 ? 'bg-red-950/60 text-red-400 border border-red-500/30' : 
                'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
              }`}>{stressLevel}</span>
            </div>
          </div>
        </div>

        {/* Breakdown Metrics */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="glass-panel p-5 rounded-2xl border border-gray-800 hover-lift stagger-1 scroll-reveal">
            <div className="flex items-center gap-3 text-blue-400 mb-3">
              <Brain className="w-5 h-5" />
              <h4 className="text-sm font-bold uppercase tracking-wide text-gray-200">Cognitive Load</h4>
            </div>
            <div className="text-2xl font-mono font-bold text-gray-100 mb-2">High</div>
            <p className="text-xs text-gray-400">Agent is processing complex, multi-lingual distress signals with high SVI variance.</p>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-gray-800 hover-lift stagger-2 scroll-reveal">
            <div className="flex items-center gap-3 text-amber-400 mb-3">
              <Clock className="w-5 h-5" />
              <h4 className="text-sm font-bold uppercase tracking-wide text-gray-200">Active Shift Duration</h4>
            </div>
            <div className="text-2xl font-mono font-bold text-gray-100 mb-2">{sessionTime}</div>
            <p className="text-xs text-gray-400">Continuous exposure time without a mandatory debriefing rotation.</p>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-gray-800 sm:col-span-2 hover-lift stagger-3 scroll-reveal">
             <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center gap-2 mb-2">
                    <Coffee className="w-4 h-4 text-emerald-400" /> Recommendation Engine
                  </h4>
                  <p className="text-xs text-gray-400 max-w-lg leading-relaxed mb-4">
                    The Wellbeing system monitors cumulative distress exposure. If the wellbeing score drops below 60%, the system will automatically block new high-risk assignments and recommend a 15-minute rotation break.
                  </p>
                </div>
                {wellbeingScore < 60 ? (
                  <button className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-lg shadow-red-500/30 animate-pulse">
                    Force Rotation Break
                  </button>
                ) : (
                  <button className="bg-gray-800 text-gray-400 px-4 py-2 rounded-lg text-xs font-semibold cursor-not-allowed border border-gray-700">
                    Rotation Not Required
                  </button>
                )}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
