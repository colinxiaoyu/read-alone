import { useLayoutEffect, useRef } from 'react';

export default function WordList({ words, view, onSelect, layout }) {
  const listRef = useRef(null);
  const rows = useRef([]);
  const index = view.index;

  useLayoutEffect(() => {
    const reveal = () => {
      const list = listRef.current;
      const row = rows.current[index];
      if (!list || !row) return;
      const bounds = list.getBoundingClientRect();
      const position = row.getBoundingClientRect();
      if (position.top < bounds.top) list.scrollTop -= bounds.top - position.top;
      else if (position.bottom > bounds.bottom) list.scrollTop += position.bottom - bounds.bottom;
    };
    reveal();
    const observer = new ResizeObserver(reveal);
    observer.observe(listRef.current);
    return () => observer.disconnect();
  }, [index, layout.zoom]);

  return <aside className="word-panel" aria-label="本课词表">
    <div className="word-panel-heading">
      <h2>单词列表</h2>
      <div className="list-zoom-controls">
        <label htmlFor="list-zoom">字号</label>
        <button type="button" aria-label="缩小列表文字" disabled={layout.zoom <= .6} onClick={() => layout.setZoom(layout.zoom - .1)}>−</button>
        <input id="list-zoom" type="range" min="60" max="180" step="5" value={Math.round(layout.zoom * 100)} aria-label="列表字号百分比" onChange={event => layout.setZoom(Number(event.target.value) / 100)} />
        <output id="list-zoom-value" htmlFor="list-zoom">{Math.round(layout.zoom * 100)}%</output>
        <button type="button" aria-label="放大列表文字" disabled={layout.zoom >= 1.8} onClick={() => layout.setZoom(layout.zoom + .1)}>＋</button>
      </div>
    </div>
    <ol id="word-list" className="word-list" ref={listRef}>
      {words.map((word, i) => {
        const current = i === index;
        const classes = ['word-row', current && 'is-selected', current && view.highlighted && 'is-current', view.completed.has(i) && 'is-done'].filter(Boolean).join(' ');
        return <li key={word.id}>
          <button ref={node => { rows.current[i] = node; }} type="button" className={classes}
            aria-current={current ? 'true' : undefined} aria-label={`${word.word}，${word.pos}，${word.meaning}`}
            onClick={() => onSelect(i)}>
            <span className="word-number">{view.completed.has(i) ? '✓' : String(i + 1).padStart(2, '0')}</span>
            <span className="word-name" lang="en">{word.word}</span>
            <span className="word-phonetic" lang="en">{word.phonetic}</span>
            <span className="word-meaning"><span className="word-pos">{word.pos}</span>{word.meaning}</span>
          </button>
        </li>;
      })}
    </ol>
  </aside>;
}
