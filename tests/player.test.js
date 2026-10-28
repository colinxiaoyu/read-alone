import test from 'node:test';
import assert from 'node:assert/strict';
import { LessonPlayer } from '../src/player.js';

class AudioDouble extends EventTarget {
  paused = true;
  play() { this.paused = false; queueMicrotask(() => { if (!this.paused) this.dispatchEvent(new Event('playing')); }); return Promise.resolve(); }
  pause() { this.paused = true; }
  removeAttribute(name) { if (name === 'src') this.src = ''; }
  load() {}
  end() { this.paused = true; this.dispatchEvent(new Event('ended')); }
}
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(condition) {
  for (let n = 0; n < 100; n++) { if (condition()) return; await sleep(5); }
  assert.fail('Player did not reach the expected state');
}
function setup(t, { count = 3, settings = {} } = {}) {
  const audios = [];
  const lesson = { words: Array.from({ length: count }, (_, n) => ({ word: `word-${n}`, audio: { slow: `${n}-slow.wav`, normal: `${n}-normal.wav`, meaning: `${n}-zh.wav` } })) };
  const player = new LessonPlayer(lesson, { settings: { gap: .05, loop: false, ...settings }, audioFactory: () => { const audio = new AudioDouble(); audios.push(audio); return audio; } });
  t.after(() => player.dispose());
  return { player, audios };
}

test('English, Chinese, follow-along gap and second English play in order', async t => {
  const { player, audios } = setup(t);
  player.start(0); await tick();
  assert.equal(audios[0].src, '0-slow.wav');
  assert.equal(player.highlighted, true);
  audios[0].end(); await tick();
  assert.equal(audios[1].src, '0-zh.wav');
  assert.equal(player.kind, 'meaning');
  audios[1].end(); await tick();
  assert.equal(player.state, 'gap');
  await until(() => audios.length === 3);
  assert.equal(audios[2].src, '0-normal.wav');
  assert.equal(player.index, 0);
});

test('rapid jumps cancel old audio and ignore its late events', async t => {
  const { player, audios } = setup(t);
  player.start(0); await tick();
  const old = audios[0];
  player.start(1); player.start(2); await tick();
  assert.equal(old.paused, true);
  old.dispatchEvent(new Event('playing')); old.end();
  await tick();
  assert.equal(player.index, 2);
  assert.equal(player.clip.audio.src, '2-slow.wav');
  assert.equal(player.state, 'playing');
  assert.equal(audios.filter(audio => !audio.paused).length, 1);
});

test('pausing a gap freezes remaining time and resuming completes it once', async t => {
  const { player, audios } = setup(t, { settings: { readMeaning: false, gap: .15 } });
  player.start(); await tick(); audios[0].end(); await tick();
  assert.equal(player.state, 'gap');
  player.pause();
  const remaining = player.remaining;
  await sleep(200);
  assert.equal(player.remaining, remaining);
  assert.equal(audios.length, 1);
  player.resume();
  await until(() => audios.length === 2);
  assert.equal(audios[1].src, '0-normal.wav');
  assert.equal(player.state, 'playing');
});

test('volume applies to every clip and English speed leaves Chinese at its recorded rate', async t => {
  const { player, audios } = setup(t);
  player.start(); await tick();
  player.updateSettings({ volume: 0, speed: .85 });
  assert.equal(audios[0].volume, 0);
  assert.equal(audios[0].playbackRate, .85);
  audios[0].end(); await tick();
  assert.equal(audios[1].volume, 0);
  assert.equal(audios[1].playbackRate, 1);
  player.updateSettings({ volume: .3 });
  assert.equal(audios[1].volume, .3);
  audios[1].end();
  await until(() => audios.length === 3);
  assert.equal(audios[2].playbackRate, .85);
});

test('a playback failure stays on the word and can be retried', async t => {
  const { player, audios } = setup(t);
  player.start(1); await tick();
  audios[0].dispatchEvent(new Event('error')); await tick();
  assert.equal(player.state, 'error');
  assert.equal(player.index, 1);
  assert.equal(audios[0].paused, true);
  player.toggle(); await tick();
  assert.equal(audios[1].src, '1-slow.wav');
  assert.equal(player.state, 'playing');
});

test('the course completes after both repetitions and starts over cleanly', async t => {
  const { player, audios } = setup(t, { count: 1, settings: { readMeaning: false } });
  player.start(); await tick(); audios[0].end();
  await until(() => audios.length === 2); audios[1].end();
  await until(() => player.state === 'complete');
  assert.equal(player.completed.size, 1);
  player.toggle(); await tick();
  assert.equal(player.completed.size, 0);
  assert.equal(audios[2].src, '0-slow.wav');
});

test('pausing and resuming an active recording preserves the audio instance', async t => {
  const { player, audios } = setup(t);
  player.start(); await tick();
  player.pause(); assert.equal(audios[0].paused, true);
  player.resume(); await tick();
  assert.equal(audios.length, 1);
  assert.equal(audios[0].paused, false);
  assert.equal(player.state, 'playing');
});

test('looping returns directly to the first word without course announcements', async t => {
  const { player, audios } = setup(t, { count: 1, settings: { readMeaning: false, loop: true } });
  player.lesson.intro = 'unwanted-intro.wav';
  player.lesson.complete = 'unwanted-outro.wav';
  player.start(); await tick();
  assert.equal(audios[0].src, '0-slow.wav');
  audios[0].end();
  await until(() => audios.length === 2); audios[1].end();
  await until(() => audios.length === 3);
  assert.equal(audios[2].src, '0-slow.wav');
  assert.equal(player.index, 0);
  assert.equal(player.state, 'playing');
});
