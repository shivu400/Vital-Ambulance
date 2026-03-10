import { useState, useEffect } from 'react'
import { Activity, ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react'
import VitalForm from './components/VitalForm'
import ResultsDisplay from './components/ResultsDisplay'
import VitalsMonitor from './components/VitalsMonitor'
import { healthCheck } from './api/client'
import './App.css'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')
  const [lastUpdated, setLastUpdated] = useState(null)

  // State lifted to App so both Form and Monitor can use it
  const [currentVitals, setCurrentVitals] = useState({
    timestamp: new Date().toISOString(),
    hr: 75,
    spo2: 98,
    sbp: 120,
    dbp: 80,
    rr: 16,
    temp: 36.8,
  })

  useEffect(() => {
    checkApiHealth()
    const timer = setInterval(checkApiHealth, 10000)
    return () => clearInterval(timer)
  }, [])

  const checkApiHealth = async () => {
    try {
      await healthCheck()
      setApiStatus('healthy')
    } catch (err) {
      setApiStatus('unhealthy')
      setError('System Backend Disconnected. Reconnecting...')
    }
  }

  const handlePredict = async (result) => {
    setLoading(true)
    setError(null)
    try {
      setResults(result)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis sequence failed')
    } finally {
      setTimeout(() => setLoading(false), 800) // Aesthetic delay
    }
  }

  return (
    <div className="min-h-screen mesh-gradient text-slate-200">
      {/* Background decoration elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full"></div>
      </div>

      <header className="relative z-10 border-b border-slate-800 bg-slate-950/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-tr from-blue-600 to-cyan-400 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.5)] border border-blue-400/30 text-white">
              <Activity size={24} strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                Gray Mobility
              </h1>
              <p className="text-sm text-slate-500 font-medium tracking-wide uppercase">
                Smart Ambulance Intelligence • v0.1.0
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">System Status</span>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/50 border border-slate-800">
                <div className={`h-2 w-2 rounded-full animate-pulse ${apiStatus === 'healthy' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                  }`}></div>
                <span className={`text-xs font-semibold ${apiStatus === 'healthy' ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                  {apiStatus === 'healthy' ? 'CORE STABLE' : 'RECONNECTING'}
                </span>
              </div>
            </div>
            {lastUpdated && (
              <div className="h-10 w-px bg-slate-800 hidden md:block"></div>
            )}
            {lastUpdated && (
              <div className="hidden md:flex flex-col items-end">
                <span className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Last Analysis</span>
                <span className="text-xs font-mono text-slate-300">{lastUpdated}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-10">
        {error && (
          <div className="mb-8 p-4 glass-card border-red-500/20 bg-red-500/5 text-red-400 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4">
            <AlertTriangle className="text-red-500" size={20} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <div className="mb-8">
          <VitalsMonitor currentVitals={currentVitals} />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
          <div className="xl:col-span-4 space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-4 w-1 bg-blue-500 rounded-full"></div>
              <h2 className="text-lg font-semibold text-white tracking-tight">Vitals Telemetry</h2>
            </div>
            <VitalForm
              onSubmit={handlePredict}
              loading={loading}
              apiHealth={apiStatus}
              currentVitals={currentVitals}
              setCurrentVitals={setCurrentVitals}
            />
          </div>

          <div className="xl:col-span-8 space-y-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="h-4 w-1 bg-cyan-500 rounded-full"></div>
                <h2 className="text-lg font-semibold text-white tracking-tight">Intelligence Dashboard</h2>
              </div>
            </div>

            {results ? (
              <div className="animate-in fade-in zoom-in-95 duration-500">
                <ResultsDisplay results={results} loading={loading} />
              </div>
            ) : (
              <div className="glass-card rounded-2xl p-16 flex flex-col items-center justify-center text-center group border-dashed">
                <div className="w-20 h-20 bg-slate-900 rounded-full flex items-center justify-center mb-6 border border-slate-800 relative">
                  <div className="absolute inset-0 bg-blue-500/5 rounded-full blur-xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
                  <Activity size={32} className="relative z-10 opacity-50 group-hover:text-blue-500 group-hover:opacity-100 transition-colors" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Diagnostic Engine Ready</h3>
                <p className="max-w-xs text-slate-500 leading-relaxed">
                  Modify sensor data in the telemetry unit to generate clinical risk assessments.
                </p>
                <div className="mt-8 flex gap-4">
                  <div className="px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-[10px] uppercase tracking-widest text-slate-500">
                    Isolation Forest
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-[10px] uppercase tracking-widest text-slate-500">
                    OC-SVM
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-[10px] uppercase tracking-widest text-slate-500">
                    MEWS Logic
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="relative z-10 border-t border-slate-800 py-10 mt-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-sm text-slate-600">
            &copy; 2026 Gray Mobility Intelligence Systems. All rights reserved.
          </p>
          <div className="flex gap-8">
            <a href="#" className="text-[10px] uppercase tracking-widest text-slate-500 hover:text-blue-400 transition-colors">Documentation</a>
            <a href="#" className="text-[10px] uppercase tracking-widest text-slate-500 hover:text-blue-400 transition-colors">Safety Protocols</a>
            <a href="#" className="text-[10px] uppercase tracking-widest text-slate-500 hover:text-blue-400 transition-colors">System Logs</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
