#!/usr/bin/env python3
"""Generate lesson audio with the Lesson 57 reference voice on Apple Silicon."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
MODEL = 'mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit'
PARTS = {'n.': '名词', 'v.': '动词', 'adj.': '形容词'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', type=int, default=63)
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--raw-dir', type=Path)
    parser.add_argument('--trim-json', type=Path, help='English word time ranges in raw recordings')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--synthesize-only', action='store_true')
    mode.add_argument('--finalize-only', action='store_true')
    args = parser.parse_args()

    import numpy as np
    import soundfile as sf

    raw_dir = args.raw_dir or Path.home() / f'.cache/read-alone/voice-clone/book2-{args.lesson}'
    raw_dir.mkdir(parents=True, exist_ok=True)
    entries = [w for w in json.loads((ROOT / 'words/nce_words.json').read_text())
               if w['book'] == 2 and w['lesson_seq'] == args.lesson]
    if not entries:
        raise SystemExit('No words for this lesson')
    references = {
        'en': {'file': 'audio/reference/lesson-57/15-english-full-sentence.wav',
               'text': 'The assistant who served her did not like the way she was dressed.'},
        'zh': {'file': 'audio/reference/lesson-57/01-chinese-reference.wav',
               'text': '就是服务行业里的服务员啊，或者说店员啊，他们会说的一句话。我能帮你吗？你要买什么呢？我给你看，我帮你去推荐。'},
    }
    for ref in references.values():
        ref['sha256'] = sha(PUBLIC / ref['file'])
    requests = []
    for number, word in enumerate(entries, 1):
        slug = re.sub(r'[^a-z0-9]+', '-', word['word'].lower()).strip('-')
        prefix = f'{number:02d}-{slug}'
        # Part-of-speech context disambiguates close; extract only the final word.
        part = {'n.': 'noun', 'v.': 'verb', 'adj.': 'adjective'}.get(word['pos'], 'word')
        english = f"The {part}: {word['word']}."
        if word['word'] == 'reception':
            english = 'reception.'
        for lang, text in [('en', english), ('zh', f"{PARTS.get(word['pos'], word['pos'])}，{word['meaning']}。")]:
            requests.append({'file': f'{prefix}-{lang}-raw.wav', 'word': word['word'], 'language': lang, 'text': text})
    job = {'model': MODEL, 'references': references, 'requests': requests}
    job_path = raw_dir / 'raw-generation.json'
    previous = json.loads(job_path.read_text()) if job_path.exists() else None
    if previous and previous != job:
        raise SystemExit('Raw cache belongs to different inputs; choose another --raw-dir')
    if not args.finalize_only:
        import mlx.core as mx
        from mlx_audio.tts.utils import load_model
        write_json(job_path, job)
        print('Loading voice clone model', args.model, flush=True)
        model = load_model(args.model)
        for number, request in enumerate(requests):
            target = raw_dir / request['file']
            if target.exists():
                print('Reusing', target.name, flush=True)
                continue
            ref = references[request['language']]
            mx.random.seed(6300 + number)
            results = list(model.generate(
                text=request['text'], lang_code='English' if request['language'] == 'en' else 'Chinese',
                ref_audio=str(PUBLIC / ref['file']), ref_text=ref['text'],
                temperature=0.65, top_p=0.9, max_tokens=192, verbose=False,
            ))
            samples = np.concatenate([np.asarray(result.audio) for result in results])
            if not np.isfinite(samples).all() or len(samples) < model.sample_rate * .15:
                raise RuntimeError(f'Invalid synthesized clip: {target.name}')
            temporary = target.with_suffix('.tmp.wav')
            sf.write(temporary, samples, model.sample_rate, subtype='PCM_16')
            temporary.replace(target)
            print('Synthesized', target.name, round(len(samples) / model.sample_rate, 3), 'seconds', flush=True)
            mx.clear_cache()
        if args.synthesize_only:
            return
    if not job_path.exists() or json.loads(job_path.read_text()) != job:
        raise SystemExit('Missing matching synthesis manifest')
    trims = json.loads(args.trim_json.read_text()) if args.trim_json else {}
    missing = [w['word'] for w in entries if w['word'] not in trims]
    if missing:
        raise SystemExit('Provide --trim-json with target word intervals: ' + ', '.join(missing))
    import imageio_ffmpeg
    from generate_audio import build_full_audio
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output = PUBLIC / 'audio/book2' / f'lesson-{args.lesson}'
    output.mkdir(parents=True, exist_ok=True)
    clips = []
    words = []
    for number, word in enumerate(entries):
        english, chinese = requests[number * 2:number * 2 + 2]
        prefix = english['file'].removesuffix('-en-raw.wav')
        audio = {}
        for kind, request, speed in [('slow', english, .72), ('normal', english, .86), ('meaning', chinese, 1.0)]:
            raw_path = raw_dir / request['file']
            samples, rate = sf.read(raw_path, dtype='float32')
            interval = trims.get(word['word']) if kind != 'meaning' else None
            if interval:
                start, end = interval
                if not 0 <= start < end <= len(samples) / rate:
                    raise ValueError(f'Invalid trim for {word["word"]}')
                samples = samples[round(start * rate):round(end * rate)]
            # Retain 90 ms around speech and pad the onset to protect initial consonants.
            frame = max(1, round(rate * .01))
            rms = np.sqrt(np.mean(samples[:len(samples) // frame * frame].reshape(-1, frame) ** 2, axis=1))
            active = np.flatnonzero(rms > max(float(np.max(rms)) * .025, .0005))
            if not len(active):
                raise RuntimeError(f'Silent clip: {raw_path.name}')
            start = max(0, int(active[0]) * frame - round(rate * .09))
            end = min(len(samples), (int(active[-1]) + 1) * frame + round(rate * .12))
            samples = samples[start:end]
            peak = float(np.max(np.abs(samples)))
            samples *= min(.82 / peak, 5)
            fade = min(round(rate * .004), len(samples) // 4)
            samples[:fade] *= np.linspace(0, 1, fade)
            samples[-fade:] *= np.linspace(1, 0, fade)
            samples = np.pad(samples, (round(rate * .08), round(rate * .12)))
            temporary = raw_dir / 'processed.wav'
            sf.write(temporary, samples, rate, subtype='PCM_16')
            target = output / f'{prefix}-teacher-{kind}.wav'
            result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(temporary),
                                     '-af', f'atempo={speed}', '-ac', '1', '-ar', '24000', '-c:a', 'pcm_s16le', str(target)],
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
            final, sr = sf.read(target)
            if sr != 24000 or not np.isfinite(final).all() or np.max(np.abs(final)) >= .999:
                raise RuntimeError(f'Invalid final clip: {target.name}')
            relative = target.relative_to(PUBLIC).as_posix()
            audio[kind] = relative
            clips.append({'file': relative, 'text': word['word'] if kind != 'meaning' else request['text'],
                          'voice': 'lesson-57-teacher', 'language': request['language'], 'speed': speed,
                          'duration': round(len(final) / sr, 3), 'sha256': sha(target),
                          'synthesis_text': request['text'], 'raw_sha256': sha(raw_path), 'word_interval': interval})
        words.append({'id': f'book2-{args.lesson}-{number + 1:02d}', **{k: word[k] for k in ['word', 'phonetic', 'pos', 'meaning']}, 'audio': audio})
    lesson = {'book': 2, 'lesson': args.lesson, 'title': 'She was not amused' if args.lesson == 63 else '单词跟读',
              'voices': {'english': 'lesson-57-teacher', 'chinese': 'lesson-57-teacher'},
              'voice_labels': {'english': '老师音色慢读', 'chinese': '老师音色普通话'},
              'model': MODEL, 'words': words}
    full = build_full_audio(lesson)
    manifest = {**job, 'license': 'Apache-2.0 (model); MIT (MLX Audio)', 'runtime': 'mlx-audio==0.6.3',
                'processing': {'english_speeds': [.72, .86], 'preserve_pitch': True, 'gap_seconds': 2.2, 'edge_fade_seconds': .004},
                'clips': clips, 'full_audio': {'file': full.relative_to(PUBLIC).as_posix(), 'sha256': sha(full)}}
    write_json(output / 'generation.json', manifest)
    write_json(PUBLIC / 'data/book2' / f'lesson-{args.lesson}.json', lesson)
    print('Saved', len(clips), 'clips and', full, flush=True)


if __name__ == '__main__':
    main()
