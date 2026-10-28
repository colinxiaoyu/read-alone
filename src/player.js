export class LessonPlayer {
  constructor(lesson, { settings = {}, onChange = () => {}, audioFactory = () => new Audio() } = {}) {
    this.lesson = lesson;
    this.settings = { volume: .7, speed: 1, gap: 2.2, readMeaning: true, loop: true, ...settings };
    this.onChange = onChange;
    this.audioFactory = audioFactory;
    this.index = 0;
    this.state = 'ready';
    this.kind = '';
    this.highlighted = false;
    this.remaining = 0;
    this.completed = new Set();
    this.runId = 0;
    this.clip = null;
    this.wait = null;
    this.error = '';
  }

  emit() { this.onChange(this); }
  get active() { return ['loading', 'playing', 'gap'].includes(this.state); }

  updateSettings(changes) {
    Object.assign(this.settings, changes);
    if (this.clip) {
      this.clip.audio.volume = this.settings.volume;
      this.clip.audio.playbackRate = ['slow', 'normal'].includes(this.kind) ? this.settings.speed : 1;
    }
    this.emit();
  }

  cancel() {
    this.runId++;
    const clip = this.clip;
    this.clip = null;
    if (clip) { clip.cleanup(); clip.audio.pause(); clip.audio.removeAttribute('src'); clip.audio.load(); clip.finish(false); }
    const wait = this.wait;
    this.wait = null;
    if (wait) { clearInterval(wait.timer); wait.finish(false); }
  }

  start(index = this.index) {
    if (!Number.isInteger(index) || index < 0 || index >= this.lesson.words.length) return;
    if (this.state === 'complete' && index === 0) this.completed.clear();
    this.cancel();
    this.index = index;
    this.highlighted = false;
    this.error = '';
    const id = this.runId;
    this.run(id).catch(error => {
      if (id !== this.runId) return;
      this.cancel();
      this.state = 'error';
      this.error = error.message;
      this.emit();
    });
  }

  async run(id) {
    while (id === this.runId) {
      const word = this.lesson.words[this.index];
      if (!await this.playClip(word.audio.slow, 'slow', id)) return;
      if (this.settings.readMeaning && !await this.playClip(word.audio.meaning, 'meaning', id)) return;
      if (!await this.followGap(id)) return;
      if (!await this.playClip(word.audio.normal, 'normal', id)) return;
      if (!await this.followGap(id)) return;
      this.completed.add(this.index);
      if (this.index === this.lesson.words.length - 1) {
        if (this.settings.loop) {
          this.index = 0;
          this.completed.clear();
        } else {
          this.state = 'complete';
          this.kind = '';
          this.emit();
          return;
        }
      } else this.index++;
      this.highlighted = false;
    }
  }

  playClip(path, kind, id) {
    if (id !== this.runId) return Promise.resolve(false);
    return new Promise((resolve, reject) => {
      const audio = this.audioFactory();
      audio.preload = 'auto';
      audio.volume = this.settings.volume;
      audio.playbackRate = ['slow', 'normal'].includes(kind) ? this.settings.speed : 1;
      audio.preservesPitch = true;
      const current = () => id === this.runId && this.clip?.audio === audio;
      const playing = () => {
        if (!current()) return;
        if (this.state === 'paused') { audio.pause(); return; }
        this.state = 'playing';
        this.highlighted = true;
        this.emit();
      };
      const stalled = () => {
        if (current() && this.state !== 'paused') { this.state = 'loading'; this.emit(); }
      };
      const cleanup = () => {
        audio.removeEventListener('playing', playing);
        audio.removeEventListener('waiting', stalled);
        audio.removeEventListener('ended', ended);
        audio.removeEventListener('error', failed);
      };
      const ended = () => {
        if (!current()) return;
        cleanup(); this.clip = null; resolve(true);
      };
      const failed = () => {
        if (!current()) return;
        cleanup(); audio.pause(); this.clip = null;
        reject(new Error('这段声音暂时无法播放，点击重试。'));
      };
      this.clip = { audio, cleanup, finish: resolve, failed, id };
      this.state = 'loading';
      this.kind = kind;
      this.remaining = 0;
      audio.addEventListener('playing', playing);
      audio.addEventListener('waiting', stalled);
      audio.addEventListener('ended', ended);
      audio.addEventListener('error', failed);
      audio.src = path;
      this.emit();
      audio.play().catch(error => {
        if (current() && this.state !== 'paused' && error.name !== 'AbortError') failed();
      });
    });
  }

  followGap(id) {
    if (id !== this.runId) return Promise.resolve(false);
    this.state = 'gap';
    this.remaining = this.settings.gap;
    this.emit();
    return new Promise(resolve => {
      const wait = { finish: resolve, last: performance.now(), timer: null };
      wait.timer = setInterval(() => {
        if (id !== this.runId) return;
        if (this.state !== 'gap') return;
        const now = performance.now();
        this.remaining = Math.max(0, this.remaining - (now - wait.last) / 1000);
        wait.last = now;
        this.emit();
        if (!this.remaining) { clearInterval(wait.timer); this.wait = null; resolve(true); }
      }, 50);
      this.wait = wait;
    });
  }

  pause() {
    if (!this.active) return;
    if (this.wait) {
      this.remaining = Math.max(0, this.remaining - (performance.now() - this.wait.last) / 1000);
    }
    this.state = 'paused';
    this.clip?.audio.pause();
    this.emit();
  }

  resume() {
    if (this.state !== 'paused') return;
    if (this.wait) {
      this.wait.last = performance.now();
      this.state = 'gap';
    } else if (this.clip) {
      const clip = this.clip;
      this.state = 'loading';
      clip.audio.play().catch(error => {
        if (this.clip === clip && this.state !== 'paused' && error.name !== 'AbortError') clip.failed();
      });
    }
    this.emit();
  }

  toggle() {
    if (this.active) this.pause();
    else if (this.state === 'paused') this.resume();
    else this.start(this.state === 'complete' ? 0 : this.index);
  }

  dispose() { this.cancel(); }
}
