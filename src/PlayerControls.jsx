import { useEffect, useRef, useState } from 'react';

const asset = path => `${import.meta.env.BASE_URL}${path}`;

export default function PlayerControls({ lesson, controller, layout }) {
  const { view, update } = controller;
  const { settings } = view;
  const previousVolume = useRef(settings.volume || .7);
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement));
  const [fullscreenFailed, setFullscreenFailed] = useState(false);

  useEffect(() => {
    const changed = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener('fullscreenchange', changed);
    return () => document.removeEventListener('fullscreenchange', changed);
  }, []);

  const fullscreen = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch { setFullscreenFailed(true); }
  };
  const volume = value => {
    if (value > 0) previousVolume.current = value;
    update({ volume: value });
  };
  const mute = () => {
    if (settings.volume > 0) { previousVolume.current = settings.volume; update({ volume: 0 }); }
    else update({ volume: previousVolume.current });
  };
  const label = view.active ? '暂停' : view.state === 'paused' ? '继续跟读' : view.state === 'complete' ? '再读一遍' : view.state === 'error' ? '重新播放' : '开始跟读';

  return <section className="control-bar" aria-label="播放控制">
    <div className="transport">
      <button type="button" id="previous" aria-label="上一个单词" disabled={view.index === 0} onClick={controller.previous}>上一词</button>
      <button type="button" className="play-button" id="play" onClick={controller.toggle}><span id="play-icon" aria-hidden="true">{view.active ? 'Ⅱ' : '▶'}</span><span id="play-label">{label}</span></button>
      <button type="button" id="next" aria-label="下一个单词" disabled={view.index === lesson.words.length - 1} onClick={controller.next}>下一词</button>
      <button type="button" id="replay" onClick={controller.replay}>重读</button>
    </div>
    <div className="volume-control">
      <label htmlFor="volume">音量</label>
      <input type="range" id="volume" min="0" max="100" value={Math.round(settings.volume * 100)} aria-label="音量" onChange={event => volume(Number(event.target.value) / 100)} />
      <output id="volume-value" htmlFor="volume">{Math.round(settings.volume * 100)}%</output>
      <button type="button" id="mute" aria-label={settings.volume ? '静音' : '恢复声音'} aria-pressed={settings.volume === 0} onClick={mute}>{settings.volume ? '静音' : '恢复声音'}</button>
    </div>
    <button type="button" id="fullscreen" onClick={fullscreen}>{fullscreenFailed ? '浏览器全屏' : isFullscreen ? '退出全屏' : '全屏'}</button>
    <details className="settings-menu"><summary>设置</summary>
      <section className="settings" aria-label="播放设置">
        <div className="setting"><label htmlFor="list-width">左侧列表宽度 <output htmlFor="list-width">{Math.round(layout.width)}%</output></label><input id="list-width" type="range" min="30" max="75" value={Math.round(layout.width)} aria-label="左侧列表宽度百分比" onChange={event => layout.setWidth(Number(event.target.value))} /></div>
        <div className="setting"><label htmlFor="speed">英文播放速度</label><select id="speed" value={settings.speed} onChange={event => update({ speed: Number(event.target.value) })}><option value="0.6">0.6×</option><option value="0.75">0.75×</option><option value="0.85">0.85×</option><option value="1">1.0×</option></select></div>
        <div className="setting"><label htmlFor="gap">跟读留白 <output id="gap-value" htmlFor="gap">{settings.gap.toFixed(1)} 秒</output></label><input type="range" id="gap" min="1" max="5" step="0.1" value={settings.gap} aria-label="跟读留白秒数" onChange={event => update({ gap: Number(event.target.value) })} /></div>
        <label className="check-setting"><input type="checkbox" id="read-meaning" checked={settings.readMeaning} onChange={event => update({ readMeaning: event.target.checked })} /><span>朗读中文释义</span></label>
        <label className="check-setting"><input type="checkbox" id="loop" checked={settings.loop} onChange={event => update({ loop: event.target.checked })} /><span>整课循环</span></label>
        <span className="voice-tag">{lesson.voice_labels.english} · {lesson.voice_labels.chinese}</span>
        <a href={asset(`audio/book2/lesson-${lesson.lesson}/lesson-${lesson.lesson}-full.wav`)} download={`新概念第二册第${lesson.lesson}课.wav`}>下载整课音频</a>
        <a className="license-link" href={asset('THIRD_PARTY_NOTICES.txt')}>AI 合成语音与许可</a>
      </section>
    </details>
  </section>;
}
