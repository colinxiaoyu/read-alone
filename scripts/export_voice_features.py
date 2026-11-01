#!/usr/bin/env python3
"""Save model-specific speaker features from the retained reference WAVs."""

import argparse
import importlib.metadata
import json
from pathlib import Path

from generate_cloned_audio import ROOT, PUBLIC, sha, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, default=ROOT / 'voices/lesson-57-teacher/profile.json')
    parser.add_argument('--model', required=True, help='The matching local Qwen3-TTS model directory')
    args = parser.parse_args()
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    profile = json.loads(args.profile.read_text())
    model_dir = Path(args.model)
    for name, expected in profile['model']['weights_sha256'].items():
        import hashlib
        digest = hashlib.sha256()
        with (model_dir / name).open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise RuntimeError(f'Model checksum differs: {name}')
    model = load_model(str(model_dir))
    features = {}
    for lang, ref in profile['references'].items():
        path = PUBLIC / ref['file']
        if sha(path) != ref['sha256']:
            raise RuntimeError(f'Reference checksum differs: {path}')
        audio, rate = sf.read(path, dtype='float32')
        if rate != 24000 or audio.ndim != 1:
            raise RuntimeError(f'Expected mono 24 kHz reference: {path}')
        embedding = model.extract_speaker_embedding(mx.array(audio), sr=rate)
        mx.eval(embedding)
        vector = np.asarray(embedding, dtype=np.float32)
        if not np.isfinite(vector).all() or not float(np.linalg.norm(vector)):
            raise RuntimeError(f'Invalid embedding: {lang}')
        features[lang] = vector
    target = ROOT / profile['feature_files']['speaker_embeddings']
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, **features)
    metadata = {'voice_id': profile['id'], 'model': profile['model'], 'artifact_type': 'speaker_embeddings',
                'reference_inputs': profile['references'], 'model_specific': True,
                'file': target.relative_to(ROOT).as_posix(), 'sha256': sha(target),
                'vectors': {k: {'shape': list(v.shape), 'dtype': str(v.dtype), 'l2_norm': float(np.linalg.norm(v))}
                            for k, v in features.items()},
                'runtime': {name: importlib.metadata.version(name) for name in ['mlx-audio', 'mlx', 'numpy', 'soundfile']}}
    write_json(ROOT / profile['feature_files']['metadata'], metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
