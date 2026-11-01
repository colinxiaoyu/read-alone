#!/usr/bin/env python3
"""Validate a lesson's WAVs, hashes, references and full playback sequence."""

import argparse
import hashlib
import json
from pathlib import Path
import wave

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', type=int, required=True)
    parser.add_argument('--public-dir', type=Path, default=ROOT / 'public')
    parser.add_argument('--compare-approved', type=Path, help='Compare every recording to an approved generation.json')
    args = parser.parse_args()
    public = args.public_dir
    lesson = json.loads((public / f'data/book2/lesson-{args.lesson}.json').read_text())
    manifest = json.loads((public / f'audio/book2/lesson-{args.lesson}/generation.json').read_text())
    entries = [w for w in json.loads((ROOT / 'words/nce_words.json').read_text())
               if w['book'] == 2 and w['lesson_seq'] == args.lesson]
    assert entries and len(lesson['words']) == len(entries), 'Lesson word count differs'
    clips = {clip['file']: clip for clip in manifest['clips']}
    assert len(clips) == len(entries) * 3, 'Clip count differs'
    for ref in manifest['references'].values():
        assert digest(ROOT / 'public' / ref['file']) == ref['sha256'], 'Reference differs'
    audio = {}
    for word, source in zip(lesson['words'], entries):
        for field in ['word', 'phonetic', 'pos', 'meaning']:
            assert word[field] == source[field], f'Word data differs: {field}'
        assert set(word['audio']) == {'slow', 'normal', 'meaning'}
        for path in word['audio'].values():
            file = public / path
            assert digest(file) == clips[path]['sha256'], f'Checksum differs: {path}'
            with wave.open(str(file), 'rb') as wav:
                assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 24000)
                assert wav.getnframes() >= 2400, f'Clip too short: {path}'
                assert abs(wav.getnframes() / 24000 - clips[path]['duration']) <= .001
                audio[path] = wav.readframes(wav.getnframes())
        assert len(audio[word['audio']['slow']]) > len(audio[word['audio']['normal']])
    gap = b'\0\0' * int(24000 * manifest['processing']['gap_seconds'])
    expected = b''.join(piece for w in lesson['words'] for piece in
                        [audio[w['audio']['slow']], audio[w['audio']['meaning']], gap,
                         audio[w['audio']['normal']], gap])
    full_record = manifest['full_audio']
    full = public / full_record['file']
    assert digest(full) == full_record['sha256'], 'Full recording checksum differs'
    with wave.open(str(full), 'rb') as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 24000)
        assert wav.readframes(wav.getnframes()) == expected, 'Playback order or gaps differ'
        duration = wav.getnframes() / 24000
    if args.compare_approved:
        approved = json.loads(args.compare_approved.read_text())
        assert {c['file']: c['sha256'] for c in approved['clips']} == {k: v['sha256'] for k, v in clips.items()}, 'Approved clips differ'
        assert approved['full_audio']['sha256'] == full_record['sha256'], 'Approved full recording differs'
    print(json.dumps({'lesson': args.lesson, 'words': len(entries), 'clips': len(clips),
                      'duration_seconds': duration, 'format': '24 kHz mono PCM16',
                      'hashes_and_playback_sequence': 'verified', 'approved_audio_identical': bool(args.compare_approved)}))


if __name__ == '__main__':
    main()
