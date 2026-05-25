'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';
import { Room } from 'livekit-client';
import { WaveformVisualizer } from '@/components/WaveformVisualizer';
import { TranscriptPanel } from '@/components/TranscriptPanel';

async function fetchToken(): Promise<{ server_url: string; participant_token: string }> {
  const identity = `trainee-${Date.now()}`;
  const res = await fetch('/api/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ participant_name: 'Trainee', participant_identity: identity }),
  });
  if (!res.ok) throw new Error(`Token request failed: ${res.status}`);
  return res.json();
}

function SessionView({ onEnd }: { onEnd: () => void }) {
  return (
    <div className="flex flex-col h-screen">

      {/* Dumbbell decorative strip */}
      <div
        className="flex items-center px-7 py-2"
        style={{ background: '#080808', borderBottom: '1px solid #0e0e0e' }}
      >
        <div style={{ flex: 1, height: '1px', background: 'linear-gradient(to right, transparent, #2a2a2a)' }} />
        <svg width="72" height="18" viewBox="0 0 144 36" fill="none" style={{ flexShrink: 0 }}>
          {/* handle */}
          <rect x="30" y="15" width="84" height="5" rx="1" fill="url(#dbS)" />
          {/* knurling */}
          <line x1="48" y1="15" x2="48" y2="20" stroke="rgba(0,0,0,0.5)" strokeWidth="1" />
          <line x1="53" y1="15" x2="53" y2="20" stroke="rgba(0,0,0,0.5)" strokeWidth="1" />
          <line x1="91" y1="15" x2="91" y2="20" stroke="rgba(0,0,0,0.5)" strokeWidth="1" />
          <line x1="96" y1="15" x2="96" y2="20" stroke="rgba(0,0,0,0.5)" strokeWidth="1" />
          {/* left collar */}
          <rect x="24" y="12" width="5" height="11" rx="1" fill="url(#dbG)" />
          {/* left plates: large outer, smaller inner */}
          <rect x="8"  y="5"  width="12" height="25" rx="2" fill="url(#dbP)" />
          <rect x="9"  y="5"  width="3"  height="25" fill="rgba(255,255,255,0.07)" />
          <rect x="18" y="9"  width="6"  height="17" rx="1" fill="url(#dbP2)" />
          {/* right collar */}
          <rect x="115" y="12" width="5" height="11" rx="1" fill="url(#dbG)" />
          {/* right plates: smaller inner, large outer */}
          <rect x="120" y="9"  width="6"  height="17" rx="1" fill="url(#dbP2)" />
          <rect x="124" y="5"  width="12" height="25" rx="2" fill="url(#dbP)" />
          <rect x="125" y="5"  width="3"  height="25" fill="rgba(255,255,255,0.07)" />
          <defs>
            <linearGradient id="dbS" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
              <stop offset="0%" stopColor="#999" />
              <stop offset="100%" stopColor="#555" />
            </linearGradient>
            <linearGradient id="dbG" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
              <stop offset="0%" stopColor="#FFD700" />
              <stop offset="100%" stopColor="#7a5810" />
            </linearGradient>
            <linearGradient id="dbP" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
              <stop offset="0%" stopColor="#1e1e1e" />
              <stop offset="60%" stopColor="#2e2e2e" />
              <stop offset="100%" stopColor="#141414" />
            </linearGradient>
            <linearGradient id="dbP2" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
              <stop offset="0%" stopColor="#252525" />
              <stop offset="60%" stopColor="#353535" />
              <stop offset="100%" stopColor="#1a1a1a" />
            </linearGradient>
          </defs>
        </svg>
        <div style={{ flex: 1, height: '1px', background: 'linear-gradient(to left, transparent, #2a2a2a)' }} />
      </div>

      <header className="flex items-center gap-3 px-4 md:px-8 py-5 border-b" style={{ borderColor: '#141414' }}>
        <div
          className="w-[3px] h-7 rounded-sm flex-shrink-0"
          style={{ background: 'linear-gradient(180deg, #FFD700, #8B6914)' }}
        />
        <div>
          <p className="text-sm font-bold tracking-widest" style={{ color: '#fff' }}>
            THE AUSTRIAN OAK
          </p>
          <p className="text-[9px] tracking-[0.3em]" style={{ color: '#FFD700' }}>
            EST. THAL, AUSTRIA 1947 &middot; 7&times; MR. OLYMPIA
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-[9px] tracking-widest" style={{ color: '#4ade80' }}>LIVE</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        {/* Mobile: horizontal waveform bar */}
        <div
          className="flex md:hidden items-center gap-3 px-4 border-b flex-shrink-0"
          style={{ height: '44px', borderColor: '#141414', background: '#0a0a0a' }}
        >
          <WaveformVisualizer horizontal />
        </div>

        {/* Desktop: vertical waveform sidebar */}
        <div
          className="hidden md:flex flex-shrink-0 items-center justify-center border-r"
          style={{ width: '72px', borderColor: '#141414', background: '#0d0d0d' }}
        >
          <WaveformVisualizer />
        </div>

        <div className="flex-1 overflow-hidden px-4 md:px-8 py-6">
          <TranscriptPanel />
        </div>
      </div>

      <footer className="flex justify-end px-4 md:px-8 py-4 border-t" style={{ borderColor: '#141414' }}>
        <button
          onClick={onEnd}
          className="text-[10px] tracking-widest px-4 py-2 border rounded-sm transition-colors hover:bg-white hover:text-black"
          style={{ borderColor: '#2a2a2a', color: '#555' }}
        >
          RACK UP
        </button>
      </footer>
    </div>
  );
}

const QUOTES = [
  "The pump is the greatest feeling you can get in the gym. I'm addicted to the pump.",
  'Strength does not come from winning. Your struggles develop your strengths.',
  'You can have results or excuses. Not both.',
  'The last three or four reps is what makes the muscle grow.',
] as const;

export default function Home() {
  const [conn, setConn] = useState<{ serverUrl: string; token: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const roomRef = useRef<Room | null>(null);

  const [quoteIdx, setQuoteIdx] = useState(0);
  const touchStartX = useRef<number | null>(null);

  useEffect(() => {
    const timer = setInterval(
      () => setQuoteIdx(i => (i + 1) % QUOTES.length),
      5000,
    );
    return () => clearInterval(timer);
  }, []);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const delta = e.changedTouches[0].clientX - touchStartX.current;
    if (Math.abs(delta) > 40)
      setQuoteIdx(i =>
        delta < 0
          ? (i + 1) % QUOTES.length
          : (i - 1 + QUOTES.length) % QUOTES.length,
      );
    touchStartX.current = null;
  };

  const handleStart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { server_url, participant_token } = await fetchToken();
      roomRef.current = new Room();
      setConn({ serverUrl: server_url, token: participant_token });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleEnd = useCallback(async () => {
    await roomRef.current?.disconnect();
    roomRef.current = null;
    setConn(null);
  }, []);

  if (!conn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-6 md:gap-10 px-4">

        {/* Heavy Load barbell */}
        <svg
          viewBox="0 0 280 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-[200px] md:w-[300px]"
          style={{ height: 'auto' }}
        >
          {/* shaft */}
          <rect x="0" y="47.5" width="280" height="5" rx="1" fill="url(#lbShaft)" />
          <rect x="0" y="47.5" width="280" height="1.5" fill="rgba(255,255,255,0.15)" />
          {/* knurling */}
          <line x1="72"  y1="47.5" x2="72"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="77"  y1="47.5" x2="77"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="82"  y1="47.5" x2="82"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="87"  y1="47.5" x2="87"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="92"  y1="47.5" x2="92"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="97"  y1="47.5" x2="97"  y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="102" y1="47.5" x2="102" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="107" y1="47.5" x2="107" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="170" y1="47.5" x2="170" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="175" y1="47.5" x2="175" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="180" y1="47.5" x2="180" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="185" y1="47.5" x2="185" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="190" y1="47.5" x2="190" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="195" y1="47.5" x2="195" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="200" y1="47.5" x2="200" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          <line x1="205" y1="47.5" x2="205" y2="52.5" stroke="rgba(0,0,0,0.45)" strokeWidth="1" />
          {/* sleeves */}
          <rect x="0"   y="46" width="55" height="8" rx="1.5" fill="url(#lbSleeve)" />
          <rect x="225" y="46" width="55" height="8" rx="1.5" fill="url(#lbSleeve)" />
          {/* left plates: 3× 45lb, innermost (x=35) to outermost (x=15) */}
          <rect x="35" y="20" width="10" height="60" rx="2" fill="url(#lbP45a)" />
          <rect x="36" y="20" width="3"  height="60" fill="rgba(255,255,255,0.06)" />
          <rect x="25" y="20" width="10" height="60" rx="2" fill="url(#lbP45b)" />
          <rect x="26" y="20" width="3"  height="60" fill="rgba(255,255,255,0.05)" />
          <rect x="15" y="20" width="10" height="60" rx="2" fill="url(#lbP45c)" />
          <rect x="16" y="20" width="3"  height="60" fill="rgba(255,255,255,0.04)" />
          {/* left collar */}
          <rect x="6"  y="41" width="7" height="18" rx="2" fill="url(#lbCol)" />
          <rect x="7"  y="41" width="2" height="18" rx="1" fill="rgba(255,255,255,0.22)" />
          {/* left tip */}
          <rect x="0"  y="44" width="4" height="12" rx="1.5" fill="#8B6914" />
          {/* right plates: innermost (x=235) to outermost (x=255) */}
          <rect x="235" y="20" width="10" height="60" rx="2" fill="url(#lbP45a)" />
          <rect x="236" y="20" width="3"  height="60" fill="rgba(255,255,255,0.06)" />
          <rect x="245" y="20" width="10" height="60" rx="2" fill="url(#lbP45b)" />
          <rect x="246" y="20" width="3"  height="60" fill="rgba(255,255,255,0.05)" />
          <rect x="255" y="20" width="10" height="60" rx="2" fill="url(#lbP45c)" />
          <rect x="256" y="20" width="3"  height="60" fill="rgba(255,255,255,0.04)" />
          {/* right collar */}
          <rect x="267" y="41" width="7" height="18" rx="2" fill="url(#lbCol)" />
          <rect x="268" y="41" width="2" height="18" rx="1" fill="rgba(255,255,255,0.22)" />
          {/* right tip */}
          <rect x="276" y="44" width="4" height="12" rx="1.5" fill="#8B6914" />
          {/* floor glow */}
          <ellipse cx="30"  cy="83" rx="14" ry="2.5" fill="rgba(255,215,0,0.08)" />
          <ellipse cx="250" cy="83" rx="14" ry="2.5" fill="rgba(255,215,0,0.08)" />
          <defs>
            <linearGradient id="lbShaft" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#bbb" />
              <stop offset="35%"  stopColor="#888" />
              <stop offset="100%" stopColor="#444" />
            </linearGradient>
            <linearGradient id="lbSleeve" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#ccc" />
              <stop offset="40%"  stopColor="#999" />
              <stop offset="100%" stopColor="#555" />
            </linearGradient>
            <linearGradient id="lbP45a" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#1e1e1e" />
              <stop offset="70%"  stopColor="#2e2e2e" />
              <stop offset="100%" stopColor="#141414" />
            </linearGradient>
            <linearGradient id="lbP45b" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#191919" />
              <stop offset="70%"  stopColor="#282828" />
              <stop offset="100%" stopColor="#111" />
            </linearGradient>
            <linearGradient id="lbP45c" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#141414" />
              <stop offset="70%"  stopColor="#222" />
              <stop offset="100%" stopColor="#0e0e0e" />
            </linearGradient>
            <linearGradient id="lbCol" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
              <stop offset="0%"   stopColor="#FFE44D" />
              <stop offset="40%"  stopColor="#FFD700" />
              <stop offset="100%" stopColor="#7a5810" />
            </linearGradient>
          </defs>
        </svg>

        {/* 7× Mr. Olympia badge */}
        <div
          className="flex items-center gap-2 px-4 py-1.5 text-[8px] tracking-[0.4em] uppercase"
          style={{ border: '1px solid #2a1f05', background: 'rgba(255,215,0,0.04)', color: '#8B6914' }}
        >
          <span style={{ color: '#FFD700' }}>★</span>
          7&times; Mr. Olympia &nbsp;&middot;&nbsp; Est. 1947 &nbsp;&middot;&nbsp; Venice Beach
          <span style={{ color: '#FFD700' }}>★</span>
        </div>

        {/* Title */}
        <div className="text-center">
          <h1 className="text-4xl font-black tracking-widest mb-2" style={{ color: '#FFD700' }}>
            THE AUSTRIAN OAK
          </h1>
          <p className="text-[10px] tracking-[0.5em]" style={{ color: '#8B6914' }}>
            PERSONAL COACHING &middot; VENICE BEACH &middot; 1977
          </p>
        </div>

        {/* Rotating quote */}
        <div
          className="max-w-sm md:max-w-lg text-center py-3 select-none"
          style={{ borderTop: '1px solid #1a1a1a', borderBottom: '1px solid #1a1a1a' }}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          <p className="text-[11px] italic leading-relaxed" style={{ color: '#6a5218' }}>
            &ldquo;{QUOTES[quoteIdx]}&rdquo;
          </p>
          <p className="text-[8px] tracking-[0.4em] mt-2" style={{ color: '#3a2e08' }}>
            &mdash; Arnold Schwarzenegger
          </p>
        </div>

        {/* Dot pager */}
        <div className="flex gap-1.5 items-center">
          {QUOTES.map((_, i) => (
            <button
              key={i}
              onClick={() => setQuoteIdx(i)}
              aria-label={`Quote ${i + 1}`}
              style={{
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                border: 'none',
                cursor: 'pointer',
                background: i === quoteIdx ? '#FFD700' : '#2a2a2a',
                padding: 0,
                transition: 'background 0.2s',
              }}
            />
          ))}
        </div>

        <button
          onClick={handleStart}
          disabled={loading}
          className="text-sm font-bold tracking-[0.2em] px-10 py-3 border transition-all hover:bg-yellow-500 hover:text-black disabled:opacity-30"
          style={{ borderColor: '#FFD700', color: '#FFD700' }}
        >
          {loading ? 'CONNECTING...' : '▶ BEGIN SESSION'}
        </button>
        {error && (
          <p className="text-[10px] tracking-widest" style={{ color: '#c0392b' }}>
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <LiveKitRoom
      room={roomRef.current ?? undefined}
      serverUrl={conn.serverUrl}
      token={conn.token}
      connect
      audio
      video={false}
    >
      <RoomAudioRenderer />
      <SessionView onEnd={handleEnd} />
    </LiveKitRoom>
  );
}
