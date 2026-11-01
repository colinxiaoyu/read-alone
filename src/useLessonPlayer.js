import { useCallback, useEffect, useRef, useState } from 'react';
import { LessonPlayer } from './player.js';

const storageKey = 'read-alone.settings.v2';
const defaults = { volume: .7, speed: 1, gap: 2.2, readMeaning: true, loop: true };

function readSettings() {
  let saved = {};
  try {
    const current = localStorage.getItem(storageKey);
    saved = JSON.parse(current || localStorage.getItem('read-alone.settings.v1')) || {};
    if (!current) saved.loop = true;
  } catch { /* Use the defaults when storage is unavailable. */ }
  const settings = { ...defaults };
  for (const name of ['volume', 'speed', 'gap']) {
    const [min, max] = { volume: [0, 1], speed: [.6, 1], gap: [1, 5] }[name];
    if (typeof saved[name] === 'number' && saved[name] >= min && saved[name] <= max) settings[name] = saved[name];
  }
  for (const name of ['readMeaning', 'loop']) if (typeof saved[name] === 'boolean') settings[name] = saved[name];
  return settings;
}

function snapshot(player) {
  return {
    index: player.index, state: player.state, kind: player.kind,
    highlighted: player.highlighted, remaining: player.remaining,
    completed: new Set(player.completed), settings: { ...player.settings },
    error: player.error, active: player.active,
  };
}

export default function useLessonPlayer(lesson) {
  const playerRef = useRef(null);
  const [view, setView] = useState(null);

  useEffect(() => {
    if (!lesson) { setView(null); return; }
    let alive = true;
    const player = new LessonPlayer(lesson, {
      settings: readSettings(),
      onChange: current => { if (alive) setView(snapshot(current)); },
    });
    playerRef.current = player;
    setView(snapshot(player));
    const stop = () => player.dispose();
    const keydown = event => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName)) return;
      if (event.code === 'ArrowRight' && player.index < lesson.words.length - 1) {
        event.preventDefault(); player.start(player.index + 1);
      }
      if (event.code === 'ArrowLeft' && player.index > 0) {
        event.preventDefault(); player.start(player.index - 1);
      }
      if (event.code === 'Space' && (event.target === document.body || event.target.tagName === 'MAIN')) {
        event.preventDefault(); player.toggle();
      }
    };
    window.addEventListener('pagehide', stop);
    document.addEventListener('keydown', keydown);
    return () => {
      alive = false;
      player.dispose();
      if (playerRef.current === player) playerRef.current = null;
      window.removeEventListener('pagehide', stop);
      document.removeEventListener('keydown', keydown);
    };
  }, [lesson]);

  const start = useCallback(index => playerRef.current?.start(index), []);
  const stop = useCallback(() => {
    playerRef.current?.dispose();
    playerRef.current = null;
    setView(null);
  }, []);
  const toggle = useCallback(() => playerRef.current?.toggle(), []);
  const previous = useCallback(() => {
    const player = playerRef.current;
    if (player) player.start(player.index - 1);
  }, []);
  const next = useCallback(() => {
    const player = playerRef.current;
    if (player) player.start(player.index + 1);
  }, []);
  const replay = useCallback(() => playerRef.current?.start(), []);
  const update = useCallback(changes => {
    const player = playerRef.current;
    if (!player) return;
    player.updateSettings(changes);
    try { localStorage.setItem(storageKey, JSON.stringify(player.settings)); } catch { /* Playback still works. */ }
  }, []);

  return { view, start, stop, toggle, previous, next, replay, update };
}
