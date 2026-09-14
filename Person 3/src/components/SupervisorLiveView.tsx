import React from 'react';

interface SupervisorLiveViewProps {
  originalText: string;
  supervisorGloss?: string;
}

export const SupervisorLiveView: React.FC<SupervisorLiveViewProps> = ({ originalText, supervisorGloss }) => {
  return (
    <div className="supervisor-live-view p-5 rounded-2xl bg-gray-900/60 border border-gray-800/60 flex flex-col gap-3">
      <div className="flex items-center justify-between border-b border-gray-800 pb-2">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
          Original Spoken Transcript
        </h3>
      </div>
      <div className="original-transcript text-base text-gray-100 leading-relaxed min-h-[3rem]">
        {originalText || <span className="text-gray-500 italic text-sm">Waiting for incoming caller speech stream...</span>}
      </div>
      
      {supervisorGloss && (
        <div className="supervisor-gloss-section mt-4 pt-3 border-t border-gray-800/80">
          <div className="text-[10px] uppercase tracking-wide text-amber-500/70 mb-1.5 font-semibold">
            Approximate translation for reference only -- not used for scoring
          </div>
          <div className="supervisor-gloss text-sm text-gray-500 italic bg-gray-950/40 p-3 rounded-lg border border-gray-800/40">
            {supervisorGloss}
          </div>
        </div>
      )}
    </div>
  );
};
