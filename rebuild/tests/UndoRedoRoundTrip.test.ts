/**
 * @jest-environment jsdom
 */

import { FrameOverridesStore } from '../src/core/FrameOverridesStore';

// Mock command stack for testing undo operations
interface Command {
  label: string;
  do(): void;
  undo(): void;
}

class MockCommandStack {
  private done: Command[] = [];
  private undone: Command[] = [];

  push(command: Command): void {
    // Execute command immediately
    command.do();
    
    // Add to done stack
    this.done.push(command);
    
    // Clear undone stack (new action invalidates redo)
    this.undone = [];
  }

  undo(): boolean {
    const command = this.done.pop();
    if (command) {
      command.undo();
      this.undone.push(command);
      return true;
    }
    return false;
  }

  redo(): boolean {
    const command = this.undone.pop();
    if (command) {
      command.do();
      this.done.push(command);
      return true;
    }
    return false;
  }

  canUndo(): boolean {
    return this.done.length > 0;
  }

  canRedo(): boolean {
    return this.undone.length > 0;
  }

  clear(): void {
    this.done = [];
    this.undone = [];
  }

  getUndoCount(): number {
    return this.done.length;
  }

  getRedoCount(): number {
    return this.undone.length;
  }
}

describe('Undo/Redo Round-trip Tests', () => {
  let overrideStore: FrameOverridesStore;
  let commandStack: MockCommandStack;

  beforeEach(() => {
    overrideStore = new FrameOverridesStore();
    commandStack = new MockCommandStack();
  });

  test('pivot override undo/redo cycle', () => {
    const frameIndex = 5;
    const initialPivot = { x: 10, y: 20 };
    const newPivot = { x: 15, y: 25 };

    // Verify no initial override
    expect(overrideStore.getPivot(frameIndex)).toBeUndefined();

    // Create command to set pivot override
    const setPivotCommand: Command = {
      label: 'Set Pivot Override',
      do() {
        overrideStore.setPivot(frameIndex, newPivot);
      },
      undo() {
        overrideStore.clearPivot(frameIndex);
      }
    };

    // Execute command
    commandStack.push(setPivotCommand);

    // Verify override was set
    expect(overrideStore.getPivot(frameIndex)).toEqual(newPivot);
    expect(commandStack.canUndo()).toBe(true);
    expect(commandStack.canRedo()).toBe(false);

    // Undo
    const undoSuccess = commandStack.undo();
    expect(undoSuccess).toBe(true);
    expect(overrideStore.getPivot(frameIndex)).toBeUndefined();
    expect(commandStack.canUndo()).toBe(false);
    expect(commandStack.canRedo()).toBe(true);

    // Redo
    const redoSuccess = commandStack.redo();
    expect(redoSuccess).toBe(true);
    expect(overrideStore.getPivot(frameIndex)).toEqual(newPivot);
    expect(commandStack.canUndo()).toBe(true);
    expect(commandStack.canRedo()).toBe(false);
  });

  test('trim override undo/redo with previous value preservation', () => {
    const frameIndex = 3;
    const originalTrim = { x: 5, y: 5, w: 20, h: 20 };
    const newTrim = { x: 10, y: 10, w: 15, h: 15 };

    // Set initial override
    overrideStore.setTrim(frameIndex, originalTrim);

    // Create command to modify existing override
    const modifyTrimCommand: Command = {
      label: 'Modify Trim Override',
      do() {
        overrideStore.setTrim(frameIndex, newTrim);
      },
      undo() {
        overrideStore.setTrim(frameIndex, originalTrim);
      }
    };

    // Execute modification
    commandStack.push(modifyTrimCommand);

    // Verify new value
    expect(overrideStore.getTrim(frameIndex)).toEqual(newTrim);

    // Undo should restore original value
    commandStack.undo();
    expect(overrideStore.getTrim(frameIndex)).toEqual(originalTrim);

    // Redo should apply new value again
    commandStack.redo();
    expect(overrideStore.getTrim(frameIndex)).toEqual(newTrim);
  });

  test('multiple sequential operations with undo/redo', () => {
    const frame1 = 1, frame2 = 2, frame3 = 3;
    const pivot1 = { x: 10, y: 10 };
    const pivot2 = { x: 20, y: 20 };
    const trim3 = { x: 5, y: 5, w: 30, h: 30 };

    // Command 1: Set pivot for frame 1
    commandStack.push({
      label: 'Set Pivot Frame 1',
      do() { overrideStore.setPivot(frame1, pivot1); },
      undo() { overrideStore.clearPivot(frame1); }
    });

    // Command 2: Set pivot for frame 2
    commandStack.push({
      label: 'Set Pivot Frame 2',
      do() { overrideStore.setPivot(frame2, pivot2); },
      undo() { overrideStore.clearPivot(frame2); }
    });

    // Command 3: Set trim for frame 3
    commandStack.push({
      label: 'Set Trim Frame 3',
      do() { overrideStore.setTrim(frame3, trim3); },
      undo() { overrideStore.clearTrim(frame3); }
    });

    // Verify all overrides are set
    expect(overrideStore.getPivot(frame1)).toEqual(pivot1);
    expect(overrideStore.getPivot(frame2)).toEqual(pivot2);
    expect(overrideStore.getTrim(frame3)).toEqual(trim3);
    expect(commandStack.getUndoCount()).toBe(3);

    // Undo last command (trim)
    commandStack.undo();
    expect(overrideStore.getPivot(frame1)).toEqual(pivot1);
    expect(overrideStore.getPivot(frame2)).toEqual(pivot2);
    expect(overrideStore.getTrim(frame3)).toBeUndefined();
    expect(commandStack.getUndoCount()).toBe(2);
    expect(commandStack.getRedoCount()).toBe(1);

    // Undo second command (pivot frame 2)
    commandStack.undo();
    expect(overrideStore.getPivot(frame1)).toEqual(pivot1);
    expect(overrideStore.getPivot(frame2)).toBeUndefined();
    expect(overrideStore.getTrim(frame3)).toBeUndefined();

    // Undo first command (pivot frame 1)
    commandStack.undo();
    expect(overrideStore.getPivot(frame1)).toBeUndefined();
    expect(overrideStore.getPivot(frame2)).toBeUndefined();
    expect(overrideStore.getTrim(frame3)).toBeUndefined();
    expect(commandStack.getUndoCount()).toBe(0);
    expect(commandStack.getRedoCount()).toBe(3);

    // Redo all commands
    commandStack.redo(); // pivot frame 1
    commandStack.redo(); // pivot frame 2
    commandStack.redo(); // trim frame 3

    // Verify all restored
    expect(overrideStore.getPivot(frame1)).toEqual(pivot1);
    expect(overrideStore.getPivot(frame2)).toEqual(pivot2);
    expect(overrideStore.getTrim(frame3)).toEqual(trim3);
    expect(commandStack.getUndoCount()).toBe(3);
    expect(commandStack.getRedoCount()).toBe(0);
  });

  test('new command clears redo stack', () => {
    const frameIndex = 1;
    const pivot1 = { x: 10, y: 10 };
    const pivot2 = { x: 20, y: 20 };
    const pivot3 = { x: 30, y: 30 };

    // Execute two commands
    commandStack.push({
      label: 'Set Pivot 1',
      do() { overrideStore.setPivot(frameIndex, pivot1); },
      undo() { overrideStore.clearPivot(frameIndex); }
    });

    commandStack.push({
      label: 'Set Pivot 2',
      do() { overrideStore.setPivot(frameIndex, pivot2); },
      undo() { overrideStore.setPivot(frameIndex, pivot1); }
    });

    // Undo one command
    commandStack.undo();
    expect(overrideStore.getPivot(frameIndex)).toEqual(pivot1);
    expect(commandStack.getRedoCount()).toBe(1);

    // Execute new command - should clear redo stack
    commandStack.push({
      label: 'Set Pivot 3',
      do() { overrideStore.setPivot(frameIndex, pivot3); },
      undo() { overrideStore.setPivot(frameIndex, pivot1); }
    });

    expect(overrideStore.getPivot(frameIndex)).toEqual(pivot3);
    expect(commandStack.getRedoCount()).toBe(0); // Redo stack cleared
    expect(commandStack.getUndoCount()).toBe(2);
  });

  test('undo/redo state consistency', () => {
    // Test that undo/redo operations maintain consistent state
    const frameIndex = 0;
    const states = [
      { x: 0, y: 0 },
      { x: 10, y: 10 },
      { x: 20, y: 20 },
      { x: 30, y: 30 }
    ];

    // Build up a series of commands
    for (let i = 1; i < states.length; i++) {
      const prevState = states[i - 1];
      const newState = states[i];

      commandStack.push({
        label: `Set State ${i}`,
        do() { overrideStore.setPivot(frameIndex, newState); },
        undo() { 
          if (i === 1) {
            overrideStore.clearPivot(frameIndex);
          } else {
            overrideStore.setPivot(frameIndex, prevState);
          }
        }
      });
    }

    // Verify final state
    expect(overrideStore.getPivot(frameIndex)).toEqual(states[states.length - 1]);

    // Undo all the way back
    while (commandStack.canUndo()) {
      commandStack.undo();
    }

    // Should be back to initial state (no override)
    expect(overrideStore.getPivot(frameIndex)).toBeUndefined();

    // Redo all the way forward
    while (commandStack.canRedo()) {
      commandStack.redo();
    }

    // Should be back to final state
    expect(overrideStore.getPivot(frameIndex)).toEqual(states[states.length - 1]);
  });

  test('command execution order during undo/redo', () => {
    const executionLog: string[] = [];
    const frameIndex = 0;

    const command: Command = {
      label: 'Test Command',
      do() {
        executionLog.push('do');
        overrideStore.setPivot(frameIndex, { x: 10, y: 10 });
      },
      undo() {
        executionLog.push('undo');
        overrideStore.clearPivot(frameIndex);
      }
    };

    // Initial execution
    commandStack.push(command);
    expect(executionLog).toEqual(['do']);

    // Undo
    commandStack.undo();
    expect(executionLog).toEqual(['do', 'undo']);

    // Redo
    commandStack.redo();
    expect(executionLog).toEqual(['do', 'undo', 'do']);

    // Undo again
    commandStack.undo();
    expect(executionLog).toEqual(['do', 'undo', 'do', 'undo']);
  });
});