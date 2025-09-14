import React from 'react';

interface StatusBarProps {
  message: string;
  undoCount: number;
  redoCount: number;
  onUndo: () => void;
  onRedo: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({ 
  message, 
  undoCount, 
  redoCount, 
  onUndo, 
  onRedo 
}) => {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      padding: '4px 8px', 
      background: '#f0f0f0', 
      borderTop: '1px solid #ccc',
      fontSize: '12px'
    }}>
      <span>{message}</span>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button 
          onClick={onUndo} 
          disabled={undoCount === 0}
          style={{ fontSize: '11px', padding: '2px 6px' }}
        >
          Undo ({undoCount})
        </button>
        <button 
          onClick={onRedo} 
          disabled={redoCount === 0}
          style={{ fontSize: '11px', padding: '2px 6px' }}
        >
          Redo ({redoCount})
        </button>
      </div>
    </div>
  );
};