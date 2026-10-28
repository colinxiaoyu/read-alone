#!/usr/bin/env python3
"""Generate the bilingual lesson locally with Piper English and Kokoro Mandarin. Requires Python 3.10-3.12."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


def download(cache, name, url=None):
    target = cache / name
    if not target.exists():
        print("Downloading", name, flush=True)
        temporary = target.with_suffix(target.suffix + ".part")
        urllib.request.urlretrieve(url or MODEL_URL + name, temporary)
        temporary.replace(target)
    return target


def build_full_audio(lesson):
    sequence = []
    for word in lesson["words"]:
        sequence.extend([word["audio"]["slow"], word["audio"]["meaning"], None, word["audio"]["normal"], None])
    target = PUBLIC / "audio/book2" / f"lesson-{lesson['lesson']}" / f"lesson-{lesson['lesson']}-full.wav"
    temporary = target.with_suffix(".tmp.wav")
    with wave.open(str(temporary), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        for clip in sequence:
            if clip is None:
                output.writeframes(b"\0\0" * int(24000 * 2.2))
            else:
                with wave.open(str(PUBLIC / clip), "rb") as source:
                    output.writeframes(source.readframes(source.getnframes()))
    temporary.replace(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", type=int, default=62)
    parser.add_argument("--english-voice", default="en_GB-cori-high", choices=["en_GB-cori-high"])
    parser.add_argument("--chinese-voice", default="zf_001")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--chinese-only", action="store_true", help="Replace Chinese clips and reuse existing English audio")
    mode.add_argument("--english-only", action="store_true", help="Replace English clips and reuse existing Chinese audio")
    parser.add_argument("--slow-speed", type=float, default=0.35)
    parser.add_argument("--normal-speed", type=float, default=0.45)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/read-alone/kokoro")
    args = parser.parse_args()

    import numpy as np
    import onnxruntime as rt
    import soundfile as sf
    from kokoro_onnx import Kokoro
    from misaki import zh
    from piper import PiperVoice, SynthesisConfig

    args.cache.mkdir(parents=True, exist_ok=True)
    options = rt.SessionOptions()
    options.intra_op_num_threads = min(4, os.cpu_count() or 1)
    options.inter_op_num_threads = 1
    def load_engine(model, voices, vocab=None):
        session = rt.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
        return Kokoro.from_session(session, str(voices), vocab_config=str(vocab) if vocab else None)

    english_tts = None
    if not args.chinese_only:
        piper_cache = args.cache.parent / "piper"
        piper_cache.mkdir(parents=True, exist_ok=True)
        piper_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/"
        english_model = download(piper_cache, "en_GB-cori-high.onnx", piper_url + "en_GB-cori-high.onnx")
        download(piper_cache, "en_GB-cori-high.onnx.json", piper_url + "en_GB-cori-high.onnx.json")
        english_tts = PiperVoice.load(english_model)
    chinese_tts = None
    chinese = None
    if not args.english_only:
        chinese_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/"
        chinese_model = download(args.cache, "kokoro-v1.1-zh.onnx", chinese_url + "kokoro-v1.1-zh.onnx")
        chinese_voices = download(args.cache, "voices-v1.1-zh.bin", chinese_url + "voices-v1.1-zh.bin")
        chinese_vocab = download(args.cache, "config-v1.1-zh.json", "https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh/resolve/main/config.json")
        chinese_tts = load_engine(chinese_model, chinese_voices, chinese_vocab)
        chinese = zh.ZHG2P(version="1.1")
    raw = json.loads((ROOT / "words/nce_words.json").read_text())
    entries = [v for v in raw if v["book"] == 2 and v["lesson_seq"] == args.lesson]
    if not entries:
        raise SystemExit("No entries for this lesson")
    output = PUBLIC / "audio/book2" / f"lesson-{args.lesson}"
    output.mkdir(parents=True, exist_ok=True)
    old_manifest_path = output / "generation.json"
    old_manifest = json.loads(old_manifest_path.read_text()) if old_manifest_path.exists() else {"clips": []}
    old_clips = {clip["file"]: clip for clip in old_manifest["clips"]}
    clips = []

    def synthesize(name, text, voice, speed, phonemes=None):
        destination = output / name
        relative = destination.relative_to(PUBLIC).as_posix()
        if (args.chinese_only and not voice.startswith("z")) or (args.english_only and voice.startswith("z")):
            record = old_clips.get(relative)
            if not record or record["voice"] != voice or not destination.is_file():
                raise RuntimeError(f"No matching recording to reuse: {name}")
            if hashlib.sha256(destination.read_bytes()).hexdigest() != record["sha256"]:
                raise RuntimeError(f"Recording checksum differs: {name}")
            clips.append(record)
            return relative
        if phonemes is None and voice.startswith("z"):
            converted = chinese(text)
            phonemes = converted[0] if isinstance(converted, tuple) else converted
        if voice.startswith("z"):
            samples, rate = chinese_tts.create(phonemes, voice=voice, speed=speed, is_phonemes=True)
        else:
            config = SynthesisConfig(speaker_id=None, length_scale=1 / speed,
                                     noise_scale=0.3, noise_w_scale=0.3, normalize_audio=False)
            input_phonemes = list(phonemes) if phonemes else english_tts.phonemize(text)[0]
            phonemes = "".join(input_phonemes)
            ids = english_tts.phonemes_to_ids(input_phonemes)
            samples = english_tts.phoneme_ids_to_audio(ids, config)
            if isinstance(samples, tuple):
                samples = samples[0]
            source_rate = english_tts.config.sample_rate
            rate = 24000
            samples = np.interp(np.arange(int(len(samples) * rate / source_rate)) / rate,
                                np.arange(len(samples)) / source_rate, samples)
        samples = np.asarray(samples, dtype=np.float32)
        if not np.isfinite(samples).all() or len(samples) < rate * 0.12:
            raise RuntimeError(f"Invalid generated audio: {name}")
        peak = float(np.max(np.abs(samples)))
        if peak < 0.001:
            raise RuntimeError(f"Silent generated audio: {name}")
        samples *= min(0.90 / peak, 2.5)
        temporary = destination.with_suffix(".tmp.wav")
        sf.write(temporary, samples, rate, subtype="PCM_16")
        temporary.replace(destination)
        record = {"file": destination.relative_to(PUBLIC).as_posix(), "text": text,
                  "voice": voice, "speed": speed, "phonemes": phonemes, "duration": round(len(samples) / rate, 3),
                  "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
        clips.append(record)
        print(f"Generated {name}: {record['duration']}s", flush=True)
        return record["file"]

    words = []
    parts = {"n.": "名词", "v.": "动词", "adj.": "形容词", "adv.": "副词", "prep.": "介词"}
    for number, item in enumerate(entries, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", item["word"].lower()).strip("-")
        prefix = f"{number:02d}-{slug}"
        # The adjective desolate ends in /ət/; its verb ends in /eɪt/.
        override = "dˈɛsələt" if item["word"] == "desolate" and item["pos"] == "adj." else None
        english = item["word"].replace("-", " ")
        chinese_text = f"{parts.get(item['pos'], item['pos'])}，{item['meaning']}。"
        slow_tag = f"{args.slow_speed:.2f}".replace(".", "")
        normal_tag = f"{args.normal_speed:.2f}".replace(".", "")
        audio = {
            "slow": synthesize(prefix + f"-en-cori-slow-{slow_tag}.wav", english, args.english_voice, args.slow_speed, override),
            "normal": synthesize(prefix + f"-en-cori-normal-{normal_tag}.wav", english, args.english_voice, args.normal_speed, override),
            "meaning": synthesize(prefix + f"-zh-{args.chinese_voice}.wav", chinese_text, args.chinese_voice, 1.0),
        }
        words.append({"id": f"book2-{args.lesson}-{number:02d}", "word": item["word"],
                      "phonetic": item["phonetic"], "pos": item["pos"], "meaning": item["meaning"],
                      "audio": audio})

    result = {"book": 2, "lesson": args.lesson, "title": "After the fire" if args.lesson == 62 else "单词跟读",
              "voices": {"english": args.english_voice, "chinese": args.chinese_voice},
              "voice_labels": {"english": "英音慢读", "chinese": "普通话女声"},
              "model": "Piper Cori English / Kokoro-82M v1.1-zh Mandarin", "words": words}
    target = PUBLIC / "data/book2" / f"lesson-{args.lesson}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(target)
    manifest = {"model": result["model"], "license": {"english_model": "MIT", "english_dataset": "Public domain", "chinese_model": "Apache-2.0"},
                "model_source": {"english": "https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/vctk/medium", "chinese": "https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh"},
                "runtime": {"english": "piper-tts", "chinese": "kokoro-onnx"}, "voices": result["voices"], "clips": clips}
    (output / "generation.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    build_full_audio(result)
    current_files = {clip["file"] for clip in clips}
    for old in old_manifest["clips"]:
        obsolete = PUBLIC / old["file"]
        if old["file"] not in current_files and obsolete.parent == output:
            obsolete.unlink(missing_ok=True)
    print("Saved", target, flush=True)


if __name__ == "__main__":
    main()
