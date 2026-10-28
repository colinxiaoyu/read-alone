import { useCallback, useEffect, useState } from 'react';

const key = 'read-alone.layout.v1';
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

export default function useLayoutSettings() {
  const [layout, setLayout] = useState(() => {
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(key)) || {}; } catch { /* Use the default layout. */ }
    return {
      width: Number.isFinite(saved.width) ? clamp(saved.width, 30, 75) : 66,
      zoom: Number.isFinite(saved.zoom) ? clamp(saved.zoom, .6, 1.8) : 1,
    };
  });
  useEffect(() => {
    const timer = setTimeout(() => {
      try { localStorage.setItem(key, JSON.stringify(layout)); } catch { /* The controls still work. */ }
    }, 150);
    return () => clearTimeout(timer);
  }, [layout]);
  const setWidth = useCallback(width => setLayout(current => ({ ...current, width: clamp(width, 30, 75) })), []);
  const setZoom = useCallback(zoom => setLayout(current => ({ ...current, zoom: clamp(Math.round(zoom * 20) / 20, .6, 1.8) })), []);
  return { ...layout, setWidth, setZoom };
}
