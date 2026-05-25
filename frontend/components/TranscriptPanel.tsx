'use client';

import { useEffect, useRef } from 'react';
import { useTranscriptions } from '@livekit/components-react';

export function TranscriptPanel() {
  const transcriptions = useTranscriptions();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptions.length]);

  return (
    <div className="flex flex-col h-full">
      <p className="text-[9px] font-mono tracking-[0.25em] mb-4" style={{ color: '#8B6914' }}>
        SESSION TRANSCRIPT
      </p>

      <div className="flex-1 overflow-y-auto flex flex-col gap-4 pr-2">
        {transcriptions.length === 0 && (
          <p className="text-sm italic" style={{ color: '#2a2a2a' }}>
            Waiting for ze session to begin...
          </p>
        )}

        {transcriptions.map((t) => {
          const isCoach = !t.participantInfo?.identity?.startsWith('trainee');
          return (
            <div
              key={t.streamInfo.id}
              className="flex flex-col gap-1"
              style={{ alignItems: isCoach ? 'flex-start' : 'flex-end' }}
            >
              <span
                className="text-[8px] font-mono tracking-widest"
                style={{ color: isCoach ? '#8B6914' : '#444' }}
              >
                {isCoach ? 'ARNOLD' : 'YOU'}
              </span>
              <p
                className="text-sm leading-relaxed max-w-[85%]"
                style={{
                  color: isCoach ? '#C8941A' : '#aaa',
                  fontStyle: isCoach ? 'italic' : 'normal',
                  borderLeft: isCoach ? '2px solid #C8941A' : 'none',
                  borderRight: isCoach ? 'none' : '2px solid #333',
                  paddingLeft: isCoach ? '10px' : '0',
                  paddingRight: isCoach ? '0' : '10px',
                }}
              >
                {t.text}
              </p>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
