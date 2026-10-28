import { useEffect, useRef, useState } from 'react';
import useLessonPlayer from './useLessonPlayer.js';
import WordList from './WordList.jsx';
import PlayerControls from './PlayerControls.jsx';
import CurrentWord from './CurrentWord.jsx';
import useLayoutSettings from './useLayoutSettings.js';

function status(view) {
  if (view.state === 'ready') return '准备好了';
  if (view.state === 'paused') return '已暂停';
  if (view.state === 'complete') return '本课跟读完成';
  if (view.state === 'error') return '声音播放中断';
  if (view.state === 'gap') return `请跟读 · ${view.remaining.toFixed(1)} 秒`;
  return { slow: '英文示范 · 第 1 遍', normal: '英文示范 · 第 2 遍', meaning: '中文释义' }[view.kind] || '正在准备声音';
}

export default function App() {
  const [lesson, setLesson] = useState(null);
  const [error, setError] = useState('');
  const layout = useLayoutSettings();
  const workspace = useRef(null);
  const dragging = useRef(false);
  const [resizing, setResizing] = useState(false);
  const controller = useLessonPlayer(lesson);
  const { view } = controller;

  useEffect(() => {
    const abort = new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/book2/lesson-62.json`, { signal: abort.signal, cache: 'no-store' })
      .then(response => {
        if (!response.ok) throw new Error('词表加载失败，请刷新页面重试。');
        return response.json();
      })
      .then(data => setLesson({ ...data, words: data.words.map(word => ({ ...word,
        audio: Object.fromEntries(Object.entries(word.audio).map(([kind, path]) => [kind, `${import.meta.env.BASE_URL}${path}`])),
      })) }))
      .catch(failure => { if (failure.name !== 'AbortError') setError(failure.message); });
    return () => abort.abort();
  }, []);

  const word = lesson && view ? lesson.words[view.index] : null;
  const progress = view ? (view.state === 'complete' ? lesson.words.length : view.completed.size) : 0;

  return <div className="shell" style={{ '--list-zoom': layout.zoom }}>
    <header className="header"><h1>新概念英语第二册 · 第 62 课</h1><span>单词跟读</span></header>
    <main>
      {error ? <div id="load-error" className="error-message" role="alert">{error}</div> : !word ? <div className="loading" role="status">正在准备词表…</div> : <>
        <div className={`workspace${resizing ? ' is-resizing' : ''}`} id="workspace" ref={workspace} aria-busy="false" style={{ '--list-columns': `${layout.width}fr`, '--word-columns': `${100 - layout.width}fr` }}>
          <WordList words={lesson.words} view={view} onSelect={controller.start} layout={layout} />
          <div className="split-handle" role="separator" aria-label="调整左侧列表宽度" aria-orientation="vertical" aria-valuemin="30" aria-valuemax="75" aria-valuenow={Math.round(layout.width)} tabIndex="0" title="拖动调整列表宽度"
            onPointerDown={event => { dragging.current = true; setResizing(true); event.currentTarget.setPointerCapture(event.pointerId); }}
            onPointerMove={event => {
              if (!dragging.current) return;
              const bounds = workspace.current.getBoundingClientRect();
              layout.setWidth((event.clientX - bounds.left) / bounds.width * 100);
            }}
            onPointerUp={event => { dragging.current = false; setResizing(false); if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }}
            onLostPointerCapture={() => { dragging.current = false; setResizing(false); }}
            onPointerCancel={() => { dragging.current = false; setResizing(false); }}
            onKeyDown={event => {
              if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.code)) {
                event.preventDefault(); event.stopPropagation();
                layout.setWidth(event.code === 'Home' ? 30 : event.code === 'End' ? 75 : layout.width + (event.code === 'ArrowRight' ? 2 : -2));
              }
            }}><span aria-hidden="true">⋮</span></div>
          <section className="practice" aria-label="当前单词">
            <div className="practice-top"><span id="counter">{String(view.index + 1).padStart(2, '0')} <span>/ {lesson.words.length}</span></span><span id="state-label" className={`state-label${view.state === 'gap' ? ' is-gap' : ''}`} role="status" aria-live="polite">{status(view)}</span></div>
            <div className="word-stage">
              <CurrentWord word={word.word} highlighted={view.highlighted} />
              <p id="phonetic" className="phonetic" lang="en">{word.phonetic}</p>
              <p className="translation"><span id="pos">{word.pos}</span><span id="meaning">{word.meaning}</span></p>
              {view.state === 'error' && <p id="status-detail" className="status-detail" role="alert">{view.error}</p>}
            </div>
            <div className="lesson-progress" role="progressbar" aria-label="课程进度" aria-valuemin="0" aria-valuemax={lesson.words.length} aria-valuenow={progress}><span id="progress-fill" style={{ width: `${progress / lesson.words.length * 100}%` }} /></div>
          </section>
        </div>
        <PlayerControls lesson={lesson} controller={controller} layout={layout} />
      </>}
    </main>
  </div>;
}
