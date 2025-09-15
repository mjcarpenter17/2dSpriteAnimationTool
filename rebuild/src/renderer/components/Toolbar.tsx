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
  onZoomReset
}) => {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '8px', 
      padding: '8px', 
      background: '#f8f8f8', 
      borderBottom: '1px solid #ddd' 
    }}>
      <label 
        style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
        title="Toggle trim bounds overlay (hotkey: T) - shows tight non-transparent boundaries"
      >
        <input 
          type="checkbox" 
          checked={showTrim} 
          onChange={onToggleTrim} 
        />
        Show Trim
      </label>
      
      <label 
        style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
        title="Toggle pivot points overlay (hotkey: P) - shows anchor points for rotation/positioning"
      >
        <input 
          type="checkbox" 
          checked={showPivot} 
          onChange={onTogglePivot} 
        />
        Show Pivot
      </label>
      
      <label 
        style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
        title="Toggle slice boundaries overlay - shows hit boxes, collision areas, and other game regions"
      >
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
        title={`Current pivot strategy: ${pivotStrategy}. Auto-calculated pivot points use this strategy. Manual overrides take precedence.`}
      >
        <option value="bottom-center">Bottom Center</option>
        <option value="center">Center</option>
        <option value="top-left">Top Left</option>
        <option value="top-right">Top Right</option>
      </select>
      
      <button 
        onClick={onZoomReset}
        style={{ marginLeft: 'auto' }}
        title="Reset zoom to 100% and center view (hotkey: Ctrl+0)"
      >
        Reset Zoom
      </button>
    </div>
  );
};