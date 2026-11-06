import json
import re
import sys
from pathlib import Path

import numpy as np
import parselmouth
import soundfile as sf
from faster_whisper import WhisperModel

FRAME = .01


def tokens(text):
    return re.findall(r'[a-z]+', text.lower())


def segments(rms, threshold, min_gap):
    active = rms > threshold
    segs = []
    begin = None
    for n, a in enumerate(list(active) + [False]):
        if a and begin is None:
            begin = n
        if not a and begin is not None:
            segs.append([begin, n])
            begin = None
    merged = []
    for s in segs:
        if merged and (s[0] - merged[-1][1]) * FRAME < min_gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return merged


def pitch(audio, rate, a, b):
    snd = parselmouth.Sound(audio[round(a * rate):round(b * rate)].astype('float64'), rate)
    p = snd.to_pitch_ac(time_step=.01, pitch_floor=100, pitch_ceiling=600, octave_jump_cost=.7)
    f = p.selected_array['frequency']
    t = p.xs() + a
    voiced = [(round(float(x), 2), float(y)) for x, y in zip(t, f) if y > 0]
    if len(voiced) < 4:
        return {'voiced_frames': len(voiced)}
    vals = np.array([v for _, v in voiced])
    peak = int(np.argmax(vals))
    tail = float(np.median(vals[-3:]))
    last = vals[-8:]
    return {'peak_hz': round(float(vals[peak]), 1), 'peak_t': voiced[peak][0], 'tail_hz': round(tail, 1),
            'drop_st': round(12 * np.log2(vals[peak] / tail), 2),
            'tail_delta_st': round(12 * np.log2(last[-1] / last[0]), 2)}


def main():
    model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=1,
                         download_root=str(Path.home() / '.cache/read-alone/whisper'), local_files_only=True)
    out = []
    raw = Path(sys.argv[1])
    reqs = [r for r in json.loads((raw / 'raw-generation.json').read_text())['requests'] if r['language'] == 'en']
    for r in reqs:
        path, word = str(raw / r['file']), r['word']
        audio, rate = sf.read(path, dtype='float32')
        dur = len(audio) / rate
        frame = round(rate * FRAME)
        rms = np.sqrt(np.mean(audio[:len(audio) // frame * frame].reshape(-1, frame) ** 2, axis=1))
        peak = float(rms.max())
        segs = segments(rms, peak * .025, .15)
        quiet = segments(rms, peak * .005, .0)
        x = np.interp(np.arange(round(len(audio) * 16000 / rate)) / 16000, np.arange(len(audio)) / rate, audio).astype('float32')
        segs_asr, _ = model.transcribe(x, language='en', beam_size=3, word_timestamps=True,
                                       vad_filter=False, condition_on_previous_text=False)
        segs_asr = list(segs_asr)
        text = ' '.join(s.text.strip() for s in segs_asr)
        main_seg = max(segs, key=lambda s: rms[s[0]:s[1]].sum())
        leading = [s for s in segs if s[1] <= main_seg[0]]
        onset = main_seg[0] * FRAME
        prior_quiet_end = max([q[1] * FRAME for q in quiet if q[1] <= main_seg[0]] or [0])
        out.append({
            'file': Path(path).name, 'word': word, 'duration': round(dur, 3), 'asr': text,
            'asr_strict': tokens(text) == tokens(word) and '?' not in text and '？' not in text,
            'segments_2.5pct': [[round(a * FRAME, 2), round(b * FRAME, 2)] for a, b in segs],
            'segments_0.5pct': [[round(a * FRAME, 2), round(b * FRAME, 2)] for a, b in quiet],
            'leading_blips': [[round(a * FRAME, 2), round(b * FRAME, 2)] for a, b in leading],
            'main_onset': round(onset, 2), 'main_end': round(main_seg[1] * FRAME, 2),
            'pitch': pitch(audio, rate, onset, main_seg[1] * FRAME),
            'clip_peak': round(float(np.abs(audio).max()), 3),
        })
        print(json.dumps(out[-1], ensure_ascii=False), flush=True)
    (raw / 'analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
