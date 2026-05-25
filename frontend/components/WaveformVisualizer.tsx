'use client';

import { useEffect, useRef } from 'react';
import { useVoiceAssistant } from '@livekit/components-react';

export function WaveformVisualizer({ horizontal = false }: { horizontal?: boolean }) {
  const { audioTrack, state } = useVoiceAssistant();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const mediaStreamTrack = audioTrack?.publication?.track?.mediaStreamTrack;
    if (!mediaStreamTrack) return;

    const audioCtx = new AudioContext();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const source = audioCtx.createMediaStreamSource(new MediaStream([mediaStreamTrack]));
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      analyser.getByteFrequencyData(data);
      const ctx = canvas.getContext('2d')!;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (horizontal) {
        const barH = canvas.height / data.length;
        data.forEach((value, i) => {
          const w = (value / 255) * canvas.width;
          const alpha = 0.35 + (value / 255) * 0.65;
          ctx.fillStyle = `rgba(200, 148, 26, ${alpha})`;
          ctx.fillRect(0, i * barH, w, Math.max(barH - 1, 1));
        });
      } else {
        const barW = canvas.width / data.length;
        data.forEach((value, i) => {
          const h = (value / 255) * canvas.height;
          const alpha = 0.35 + (value / 255) * 0.65;
          ctx.fillStyle = `rgba(200, 148, 26, ${alpha})`;
          ctx.fillRect(i * barW, canvas.height - h, barW - 1, h);
        });
      }
      animRef.current = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      audioCtx.close();
    };
  }, [audioTrack, horizontal]);

  const speaking = state === 'speaking';

  if (horizontal) {
    return (
      <div className="flex items-center gap-3 w-full">
        <span
          className="text-[9px] font-mono tracking-[0.35em] flex-shrink-0"
          style={{ color: speaking ? '#FFD700' : '#4a3a0a' }}
        >
          {speaking ? 'COACH' : 'VOICE'}
        </span>
        <canvas
          ref={canvasRef}
          width={300}
          height={36}
          style={{ opacity: speaking ? 1 : 0.25, borderRadius: '2px', width: '100%', height: '36px' }}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 py-6">
      <span
        className="text-[9px] font-mono tracking-[0.35em]"
        style={{
          color: speaking ? '#FFD700' : '#4a3a0a',
          writingMode: 'vertical-rl',
          transform: 'rotate(180deg)',
        }}
      >
        {speaking ? 'COACH' : 'VOICE'}
      </span>
      <canvas
        ref={canvasRef}
        width={40}
        height={180}
        style={{ opacity: speaking ? 1 : 0.25, borderRadius: '2px' }}
      />
    </div>
  );
}
