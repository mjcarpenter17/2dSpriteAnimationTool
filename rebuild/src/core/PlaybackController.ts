import { Animation } from './Animation';

export interface PlaybackState {
  currentFrameIndex: number; // index inside animation.frames array
  playing: boolean;
  elapsedInFrame: number; // ms within current frame
}

export class PlaybackController {
  private anim: Animation | null = null;
  private state: PlaybackState = { currentFrameIndex: 0, playing: false, elapsedInFrame: 0 };
  private speedScale = 1.0;

  load(animation: Animation | null) {
    this.anim = animation;
    this.state = { currentFrameIndex: 0, playing: !!animation, elapsedInFrame: 0 };
    this.speedScale = animation ? animation.playback.speedScale : 1.0;
  }

  play() { if (this.anim) this.state.playing = true; }
  pause() { this.state.playing = false; }
  toggle() { this.state.playing = !this.state.playing && !!this.anim; }
  isPlaying() { return this.state.playing; }
  currentFrameGlobalIndex(): number | null {
    if (!this.anim) return null; const ref = this.anim.frames[this.state.currentFrameIndex]; return ref ? ref.frameIndex : null;
  }
  currentFrameNumberInAnimation(): number { return this.state.currentFrameIndex; }

  update(deltaMs: number) {
    if (!this.anim || !this.state.playing) return;
    if (this.anim.frames.length === 0) return;
    this.state.elapsedInFrame += deltaMs * this.speedScale;
    let safeguard = 0; // prevent infinite loops if durations are zero
    while (safeguard < 500) { // enough for pathological cases
      const frameRef = this.anim.frames[this.state.currentFrameIndex];
      const dur = Math.max(1, frameRef.durationMs); // clamp to avoid zero
      if (this.state.elapsedInFrame < dur) break;
      this.state.elapsedInFrame -= dur;
      this.state.currentFrameIndex++;
      if (this.state.currentFrameIndex >= this.anim.frames.length) {
        if (this.anim.loop) {
          this.state.currentFrameIndex = 0;
        } else {
          this.state.currentFrameIndex = this.anim.frames.length - 1;
          this.state.playing = false;
          this.state.elapsedInFrame = 0;
          break;
        }
      }
      safeguard++;
    }
  }
}
