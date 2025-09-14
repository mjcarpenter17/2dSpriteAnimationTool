import { Animation } from '../src/core/Animation';
import { PlaybackController } from '../src/core/PlaybackController';

function makeAnim(): Animation {
  const a = new Animation({ name: 'run', sheetPath: 'sheet.png', frames: [
    { frameIndex: 0, durationMs: 50 },
    { frameIndex: 1, durationMs: 50 },
    { frameIndex: 2, durationMs: 100 }
  ], loop: true, playback: { mode: 'forward', speedScale: 1.0 }, tags: [] });
  return a;
}

describe('PlaybackController', () => {
  test('advances frames respecting durations and loops', () => {
    const anim = makeAnim();
    const pc = new PlaybackController();
    pc.load(anim);
    pc.play();
    expect(pc.currentFrameGlobalIndex()).toBe(0);
    pc.update(60); // pass 50ms -> advance to frame 1, 10ms into frame1
    expect(pc.currentFrameGlobalIndex()).toBe(1);
    pc.update(40); // finish frame1 (remaining 40) -> move to frame2 at 0ms
    expect(pc.currentFrameGlobalIndex()).toBe(2);
    pc.update(120); // frame2 duration 100 -> wrap to frame0 (loop) with 20ms into frame0
    expect(pc.currentFrameGlobalIndex()).toBe(0);
  });

  test('stops at last frame if not looping', () => {
    const anim = new Animation({ name: 'once', sheetPath: 's.png', frames: [
      { frameIndex: 5, durationMs: 30 },
      { frameIndex: 6, durationMs: 30 }
    ], loop: false, playback: { mode: 'forward', speedScale: 1.0 }, tags: [] });
    const pc = new PlaybackController();
    pc.load(anim);
    pc.play();
    pc.update(35); // advance first frame
    expect(pc.currentFrameGlobalIndex()).toBe(6);
    pc.update(1000); // should stay
    expect(pc.currentFrameGlobalIndex()).toBe(6);
    expect(pc.isPlaying()).toBe(false);
  });
});
