import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, ScatterChart, Scatter,
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ComposedChart, Cell, Area, ReferenceLine
} from 'recharts';
import {
  Activity, Thermometer, Droplets,
  TrendingUp, BarChart3, ScatterChart as ScatterIcon, Layers,
  Filter, Star, Check, Zap, AlertTriangle, CalendarDays,
  Clock, Hash, BrainCircuit, Box, Share2, Binary, Database
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility for tailwind classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface DataRecord {
  date: string;
  LOAD: number;
  ACT_TEMP: number;
  ACT_HUMIDITY: number;
  ACT_RAIN: number;
  ACT_HEAT_INDEX: number;
  COOL_FACTOR: number;
  Event_Name: string;
  Holiday_Ind: number;
  LOAD_MA7: number;
  LOAD_MA30: number;
  LOAD_LAG1: number;
  LOAD_LAG7: number;
  CORR_TEMP: number;
  CORR_HUMIDITY: number;
  is_anomaly: number;
  month: number;
  weekday: number;
  season: string;
}

const SEASONS = ['Winter', 'Spring', 'Summer', 'Autumn/Monsoon'];
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const App: React.FC = () => {
  const [rawData, setRawData] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadStatus, setLoadStatus] = useState("Initializing System...");
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'ml_readiness' | 'lags' | 'correlation' | 'distribution' | 'trend'>('ml_readiness');
  const [isNormalized, setIsNormalized] = useState(false);
  const [showMA7, setShowMA7] = useState(false);
  const [showAnomalies, setShowAnomalies] = useState(true);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedSeasons, setSelectedSeasons] = useState<string[]>([]);
  const [selectedWeekdays, setSelectedWeekdays] = useState<number[]>([]);
  const [showHolidaysOnly, setShowHolidaysOnly] = useState(false);

  useEffect(() => {
    setLoadStatus("Fetching Neural Grid Data...");
    fetch('/data.json')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
        return res.json();
      })
      .then(json => {
        setLoadStatus("Processing Feature Patterns...");
        setRawData(json);
        if (json.length > 0) {
          setStartDate(json[0].date);
          setEndDate(json[json.length - 1].date);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Critical System Failure:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const statsCore = useMemo(() => {
    if (rawData.length === 0) return { mean: 0, std: 1 };
    const loadValues = rawData.map(d => d.LOAD);
    const mean = loadValues.reduce((a, b) => a + b, 0) / loadValues.length;
    const std = Math.sqrt(loadValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / loadValues.length);
    return { mean, std: std || 1 };
  }, [rawData]);

  const filteredData = useMemo(() => {
    const subset = rawData.filter(d => {
      const isWithinDate = (!startDate || d.date >= startDate) && (!endDate || d.date <= endDate);
      const isSeasonMatch = selectedSeasons.length === 0 || selectedSeasons.includes(d.season);
      const isWeekdayMatch = selectedWeekdays.length === 0 || selectedWeekdays.includes(d.weekday);
      const isHolidayMatch = !showHolidaysOnly || d.Holiday_Ind === 1;
      return isWithinDate && isSeasonMatch && isWeekdayMatch && isHolidayMatch;
    });

    if (!isNormalized || !statsCore) return subset;

    return subset.map(d => ({
      ...d,
      LOAD: (d.LOAD - statsCore.mean) / statsCore.std,
      LOAD_MA7: d.LOAD_MA7 ? (d.LOAD_MA7 - statsCore.mean) / statsCore.std : 0,
      LOAD_MA30: d.LOAD_MA30 ? (d.LOAD_MA30 - statsCore.mean) / statsCore.std : 0,
    }));
  }, [rawData, startDate, endDate, selectedSeasons, selectedWeekdays, showHolidaysOnly, isNormalized, statsCore]);

  const analytics = useMemo(() => {
    if (filteredData.length === 0) return null;
    const avgLoad = filteredData.reduce((acc, curr) => acc + curr.LOAD, 0) / filteredData.length;
    const rSquared = calculateRSquared(filteredData.map(d => d.ACT_TEMP), filteredData.map(d => d.LOAD));
    const autocorrelation = calculateCorrelation(filteredData.map(d => d.LOAD_LAG1 || 0), filteredData.map(d => d.LOAD));
    return { avgLoad, rSquared, autocorrelation };
  }, [filteredData]);

  const distributionData = useMemo(() => {
    if (filteredData.length === 0) return [];
    const bins = 20;
    const vals = filteredData.map(d => d.LOAD);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const step = (max - min) / bins;
    if (isNaN(step) || step === 0) return [];

    const hist = Array.from({ length: bins }, (_, i) => ({
      range: `${(min + i * step).toFixed(1)}`,
      count: 0
    }));

    filteredData.forEach(d => {
      const idx = Math.min(Math.floor((d.LOAD - min) / step), bins - 1);
      if (idx >= 0 && hist[idx]) hist[idx].count++;
    });
    return hist;
  }, [filteredData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020202] text-white">
        <div className="flex flex-col items-center gap-8">
          <div className="relative">
            <BrainCircuit className="text-cyan-500 animate-pulse" size={64} />
            <div className="absolute inset-0 bg-cyan-500/20 blur-3xl rounded-full" />
          </div>
          <div className="flex flex-col items-center gap-2">
            <h2 className="text-2xl font-black tracking-tighter uppercase italic">{loadStatus}</h2>
            <div className="w-64 h-1 bg-zinc-900 rounded-full overflow-hidden">
              <motion.div initial={{ x: '-100%' }} animate={{ x: '100%' }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }} className="w-full h-full bg-cyan-500" />
            </div>
            <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-[0.3em] mt-2">Neural Analytics Pipeline Active</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020202] text-white p-10">
        <div className="max-w-md w-full bg-zinc-900 border border-red-900/50 p-10 rounded-[3rem] text-center space-y-6">
          <AlertTriangle className="text-red-500 mx-auto" size={48} />
          <div className="space-y-2">
            <h2 className="text-xl font-black uppercase text-red-500">System Integration Error</h2>
            <p className="text-zinc-500 text-xs font-medium leading-relaxed">{error}. Please verify data.json integrity.</p>
          </div>
          <button onClick={() => window.location.reload()} className="px-6 py-3 bg-red-500 text-black text-xs font-black rounded-2xl hover:scale-105 transition-transform">
            Re-Initialize System
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020202] text-white p-4 lg:p-10 font-sans selection:bg-cyan-500/30">
      <header className="mb-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <BrainCircuit size={20} className="text-black" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tighter uppercase italic">NeuralGrid ML-Ready</h1>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest pl-1">Advanced Pattern Identification Module v5.0</p>
            </div>
          </div>
        </div>

        <div className="flex bg-zinc-900/50 p-1 rounded-2xl border border-zinc-800 backdrop-blur-md">
          {[
            { id: 'ml_readiness', icon: <Binary size={16} />, label: 'ML Audit' },
            { id: 'lags', icon: <Share2 size={16} />, label: 'Lags/AutoCorr' },
            { id: 'correlation', icon: <Zap size={16} />, label: 'Features' },
            { id: 'distribution', icon: <Hash size={16} />, label: 'Distro' },
            { id: 'trend', icon: <TrendingUp size={16} />, label: 'Trend' },
          ].map(m => (
            <button key={m.id} onClick={() => setViewMode(m.id as any)} className={cn("px-4 py-2.5 rounded-xl transition-all flex items-center gap-2 text-[10px] font-black uppercase", viewMode === m.id ? "bg-white text-black shadow-xl" : "text-zinc-500 hover:text-white hover:bg-white/5")}>
              {m.icon} <span className="hidden sm:inline">{m.label}</span>
            </button>
          ))}
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Feature Engineering Panel */}
        <aside className="lg:col-span-3 space-y-6">
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 shadow-2xl backdrop-blur-xl">
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 mb-8 flex items-center gap-2">
              <Database size={14} className="text-cyan-500" /> Feature Selection
            </h3>

            <div className="space-y-8">
              <div className="space-y-4">
                <label className="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Temporal Context</label>
                <div className="space-y-2">
                  <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-2.5 text-[10px] text-zinc-400 focus:border-cyan-500 outline-none" />
                  <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-2.5 text-[10px] text-zinc-400 focus:border-cyan-500 outline-none" />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Seasonal Dimension</label>
                <div className="grid grid-cols-2 gap-2">
                  {SEASONS.map(s => (
                    <button key={s} onClick={() => setSelectedSeasons(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])} className={cn("py-2 rounded-xl text-[9px] font-bold border transition-all", selectedSeasons.includes(s) ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-400" : "bg-black border-zinc-800 text-zinc-600 hover:border-zinc-700")}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Weekly Seasonality</label>
                <div className="flex gap-1 justify-between">
                  {WEEKDAYS.map((d, i) => (
                    <button key={d} onClick={() => setSelectedWeekdays(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i])} className={cn("w-full h-8 flex items-center justify-center rounded-lg text-[10px] font-black border transition-all", selectedWeekdays.includes(i) ? "bg-white border-white text-black" : "bg-black border-zinc-800 text-zinc-600")}>
                      {d[0]}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3 border-t border-zinc-800 pt-6">
                <label className="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Model Readiness Toggles</label>
                <div className="space-y-2">
                  <button onClick={() => setIsNormalized(!isNormalized)} className={cn("w-full flex items-center justify-between px-4 py-3 rounded-2xl text-[10px] font-black border transition-all", isNormalized ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.1)]" : "bg-zinc-800/20 border-zinc-800 text-zinc-500")}>
                    <span>Z-Score Normalized</span>
                    <div className={cn("w-2 h-2 rounded-full", isNormalized ? "bg-cyan-500 shadow-[0_0_8px_cyan]" : "bg-zinc-700")} />
                  </button>
                  <button onClick={() => setShowAnomalies(!showAnomalies)} className={cn("w-full flex items-center justify-between px-4 py-3 rounded-2xl text-[10px] font-black border transition-all", showAnomalies ? "bg-yellow-500/10 border-yellow-500/30 text-yellow-400" : "bg-zinc-800/20 border-zinc-800 text-zinc-500")}>
                    <span>Highlight Outliers</span>
                    <AlertTriangle size={12} className={showAnomalies ? "text-yellow-400" : "text-zinc-700"} />
                  </button>
                </div>
              </div>

              <button onClick={() => {
                setStartDate(rawData[0]?.date || '');
                setEndDate(rawData[rawData.length - 1]?.date || '');
                setSelectedSeasons([]);
                setSelectedWeekdays([]);
                setIsNormalized(false);
                setShowAnomalies(true);
              }} className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-2xl text-[10px] font-extrabold uppercase tracking-widest transition-all">
                Reset Engine
              </button>
            </div>
          </div>
        </aside>

        {/* Dynamic ML Canvas */}
        <section className="lg:col-span-9 space-y-8">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <MetricCard title="Model Strength (R²)" value={analytics?.rSquared.toFixed(3)} desc="Vs Temperature" color="cyan" />
            <MetricCard title="Auto-Corr (Lag1)" value={analytics?.autocorrelation.toFixed(3)} desc="Pattern persistence" color="purple" />
            <MetricCard title="Signal/Noise" value={(statsCore ? statsCore.mean / statsCore.std : 0).toFixed(2)} desc="Data volatility" color="orange" />
            <MetricCard title="Features/Day" value="12" desc="Active dimensions" color="zinc" />
          </div>

          <div className="bg-zinc-900/40 border border-zinc-800 rounded-[3rem] p-10 shadow-3xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none group-hover:scale-110 transition-transform duration-1000">
              <Binary size={240} />
            </div>

            <div className="flex flex-col mb-10">
              <span className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.4em] mb-2 leading-none">Neural Pattern Canvas</span>
              <h2 className="text-3xl font-extrabold tracking-tight">
                {viewMode === 'ml_readiness' && "Signal Component Analysis"}
                {viewMode === 'lags' && "Correlation Decay (Lagged Analysis)"}
                {viewMode === 'correlation' && "Multivariate Interaction Matrix"}
                {viewMode === 'distribution' && "Statistical Mass Distribution"}
                {viewMode === 'trend' && "Temporal Drift Reconstruction"}
              </h2>
            </div>

            <div className="w-full h-[550px]">
              <AnimatePresence mode="wait">
                <motion.div key={viewMode + isNormalized + filteredData.length} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.02 }} transition={{ duration: 0.5 }} className="w-full h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    {renderChart(viewMode, filteredData, isNormalized, showAnomalies, distributionData)}
                  </ResponsiveContainer>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          <div className="bg-zinc-900/20 border border-zinc-900 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-2 h-2 rounded-full bg-cyan-500" />
              <h4 className="text-xs font-black uppercase tracking-widest text-zinc-400 underline underline-offset-8 decoration-cyan-500/30">Expert ML Context</h4>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed font-medium">
              This view is optimized for **Feature Engineering**. By observing the **{viewMode}** view, we can confirm if the data follows a stationary process (required for some models like ARIMA) or if high-frequency non-linearity is present. The **R²** of {(analytics?.rSquared || 0).toFixed(3)} suggests that external factors capture {((analytics?.rSquared || 0) * 100).toFixed(1)}% of total variance. If **Lag-1 Auto-correlation** is {(analytics?.autocorrelation || 0) > 0.8 ? 'above 0.8' : 'relatively low'}, the model will benefit significantly from **Lags** as input features.
            </p>
          </div>
        </section>
      </main>

      <footer className="mt-20 py-10 border-t border-zinc-900 flex justify-between items-center text-[10px] font-black text-zinc-700 uppercase tracking-widest">
        <span>DALMIA ML OPS FRAMEWORK</span>
        <div className="flex gap-10">
          <span>Version 5.0.4-LTS</span>
          <span className="text-cyan-900 underline">Documentation</span>
        </div>
      </footer>
    </div>
  );
}

function renderChart(mode: string, data: any[], normalized: boolean, anomalies: boolean, distroData: any[]) {
  const common = { stroke: "#222", fontSize: 10, fontWeight: 700, tickMargin: 12 };

  switch (mode) {
    case 'ml_readiness':
      return (
        <LineChart data={data}>
          <CartesianGrid stroke="#111" vertical={false} />
          <XAxis dataKey="date" {...common} />
          <YAxis {...common} />
          <Tooltip content={<DTooltip />} />
          <Legend wrapperStyle={{ paddingTop: 40 }} />
          <Line type="monotone" dataKey="LOAD" stroke="#22d3ee" strokeWidth={3} dot={false} animationDuration={1200} name="Target (Load)" />
          {data.length < 500 && normalized && (
            <Area type="monotone" dataKey="LOAD" fill="#22d3ee" fillOpacity={0.05} stroke="none" />
          )}
          <Line type="monotone" dataKey="ACT_TEMP" stroke="#f97316" strokeWidth={1} dot={false} opacity={0.4} name="Factor_1 (Temp)" />
          <Line type="monotone" dataKey="ACT_HUMIDITY" stroke="#60a5fa" strokeWidth={1} dot={false} opacity={0.4} name="Factor_2 (Humid)" />
        </LineChart>
      );
    case 'lags':
      return (
        <ScatterChart>
          <CartesianGrid stroke="#111" />
          <XAxis type="number" dataKey="LOAD_LAG1" name="Yesterday" {...common} label={{ value: 'Previous Day Load', position: 'bottom', fill: '#444', fontSize: 10 }} />
          <YAxis type="number" dataKey="LOAD" name="Today" {...common} label={{ value: 'Current Day Load', angle: -90, position: 'left', fill: '#444', fontSize: 10 }} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={data} fill="#a855f7" opacity={0.4} fillOpacity={0.4}>
            {data.map((e, i) => <Cell key={i} fill={e.is_anomaly ? '#ef4444' : '#a855f7'} />)}
          </Scatter>
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 2000, y: 2000 }]} stroke="#333" strokeDasharray="5 5" />
        </ScatterChart>
      );
    case 'correlation':
      return (
        <ComposedChart data={data}>
          <CartesianGrid stroke="#111" vertical={false} />
          <XAxis dataKey="date" {...common} />
          <YAxis {...common} title="Correlation" />
          <Tooltip content={<DTooltip />} />
          <Bar dataKey="CORR_TEMP" fill="#f97316" opacity={0.5} name="Rolling Correlation (Temp)" />
          <Bar dataKey="CORR_HUMIDITY" fill="#3b82f6" opacity={0.5} name="Rolling Correlation (Humid)" />
          <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'High', position: 'right', fill: '#ef4444', fontSize: 8 }} />
        </ComposedChart>
      );
    case 'distribution':
      return (
        <BarChart data={distroData}>
          <CartesianGrid stroke="#111" vertical={false} />
          <XAxis dataKey="range" {...common} height={60} />
          <YAxis {...common} />
          <Tooltip cursor={{ fill: '#222' }} />
          <Bar dataKey="count" fill="#22d3ee" radius={[8, 8, 0, 0]} />
        </BarChart>
      );
    case 'trend':
      return (
        <LineChart data={data}>
          <CartesianGrid stroke="#111" />
          <XAxis dataKey="date" {...common} />
          <YAxis {...common} />
          <Tooltip content={<DTooltip />} />
          <Line type="monotone" dataKey="LOAD_MA30" stroke="#f97316" strokeWidth={4} dot={false} name="Structural Trend (MA30)" />
          <Line type="monotone" dataKey="LOAD_MA7" stroke="#22d3ee" strokeWidth={2} dot={false} name="Short-Term Signal (MA7)" />
        </LineChart>
      );
    default: return null;
  }
}

const MetricCard = ({ title, value, desc, color }: any) => (
  <div className={cn("p-6 rounded-[2rem] border transition-all hover:bg-zinc-800/10 group", color === 'cyan' ? 'bg-cyan-500/5 border-cyan-500/10' : 'bg-zinc-900/50 border-zinc-800')}>
    <div className="flex justify-between items-start mb-4">
      <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-widest">{title}</h4>
      <div className={cn("w-1.5 h-1.5 rounded-full", color === 'cyan' ? 'bg-cyan-500 group-hover:animate-ping' : 'bg-zinc-700')} />
    </div>
    <div className="text-3xl font-black tracking-tighter mb-1">{value || '---'}</div>
    <div className="text-[10px] font-bold text-zinc-500 uppercase">{desc}</div>
  </div>
);

const DTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/95 border border-zinc-800 p-5 rounded-3xl shadow-3xl backdrop-blur-xl ring-1 ring-white/5">
        <p className="text-[10px] font-black text-cyan-500 uppercase mb-3 tracking-widest">{label}</p>
        <div className="space-y-2">
          {payload.map((p: any) => (
            <div key={p.name} className="flex justify-between gap-12 items-center">
              <span className="text-[10px] font-bold text-zinc-500 uppercase">{p.name || p.dataKey}</span>
              <span className="text-xs font-black" style={{ color: p.color }}>{(p.value || 0).toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

function calculateCorrelation(x: number[], y: number[]) {
  const n = x.length; if (n === 0) return 0;
  const sX = x.reduce((a, b) => a + b, 0), sY = y.reduce((a, b) => a + b, 0);
  const sXY = x.reduce((a, b, i) => a + b * y[i], 0), sX2 = x.reduce((a, b) => a + b * b, 0), sY2 = y.reduce((a, b) => a + b * b, 0);
  const num = n * sXY - sX * sY;
  const den = Math.sqrt((n * sX2 - sX * sX) * (n * sY2 - sY * sY));
  return den === 0 ? 0 : num / den;
}

function calculateRSquared(x: number[], y: number[]) {
  const r = calculateCorrelation(x, y);
  return r * r;
}

export default App;
