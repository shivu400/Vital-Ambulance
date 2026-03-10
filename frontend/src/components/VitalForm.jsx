import { predict } from '../api/client'
import { Zap, Loader2 } from 'lucide-react'

function VitalForm({ onSubmit, loading, apiHealth, currentVitals, setCurrentVitals }) {
  const handleChange = (e) => {
    const { name, value } = e.target
    if (name === 'timestamp') {
      const dt = new Date(value)
      setCurrentVitals(prev => ({ ...prev, timestamp: isNaN(dt) ? value : dt.toISOString() }))
    } else if (name === 'temp') {
      setCurrentVitals(prev => ({ ...prev, [name]: parseFloat(value) }))
    } else {
      setCurrentVitals(prev => ({ ...prev, [name]: parseInt(value, 10) }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (apiHealth !== 'healthy') return

    try {
      const result = await predict(currentVitals)
      onSubmit(result)
    } catch (err) {
      console.error('Diagnostic error:', err)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 lg:p-8 space-y-8">
      <div className="space-y-6">
        {/* Time Configuration */}
        <div>
          <label className="block text-[10px] uppercase tracking-widest text-slate-500 mb-2 font-bold">
            Data Acquisition Timestamp
          </label>
          <input
            type="datetime-local"
            name="timestamp"
            value={currentVitals.timestamp.slice(0, 16)}
            onChange={handleChange}
            className="input-field font-mono text-sm"
          />
        </div>

        {/* Primary Critical Vitals (Sliders) */}
        <div className="space-y-6 bg-slate-900/40 p-5 rounded-2xl border border-slate-800/50">
          <div className="group">
            <div className="flex justify-between items-end mb-3">
              <label className="text-[10px] uppercase tracking-widest text-slate-400 font-bold group-hover:text-blue-400 transition-colors">
                Heart Rate (BPM)
              </label>
              <span className="text-2xl font-bold text-white tabular-nums drop-shadow-[0_0_8px_rgba(59,130,246,0.3)]">
                {currentVitals.hr}
              </span>
            </div>
            <input
              type="range"
              name="hr"
              min="40"
              max="180"
              value={currentVitals.hr}
              onChange={handleChange}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
          </div>

          <div className="group">
            <div className="flex justify-between items-end mb-3">
              <label className="text-[10px] uppercase tracking-widest text-slate-400 font-bold group-hover:text-cyan-400 transition-colors">
                Oxygen Saturation (SpO₂)
              </label>
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold tabular-nums drop-shadow-[0_0_8px_rgba(6,182,212,0.3)] ${currentVitals.spo2 < 92 ? 'text-rose-400' : 'text-white'
                  }`}>
                  {currentVitals.spo2}%
                </span>
              </div>
            </div>
            <input
              type="range"
              name="spo2"
              min="70"
              max="100"
              value={currentVitals.spo2}
              onChange={handleChange}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
          </div>
        </div>

        {/* Secondary Parameters (Grid) */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              SBP (mmHg)
            </label>
            <input
              type="number"
              name="sbp"
              value={currentVitals.sbp}
              onChange={handleChange}
              className="input-field text-center py-2"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              DBP (mmHg)
            </label>
            <input
              type="number"
              name="dbp"
              value={currentVitals.dbp}
              onChange={handleChange}
              className="input-field text-center py-2"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              RR (br/min)
            </label>
            <input
              type="number"
              name="rr"
              value={currentVitals.rr}
              onChange={handleChange}
              className="input-field text-center py-2"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              Temp (°C)
            </label>
            <input
              type="number"
              name="temp"
              step="0.1"
              value={currentVitals.temp}
              onChange={handleChange}
              className="input-field text-center py-2"
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || apiHealth !== 'healthy'}
        className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed group h-14 cursor-pointer"
      >
        <div className="flex items-center justify-center gap-3">
          {loading ? (
            <>
              <Loader2 className="animate-spin text-white/50" size={20} />
              <span className="tracking-widest uppercase text-sm font-black text-white/90">Synthesizing...</span>
            </>
          ) : (
            <>
              <Zap className="group-hover:scale-125 transition-transform duration-300 text-blue-300" size={20} />
              <span className="tracking-widest uppercase text-sm font-black text-white">Execute Analysis</span>
            </>
          )}
        </div>
      </button>

      <p className="text-[9px] text-center text-slate-600 uppercase tracking-[0.2em]">
        Signal integrity verified via secure gateway
      </p>
    </form>
  )
}

export default VitalForm
