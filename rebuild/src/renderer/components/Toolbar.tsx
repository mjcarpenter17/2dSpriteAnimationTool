import React from 'react';

interface ToolbarProps {
  showTrim: boolean;
  showPivot: boolean;
  showSlices: boolean;
  pivotStrategy: string;
  onToggleTrim: () => void;
  onTogglePivot: () => void;
  onToggleSlices: () => void;
  onPivotStrategyChange: (strategy: string) => void;
  onZoomReset: () => void;
  extraButtons?: React.ReactNode;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  showTrim,
  showPivot,
  showSlices,
  pivotStrategy,
  onToggleTrim,
  onTogglePivot,
  onToggleSlices,
  onPivotStrategyChange,
  onZoomReset,
  extraButtons
}) => {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '8px', 
      padding: '8px', 
      background: 'var(--panel-bg)', 
      borderBottom: '1px solid var(--panel-border)'
    }}>
      <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <input 
          type="checkbox" 
          checked={showTrim} 
          onChange={onToggleTrim} 
        />
        Show Trim
      </label>
      
      <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <input 
          type="checkbox" 
          checked={showPivot} 
          onChange={onTogglePivot} 
        />
        Show Pivot
      </label>
      
      <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <input 
          type="checkbox" 
          checked={showSlices} 
          onChange={onToggleSlices} 
        />
        Show Slices
      </label>
      
      <select 
        value={pivotStrategy} 
        onChange={(e) => onPivotStrategyChange(e.target.value)}
        style={{ marginLeft: '16px' }}
      >
        <option value="bottom-center">Bottom Center</option>
        <option value="center">Center</option>
        <option value="top-left">Top Left</option>
      </select>
      
      <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
        <button onClick={onZoomReset}>Reset Zoom</button>
        {extraButtons}
      </div>
    </div>
  );
};