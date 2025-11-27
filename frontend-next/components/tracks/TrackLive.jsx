"use client";

import { useEffect, useRef, useState, useMemo } from 'react';
import { useSocket } from '../../hooks/useSocket';

export default function TrackLive({ trackId = 'barber', raceId = null }) {
  const { latestUpdate, updates, isConnected } = useSocket(raceId, process.env.NEXT_PUBLIC_TELEMETRY_URL || 'http://localhost:3001');
  const [coords, setCoords] = useState(null);
  const [cars, setCars] = useState([]);
  const trailsRef = useRef({});
  const rafRef = useRef(null);

  // Load track coordinates from public JSON
  useEffect(() => {
    let mounted = true;
    fetch('/track_coords.json').then(r => r.json()).then(data => {
      if (!mounted) return;
      if (data && data[trackId]) setCoords(data[trackId].coordinates || []);
    }).catch(() => {
      setCoords([]);
    });
    return () => { mounted = false; };
  }, [trackId]);

  // Try to load an SVG for the track (exported from PDF) at /tracks/{trackId}.svg
  const [svgPathData, setSvgPathData] = useState('');
  useEffect(() => {
    let mounted = true;
    const svgUrl = `/tracks/${trackId}.svg`;
    fetch(svgUrl).then(async r => {
      if (!r.ok) throw new Error('no svg');
      const text = await r.text();
      if (!mounted) return;
      try {
        const doc = new DOMParser().parseFromString(text, 'image/svg+xml');
        const pathEl = doc.querySelector('path');
        if (pathEl && pathEl.getAttribute('d')) {
          setSvgPathData(pathEl.getAttribute('d'));
          return;
        }
        const svgEl = doc.querySelector('svg');
        if (svgEl) setSvgPathData(svgEl.innerHTML);
      } catch (e) {
        // ignore parse errors
      }
    }).catch(() => {
      // svg not present — fine, we'll use coords fallback
    });
    return () => { mounted = false; };
  }, [trackId]);

  // Accept updates from useSocket (may vary in shape)
  useEffect(() => {
    // prefer latestUpdate.cars or last element of updates
    let incoming = null;
    if (latestUpdate && latestUpdate.cars) incoming = latestUpdate.cars;
    else if (updates && updates.length) {
      const last = updates[updates.length - 1];
      if (last && last.cars) incoming = last.cars;
      else incoming = last;
    }

    if (Array.isArray(incoming)) {
      // normalize fields we expect: id, name, progress (0..1), lap, speed, gap
      const normalized = incoming.map(c => ({
        id: c.id || c.vehicle_id || c.vehicle_number || c.vehicleNumber || String(Math.random()),
        name: c.name || c.vehicle_number || c.vehicleId || c.id || 'Car',
        progress: typeof c.progress === 'number' ? c.progress : (c.lap_progress || c.progress_pct || 0),
        lap: c.lap || c.lap_number || 1,
        speed: c.speed || c.kph || c.kmh || 0,
        gap: c.gap || 0
      }));
      setCars(normalized);
    }
  }, [latestUpdate, updates]);

  // Build path (polyline) scaled to viewBox
  const pathPoints = useMemo(() => {
    if (!coords || coords.length === 0) return null;
    const pad = 40;
    const vw = 1000, vh = 1000;
    const sx = (vw - pad * 2);
    const sy = (vh - pad * 2);
    return coords.map(p => ({ x: pad + p.x * sx, y: pad + p.y * sy }));
  }, [coords]);

  // compute cumulative lengths for param mapping
  const pathSamples = useMemo(() => {
    // If an SVG path was loaded, sample it for accurate arclength mapping
    if (svgPathData && typeof document !== 'undefined') {
      try {
        const ns = 'http://www.w3.org/2000/svg';
        const tmpPath = document.createElementNS(ns, 'path');
        tmpPath.setAttribute('d', svgPathData);
        const totalLen = tmpPath.getTotalLength();
        const samples = [];
        const sampleCount = Math.max(200, Math.floor(totalLen / 5));
        let cum = 0;
        let prev = tmpPath.getPointAtLength(0);
        samples.push({ x: prev.x, y: prev.y, lenCum: 0, seg: 0 });
        for (let i = 1; i <= sampleCount; i++) {
          const pos = tmpPath.getPointAtLength((i / sampleCount) * totalLen);
          const dx = pos.x - prev.x, dy = pos.y - prev.y;
          const seg = Math.hypot(dx, dy);
          cum += seg;
          samples.push({ x: pos.x, y: pos.y, lenCum: cum, seg });
          prev = pos;
        }
        return { samples, length: cum, points: samples.map(s => ({ x: s.x, y: s.y })) };
      } catch (e) {
        // fall through to coords fallback
      }
    }

    if (!pathPoints) return null;
    const pts = pathPoints;
    const samples = [];
    let total = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i];
      const b = pts[(i + 1) % pts.length];
      const dx = b.x - a.x, dy = b.y - a.y;
      const seg = Math.hypot(dx, dy);
      samples.push({ x: a.x, y: a.y, seg, lenCum: total });
      total += seg;
    }
    return { samples, length: total, points: pts };
  }, [pathPoints, svgPathData]);

  function posOnPath(progress) {
    if (!pathSamples) return { x: 500, y: 500 };
    // Normalize progress to 0..1
    const p = ((progress % 1) + 1) % 1;
    const totalLen = pathSamples.length || 1;
    const targetLen = p * totalLen;
    const samples = pathSamples.samples;
    // Binary search for segment
    let lo = 0, hi = samples.length - 1;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (samples[mid].lenCum < targetLen) lo = mid + 1; else hi = mid;
    }
    const i = Math.max(0, lo - 1);
    const s = samples[i];
    const next = samples[(i + 1) % samples.length];
    const segLen = (next.lenCum - s.lenCum) || next.seg || 1;
    const t = Math.max(0, Math.min(1, (targetLen - s.lenCum) / segLen));
    const x = s.x + (next.x - s.x) * t;
    const y = s.y + (next.y - s.y) * t;
    return { x, y };
  }

  // Maintain trails and animate (simple SVG-based trails)
  useEffect(() => {
    if (!cars) return;
    // update trailsRef with latest car positions
    cars.forEach(c => {
      const pos = posOnPath(c.progress || 0);
      if (!trailsRef.current[c.id]) trailsRef.current[c.id] = [];
      trailsRef.current[c.id].push(pos);
      if (trailsRef.current[c.id].length > 40) trailsRef.current[c.id].shift();
    });
  }, [cars]);

  // Trigger re-render with RAF to get smooth trail fading
  useEffect(() => {
    let mounted = true;
    function tick() {
      if (!mounted) return;
      // decay trails alpha by shifting — handled in render via length
      rafRef.current = requestAnimationFrame(tick);
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => { mounted = false; cancelAnimationFrame(rafRef.current); };
  }, []);

  // Build SVG path string from points
  function buildSvgPath() {
    if (!pathPoints || pathPoints.length === 0) return '';
    const pts = pathPoints;
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) d += ` L ${pts[i].x} ${pts[i].y}`;
    d += ' Z';
    return d;
  }

  const svgPath = buildSvgPath();

  return (
    <div style={{ width: '100%', height: '500px', position: 'relative' }}>
      <svg viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet" style={{ width: '100%', height: '100%' }}>
        {/* Track surface */}
        <path d={svgPath} fill="#2a2a2a" stroke="#444" strokeWidth="60" opacity="0.3" />
        <path d={svgPath} fill="none" stroke="#666" strokeWidth="30" />
        <path d={svgPath} fill="none" stroke="#888" strokeWidth="25" />
        <path d={svgPath} fill="none" stroke="#fff" strokeWidth="3" strokeDasharray="15,10" opacity="0.6" />

        {/* trails */}
        {Object.keys(trailsRef.current).map(id => {
          const trail = trailsRef.current[id] || [];
          if (trail.length < 2) return null;
          const d = trail.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
          return <path key={`t-${id}`} d={d} fill="none" stroke="#ffd54d" strokeWidth={2} strokeOpacity={0.6} strokeLinecap="round" strokeLinejoin="round" />;
        })}

        {/* cars */}
        {cars.map(c => {
          const p = posOnPath(c.progress || 0);
          return (
            <g key={c.id}>
              <circle cx={p.x} cy={p.y} r={8} fill="#ffd54d" stroke="#222" strokeWidth={1} />
              <text x={p.x + 12} y={p.y + 4} fill="#fff" fontSize={12} fontWeight="bold">{c.name}</text>
            </g>
          );
        })}
      </svg>

      <div style={{ position: 'absolute', right: 12, top: 12, width: 280, background: 'rgba(0,0,0,0.6)', color: '#fff', padding: 10, borderRadius: 6 }}>
        <div style={{ fontWeight: 'bold', marginBottom: 6 }}>{trackId.toUpperCase()} — Live</div>
        <div style={{ fontSize: 13, opacity: 0.9 }}>WS: {isConnected ? 'connected' : 'disconnected'}</div>
        <div style={{ marginTop: 8 }}>
          {cars.slice(0, 8).map(c => (
            <div key={c.id} style={{ padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div style={{ fontWeight: '600' }}>{c.name}</div>
              <div style={{ fontSize: 12, color: '#ddd' }}>Lap {c.lap} • {c.speed} km/h • gap {c.gap}s</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
