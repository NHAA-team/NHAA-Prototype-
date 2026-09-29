import React, { useState } from 'react';
import { BarChart3, Users, ShieldAlert, CheckSquare, AlertCircle } from 'lucide-react';

interface MockAdminData {
  totalCases: number;
  riskBucketDistribution: { bucket: string; count: number }[];
  languageDistribution: { language: string; count: number }[];
  referralVolume: { type: string; count: number }[];
  reviewQueue: { id: string; bucket: string; reviewed: boolean }[];
}

const DEFAULT_MOCK_ADMIN: MockAdminData = {
  totalCases: 142,
  riskBucketDistribution: [
    { bucket: 'Low', count: 65 },
    { bucket: 'Moderate', count: 48 },
    { bucket: 'High', count: 24 },
    { bucket: 'Critical', count: 4 } // < 5 test for insufficient data privacy rule
  ],
  languageDistribution: [
    { language: 'Hindi', count: 88 },
    { language: 'Hinglish', count: 41 },
    { language: 'English', count: 11 }
  ],
  referralVolume: [
    { type: 'Counseling', count: 52 },
    { type: 'Legal Aid', count: 34 },
    { type: 'Police', count: 3 }, // < 5 test for insufficient data
    { type: 'Medical', count: 18 }
  ],
  reviewQueue: [
    { id: 'CASE-2026-881', bucket: 'Critical', reviewed: false },
    { id: 'CASE-2026-884', bucket: 'High', reviewed: false },
    { id: 'CASE-2026-889', bucket: 'Critical', reviewed: false },
    { id: 'CASE-2026-892', bucket: 'Critical', reviewed: true }
  ]
};

export const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<MockAdminData>(DEFAULT_MOCK_ADMIN);

  // Privacy Rule requirement from Solution PDF:
  // "if any single displayed count represents fewer than 5 cases, render the text 'insufficient data' in that spot"
  const renderCount = (count: number) => {
    if (count < 5) {
      return (
        <span className="text-amber-400 font-sans italic text-xs px-2 py-0.5 bg-amber-950/60 border border-amber-500/30 rounded">
          insufficient data
        </span>
      );
    }
    return <span className="font-mono font-bold">{count}</span>;
  };

  const handleMarkReviewed = (caseId: string) => {
    setData(prev => ({
      ...prev,
      reviewQueue: prev.reviewQueue.map(item =>
        item.id === caseId ? { ...item, reviewed: true } : item
      )
    }));
  };

  const maxRiskCount = Math.max(...data.riskBucketDistribution.map(r => r.count));

  return (
    <div className="flex flex-col gap-6 w-full max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-blue-400 font-semibold">Phase 4 Admin Analytics</span>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2">
            Administrator Dashboard & Compliance Queue
          </h2>
        </div>
        <div className="flex items-center gap-2 bg-blue-950/40 border border-blue-500/30 px-3 py-1.5 rounded-lg text-xs text-blue-300">
          <AlertCircle className="w-4 h-4 text-blue-400" />
          <span>K-Anonymity & Privacy Protection Active (&lt;5 anonymized)</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in-up">
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between hover-lift">
          <span className="text-xs font-semibold text-gray-400 uppercase">Total Case Count</span>
          <div className="text-3xl font-extrabold font-mono text-white mt-2">
            {renderCount(data.totalCases)}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between hover-lift stagger-1">
          <span className="text-xs font-semibold text-gray-400 uppercase">Critical Flagged</span>
          <div className="text-3xl font-extrabold font-mono text-red-400 mt-2">
            {renderCount(4)}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between hover-lift stagger-2">
          <span className="text-xs font-semibold text-gray-400 uppercase">Supervisor Queue</span>
          <div className="text-3xl font-extrabold font-mono text-amber-400 mt-2">
            {renderCount(data.reviewQueue.filter(q => !q.reviewed).length)}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between hover-lift stagger-3">
          <span className="text-xs font-semibold text-gray-400 uppercase">Active Languages</span>
          <div className="text-3xl font-extrabold font-mono text-emerald-400 mt-2">
            3 <span className="text-xs font-sans font-normal text-gray-400">(HI/EN/HING)</span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bar Chart of Risk-Bucket Distribution */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" /> Risk-Bucket Distribution
          </h3>

          <div className="flex flex-col gap-3 pt-2">
            {data.riskBucketDistribution.map(({ bucket, count }) => (
              <div key={bucket} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-gray-300">{bucket} Risk</span>
                  <span className="text-gray-400">{renderCount(count)}</span>
                </div>
                <div className="w-full bg-gray-950 rounded-full h-3 overflow-hidden border border-gray-800">
                  <div
                    className={`h-full rounded-full ${
                      bucket === 'Critical' ? 'bg-red-500' :
                      bucket === 'High' ? 'bg-orange-500' :
                      bucket === 'Moderate' ? 'bg-yellow-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: count >= 5 ? `${(count / maxRiskCount) * 100}%` : '8%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bar Chart of Language Distribution */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-400" /> Language Distribution
          </h3>

          <div className="flex flex-col gap-3 pt-2">
            {data.languageDistribution.map(({ language, count }) => (
              <div key={language} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-gray-300">{language}</span>
                  <span className="text-gray-400">{renderCount(count)}</span>
                </div>
                <div className="w-full bg-gray-950 rounded-full h-3 overflow-hidden border border-gray-800">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: count >= 5 ? `${(count / 100) * 100}%` : '8%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Supervisor Review Queue Panel */}
      <div className="glass-panel p-5 rounded-2xl flex flex-col gap-4">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" /> Supervisor Review Queue Table
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 font-semibold uppercase">
                <th className="p-3">Case ID</th>
                <th className="p-3">Risk Bucket</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {data.reviewQueue.map((item) => (
                <tr key={item.id} className="hover:bg-gray-900/40">
                  <td className="p-3 font-mono font-semibold text-gray-200">{item.id}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      item.bucket === 'Critical' ? 'bg-red-950 text-red-400 border border-red-500/40' : 'bg-orange-950 text-orange-400 border border-orange-500/40'
                    }`}>
                      {item.bucket}
                    </span>
                  </td>
                  <td className="p-3 text-gray-300">
                    {item.reviewed ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <CheckSquare className="w-3.5 h-3.5" /> Reviewed
                      </span>
                    ) : (
                      <span className="text-amber-400 font-medium">Pending Sign-off</span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    {!item.reviewed ? (
                      <button
                        onClick={() => handleMarkReviewed(item.id)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold transition"
                      >
                        Mark reviewed
                      </button>
                    ) : (
                      <span className="text-gray-500 text-[11px]">Completed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
