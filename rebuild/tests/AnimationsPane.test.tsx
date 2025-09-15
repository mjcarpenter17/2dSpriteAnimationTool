import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnimationsPane } from '../src/renderer/components/AnimationsPane';

describe('AnimationsPane', () => {
  const baseAnim = (name: string) => ({
    name,
    sheetPath: '/sheet/a.png',
    frames: [ { frameIndex: 0, durationMs: 83 } ],
    loop: true,
    playback: { mode: 'forward', speedScale: 1 },
    tags: [],
    readOnly: false
  });

  it('renders animations filtered by active sheet and responds to refresh token', () => {
    const { rerender } = render(
      <AnimationsPane
        animations={[baseAnim('walk'), baseAnim('idle')]}
        activeSheetPath={'/sheet/a.png'}
        onCreate={() => {}}
        onSelect={() => {}}
        activeAnimation={null}
        newAnimName={'new'}
        onNewNameChange={() => {}}
        refreshToken={0}
      />
    );

    // Expect both animations
    expect(screen.getByText('walk')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();

    // Rerender with new token simulating F5 refresh
    rerender(
      <AnimationsPane
        animations={[baseAnim('walk'), baseAnim('idle'), baseAnim('jump')]}
        activeSheetPath={'/sheet/a.png'}
        onCreate={() => {}}
        onSelect={() => {}}
        activeAnimation={null}
        newAnimName={'new'}
        onNewNameChange={() => {}}
        refreshToken={1}
      />
    );

    expect(screen.getByText('jump')).toBeInTheDocument();
  });
});
