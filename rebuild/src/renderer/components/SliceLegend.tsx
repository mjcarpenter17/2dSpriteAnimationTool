import React from 'react';

// Minimal legend: placeholder types until slice typing expands.
interface SliceLegendProps {
  visible?: boolean;
}

const DEFAULT_TYPES = [
  { type: 'hit', color: '#f00', label: 'Hitbox' },
  { type: 'hurt', color: '#0f0', label: 'Hurtbox' },
  { type: 'custom', color: '#ff0', label: 'Custom' }
];

export const SliceLegend: React.FC<SliceLegendProps> = ({ visible = true }) => {
  if (!visible) return null;
  return (
    <div style={{ fontSize: 10, border: '1px solid var(--panel-border)', padding: 4, borderRadius: 4, background: 'var(--panel-bg)', marginTop: 8 }}>
      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>Slices</div>
      {DEFAULT_TYPES.map(t => (
        <div key={t.type} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ width: 12, height: 12, background: t.color, display: 'inline-block', border: '1px solid #000' }} />
          <span>{t.label}</span>
        </div>
      ))}
    </div>
  );
};
