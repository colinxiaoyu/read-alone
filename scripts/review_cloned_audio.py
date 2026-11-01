#!/usr/bin/env python3
"""Transcribe cloned lesson clips and suggest English extraction intervals."""

import argparse
import json
from pathlib import Path
import re

from generate_cloned_audio import ROOT, write_json


def tokens(text):
    return re.findall(r'[a-z]+', text.lower())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', type=int, required=True)
    parser.add_argument('--mode', choices=['raw', 'final'], required=True)
    parser.add_argument('--raw-dir', type=Path)
    parser.add_argument('--public-dir', type=Path, default=ROOT / 'public')
    parser.add_argument('--language', choices=['en', 'zh', 'all'], default='all')
    parser.add_argument('--only', help='Review a single vocabulary item')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--asr-model', default='small')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    import numpy as np
    import soundfile as sf
    from faster_whisper import WhisperModel

    if args.mode == 'raw':
        if not args.raw_dir:
            parser.error('--raw-dir is required for raw review')
        manifest = json.loads((args.raw_dir / 'raw-generation.json').read_text())
        requests = [{**r, 'path': args.raw_dir / r['file'], 'expected': r['text']} for r in manifest['requests']]
    else:
        lesson = json.loads((args.public_dir / f'data/book2/lesson-{args.lesson}.json').read_text())
        manifest = json.loads((args.public_dir / f'audio/book2/lesson-{args.lesson}/generation.json').read_text())
        records = {r['file']: r for r in manifest['clips']}
        requests = [{'word': w['word'], 'file': w['audio'][kind], 'path': args.public_dir / w['audio'][kind],
                     'language': lang, 'expected': records[w['audio'][kind]]['text']}
                    for w in lesson['words'] for kind, lang in [('slow', 'en'), ('meaning', 'zh')]]
    requests = [r for r in requests if (not args.only or r['word'] == args.only)
                and (args.language == 'all' or r['language'] == args.language)]
    if not requests:
        raise SystemExit('No matching recordings')
    model = WhisperModel(args.asr_model, device='cpu', compute_type='int8', cpu_threads=1,
                         download_root=str(Path.home() / '.cache/read-alone/whisper'), local_files_only=args.offline)
    report = {'lesson': args.lesson, 'mode': args.mode, 'method': f'faster-whisper-{args.asr_model}',
              'interval_status': 'suggestions_require_boundary_review', 'clips': [], 'suggested_trims': {}}
    failed = False
    for request in requests:
        audio, rate = sf.read(request['path'], dtype='float32')
        if audio.ndim != 1:
            raise RuntimeError('Expected a mono WAV')
        duration = len(audio) / rate
        x = np.interp(np.arange(round(len(audio) * 16000 / rate)) / 16000,
                      np.arange(len(audio)) / rate, audio).astype('float32')
        segments, _ = model.transcribe(x, language=request['language'], beam_size=3, word_timestamps=True,
                                      vad_filter=False, condition_on_previous_text=False)
        segments = list(segments)
        text = ' '.join(s.text.strip() for s in segments)
        words = [{'word': w.word, 'start': w.start, 'end': w.end, 'probability': w.probability}
                 for s in segments for w in (s.words or [])]
        record = {'file': request['file'], 'word': request['word'], 'language': request['language'],
                  'expected': request['expected'], 'recognized': text, 'word_timestamps': words}
        if request['language'] == 'en':
            if args.mode == 'final':
                record['matches'] = tokens(text) == tokens(request['word'])
                failed |= not record['matches']
            elif tokens(request['expected']) == tokens(request['word']):
                report['suggested_trims'][request['word']] = [0, round(duration, 6)]
            else:
                target = tokens(request['word'])
                flat = [(t, w) for w in words for t in tokens(w['word'])]
                matches = [i for i in range(len(flat) - len(target) + 1)
                           if [t for t, _ in flat[i:i + len(target)]] == target]
                if matches:
                    i = matches[-1]
                    start = flat[i][1]['start']
                    end = flat[i + len(target) - 1][1]['end']
                    previous_end = flat[i - 1][1]['end'] if i else 0
                    frame = max(1, round(rate * .01))
                    rms = np.sqrt(np.mean(audio[:len(audio) // frame * frame].reshape(-1, frame) ** 2, axis=1))
                    quiet = rms < .001
                    gaps = []
                    begin = None
                    for n, silent in enumerate(list(quiet) + [False]):
                        if silent and begin is None:
                            begin = n
                        if not silent and begin is not None:
                            a, b = begin * .01, n * .01
                            if b - a >= .12 and a >= previous_end - .15 and b <= end - .15:
                                gaps.append((a + b) / 2)
                            begin = None
                    if gaps:
                        start = min(gaps, key=lambda mid: abs(mid - start))
                    report['suggested_trims'][request['word']] = [round(start, 6), round(duration, 6)]
                else:
                    record['target_found'] = False
        report['clips'].append(record)
        write_json(args.output, report)
        print(json.dumps({k: v for k, v in record.items() if k != 'word_timestamps'}, ensure_ascii=False), flush=True)
    if failed:
        raise SystemExit('English review found extra or mismatched words; inspect before publishing')


if __name__ == '__main__':
    main()
