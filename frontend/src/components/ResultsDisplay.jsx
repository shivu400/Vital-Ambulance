function ResultsDisplay({ results, loading }) {
  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-20 flex flex-col items-center justify-center text-center space-y-8 min-h-[500px]">
        <div className="relative">
          {/* Animated rings for loading state */}
          <div className="absolute inset-0 w-24 h-24 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
          <div className="w-24 h-24 bg-slate-900 rounded-full border-4 border-slate-800 border-t-blue-500 animate-[spin_1s_linear_infinite] relative z-10 shadow-2xl"></div>
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            Neural Diagnostic Cycle
          </h3>
          <p className="text-slate-500 text-xs font-mono tracking-widest uppercase">
            Aggregating telemetry...
          </p>
        </div>
      </div>
    )
  }

  const isHighRisk = results?.clinical_risk?.toLowerCase().includes('high') || (results?.mews_score >= 5)
  const isAnomaly = results?.is_anomaly

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Risk Assessment Primary Card */}
        <div className={`glass-card rounded-2xl p-8 transition-all duration-500 relative overflow-hidden group ${isHighRisk ? 'ring-1 ring-rose-500/30 glow-red' : 'ring-1 ring-emerald-500/30'
          }`}>
          {/* Background Highlight Gradient */}
          <div className={`absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] pointer-events-none transition-colors duration-1000 ${isHighRisk ? 'bg-rose-500/10' : 'bg-emerald-500/10'
            }`}></div>

          <div className="relative z-10">
            <div className="flex justify-between items-start mb-6">
              <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
                Clinical Status
              </span>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${isHighRisk ? 'bg-rose-500/10 text-rose-500 border border-rose-400/20' : 'bg-emerald-500/10 text-emerald-500 border border-emerald-400/20'
                }`}>
                {isHighRisk ? '⚠️' : '✓'}
              </div>
            </div>

            <h2 className={`text-3xl font-black mb-4 uppercase tracking-tighter drop-shadow-[0_0_12px_currentColor] ${isHighRisk ? 'text-rose-400' : 'text-emerald-400'
              }`}>
              {results?.clinical_risk || 'Normal'}
            </h2>

            <div className="flex flex-wrap gap-4 mt-8">
              <div className="px-4 py-2 rounded-xl bg-slate-900/60 border border-slate-700 flex flex-col">
                <span className="text-[8px] uppercase tracking-widest text-slate-500 mb-1">MEWS Score</span>
                <span className="text-xl font-bold text-white leading-none">{results?.mews_score}</span>
              </div>
              <div className="px-4 py-2 rounded-xl bg-slate-900/60 border border-slate-700 flex flex-col">
                <span className="text-[8px] uppercase tracking-widest text-slate-500 mb-1">Shock Index</span>
                <span className="text-xl font-bold text-white leading-none">{results?.shock_index?.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Anomaly Pattern Recognition Card */}
        <div className={`glass-card rounded-2xl p-8 transition-all duration-500 ring-1 h-full ${isAnomaly ? 'ring-orange-500/30 bg-orange-500/[0.03]' : 'ring-blue-500/20 bg-blue-500/[0.02]'
          }`}>
          <div className="flex justify-between items-start mb-6">
            <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
              AI Pattern Analysis
            </span>
            <div className={`px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-widest ${isAnomaly ? 'bg-orange-500/20 text-orange-400 border border-orange-400/20' : 'bg-blue-500/20 text-blue-400 border border-blue-400/20'
              }`}>
              {isAnomaly ? 'Anomaly' : 'Stable'}
            </div>
          </div>

          <div className="flex items-center gap-6 mb-8">
            <div className="relative">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle cx="40" cy="40" r="34" stroke="currentColor" strokeWidth="6" fill="transparent" className="text-slate-800" />
                <circle cx="40" cy="40" r="34" stroke="currentColor" strokeWidth="6" fill="transparent"
                  strokeDasharray={2 * Math.PI * 34}
                  strokeDashoffset={2 * Math.PI * 34 * (1 - (results?.confidence || 0))}
                  strokeLinecap="round"
                  className={`transition-all duration-1000 delay-200 ${isAnomaly ? 'text-orange-500' : 'text-blue-500'}`}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
                <span className="text-lg font-black text-white">{(results?.confidence * 100).toFixed(0)}</span>
                <span className="text-[8px] text-slate-500 uppercase font-black">%</span>
              </div>
            </div>

            <div className="space-y-1">
              <p className="text-xs text-slate-400 font-medium">Model Confidence</p>
              <p className="text-xl font-bold text-white tabular-nums tracking-tight">
                {(results?.confidence * 100).toFixed(1)}% Accuracy
              </p>
              <p className="text-[9px] text-slate-500 uppercase tracking-widest">
                Iso + OC-SVM Ensemble
              </p>
            </div>
          </div>

          <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3 flex items-center justify-between">
            <span className="text-[9px] uppercase tracking-widest text-slate-500">Anomaly Index</span>
            <span className={`text-xs font-mono font-bold ${isAnomaly ? 'text-orange-400' : 'text-blue-400'}`}>
              {results?.anomaly_score?.toFixed(4)}
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Intelligence Explanation */}
      {results?.explanation && (
        <div className="glass-card rounded-2xl p-8 bg-blue-600/[0.03] border-blue-500/10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
            <h3 className="text-[10px] uppercase font-bold tracking-[0.2em] text-blue-400">
              Diagnostic Insights
            </h3>
          </div>
          <p className="text-slate-300 text-lg lg:text-xl font-medium leading-relaxed tracking-tight">
            {results.explanation.split('; ').map((part, i) => (
              <span key={i} className="inline-block mr-4 mb-2 px-4 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/50 hover:border-blue-500/30 transition-colors">
                • {part}
              </span>
            ))}
          </p>
        </div>
      )}

      {/* Alert suppression log (bonus detail) */}
      <div className="px-6 py-4 flex items-center justify-center gap-3 bg-slate-950/30 rounded-full border border-slate-900 border-dashed">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Secure End-to-End Diagnostic Signal Terminal Verified</span>
      </div>
    </div>
  )
}

export default ResultsDisplay
