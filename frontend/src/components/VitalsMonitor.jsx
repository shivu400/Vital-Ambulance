import { useState, useEffect } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import { Activity, Heart, Wind, Thermometer } from 'lucide-react';

// Generates smooth random walk data for sparklines
const generateSparkline = (baseValue, variance, count = 20) => {
    let val = baseValue;
    return Array.from({ length: count }, (_, i) => {
        val = val + (Math.random() - 0.5) * variance;
        return { time: i, value: val };
    });
};

const MetricMonitor = ({ icon: Icon, label, value, unit, color, data, range }) => {
    return (
        <div className={`glass-card rounded-2xl p-5 relative overflow-hidden group border border-${color}-500/20`}>
            <div className={`absolute -right-10 -top-10 w-32 h-32 bg-${color}-500/5 rounded-full blur-2xl group-hover:bg-${color}-500/10 transition-colors duration-500`}></div>

            <div className="flex justify-between items-start mb-2 relative z-10">
                <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg bg-${color}-500/10 text-${color}-400`}>
                        <Icon size={18} strokeWidth={2.5} />
                    </div>
                    <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">
                        {label}
                    </span>
                </div>
            </div>

            <div className="flex items-end justify-between relative z-10 mt-4">
                <div className="flex items-baseline gap-1.5">
                    <span className={`text-4xl font-black tabular-nums tracking-tighter text-${color}-400 drop-shadow-[0_0_12px_rgba(var(--${color}-rgb),0.3)]`}>
                        {value}
                    </span>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{unit}</span>
                </div>

                <div className="h-12 w-24">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <YAxis domain={range} hide />
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke={`currentColor`}
                                strokeWidth={3}
                                dot={false}
                                activeDot={{ r: 4, fill: `currentColor`, strokeWidth: 0 }}
                                isAnimationActive={false}
                                className={`text-${color}-500 opacity-90 drop-shadow-[0_0_8px_rgba(var(--${color}-rgb),0.8)]`}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default function VitalsMonitor({ currentVitals }) {
    // We keep local state for the sparklines so they can animate independently of form submissions
    const [sparklines, setSparklines] = useState({
        hr: generateSparkline(currentVitals.hr, 4),
        spo2: generateSparkline(currentVitals.spo2, 1),
        sbp: generateSparkline(currentVitals.sbp, 3),
        rr: generateSparkline(currentVitals.rr, 1),
    });

    // Whenever the input vitals change drastically, reset the base of the sparklines
    // Otherwise, just tick them forward simulating a live monitor
    useEffect(() => {
        const tick = setInterval(() => {
            setSparklines(prev => ({
                hr: [...prev.hr.slice(1), { time: Date.now(), value: currentVitals.hr + (Math.random() - 0.5) * 5 }],
                spo2: [...prev.spo2.slice(1), { time: Date.now(), value: Math.min(100, currentVitals.spo2 + (Math.random() - 0.5) * 1) }],
                sbp: [...prev.sbp.slice(1), { time: Date.now(), value: currentVitals.sbp + (Math.random() - 0.5) * 4 }],
                rr: [...prev.rr.slice(1), { time: Date.now(), value: currentVitals.rr + (Math.random() - 0.5) * 1 }],
            }));
        }, 1000);

        return () => clearInterval(tick);
    }, [currentVitals]);


    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
            <MetricMonitor
                icon={Heart}
                label="Heart Rate"
                value={currentVitals.hr}
                unit="BPM"
                color="rose"
                data={sparklines.hr}
                range={['dataMin - 10', 'dataMax + 10']}
            />

            <MetricMonitor
                icon={Activity}
                label="Oxygen Sat."
                value={currentVitals.spo2}
                unit="SpO₂ %"
                color="cyan"
                data={sparklines.spo2}
                range={[80, 100]}
            />

            <MetricMonitor
                icon={Activity}
                label="Blood Press."
                value={`${currentVitals.sbp}/${currentVitals.dbp}`}
                unit="mmHg"
                color="emerald"
                data={sparklines.sbp}
                range={['dataMin - 20', 'dataMax + 20']}
            />

            <MetricMonitor
                icon={Wind}
                label="Resp. Rate"
                value={currentVitals.rr}
                unit="Br/Min"
                color="blue"
                data={sparklines.rr}
                range={['dataMin - 5', 'dataMax + 5']}
            />
        </div>
    );
}
