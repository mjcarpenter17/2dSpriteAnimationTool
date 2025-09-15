import React from 'react';
import { Animation } from '../../core/Animation';

export interface AnimationDescriptorLike {
  name: string;
  sheetPath: string;
  frames: { frameIndex: number; durationMs: number }[];
  loop: boolean;
  playback: { mode: string; speedScale: number };
  tags: string[];
  readOnly?: boolean; // placeholder for future Aseprite source
}

interface AnimationsPaneProps {
  animations: AnimationDescriptorLike[];
  activeSheetPath: string | null;
  onCreate: (name: string) => void;
  onSelect: (name: string) => void;
  activeAnimation: string | null;
  newAnimName: string;
  onNewNameChange: (v: string) => void;
  refreshToken: number; // increments when F5 pressed to allow effects later
}

export const AnimationsPane: React.FC<AnimationsPaneProps> = ({
  animations,
  activeSheetPath,
  onCreate,
  onSelect,
  activeAnimation,
  newAnimName,
  onNewNameChange,
  refreshToken
}) => {
  const filtered = animations.filter(a => a.sheetPath === activeSheetPath);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Animations</h3>
      <input
        type="text"
        value={newAnimName}
        onChange={(e) => onNewNameChange(e.target.value)}
        placeholder="Animation name"
        style={{ width: '100%', marginBottom: '4px' }}
      />
      <button
        style={{ width: '100%', marginBottom: '8px' }}
        disabled={!newAnimName.trim() || !activeSheetPath}
        onClick={() => {
          if (newAnimName.trim()) onCreate(newAnimName.trim());
        }}
      >
        Create Animation
      </button>
      <div style={{ fontSize: '12px', flex: 1, overflowY: 'auto', borderTop: '1px solid #ddd', paddingTop: 4 }}>
        {filtered.length === 0 && (
          <div style={{ color: '#777', fontStyle: 'italic' }}>No animations yet</div>
        )}
        {filtered.map(anim => {
          const active = anim.name === activeAnimation;
          return (
            <div
              key={anim.name + refreshToken /* ensure rerender highlight changes post-refresh if needed */}
              onClick={() => onSelect(anim.name)}
              style={{
                padding: '4px 6px',
                marginBottom: 2,
                cursor: 'pointer',
                background: active ? '#cdeffe' : '#fff',
                border: '1px solid #ccc',
                borderRadius: 3,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
              title={`Frames: ${anim.frames.length} | Duration: ${anim.frames.reduce((a,f)=>a+f.durationMs,0)}ms`}
            >
              <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{anim.name}</span>
              {anim.readOnly && (
                <span style={{ fontSize: 9, background: '#555', color: '#fff', padding: '2px 4px', borderRadius: 3 }} title="Read-only source">RO</span>
              )}
              <span style={{ fontSize: 9, background: '#eee', color: '#333', padding: '2px 4px', borderRadius: 3 }}>
                {anim.frames.length}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
