import json, glob, os, sys
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
sys.path.insert(0, os.environ['T'])
from measure import measure
model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=1,
                     download_root=os.environ['T'] + '/home/.cache/read-alone/whisper', local_files_only=True)
out = []
for f in sorted(glob.glob(os.environ['T'] + '/stage-public/audio/book2/lesson-65/*-teacher-*.wav')):
    if f.endswith('meaning.wav'): continue
    a, sr = sf.read(f, dtype='float32')
    x = np.interp(np.arange(round(len(a) * 16000 / sr)) / 16000, np.arange(len(a)) / sr, a).astype('float32')
    segs, _ = model.transcribe(x, language='en', beam_size=3, vad_filter=False, condition_on_previous_text=False)
    m = measure(f); m.pop('f0_track', None)
    r = {'file': os.path.basename(f), 'asr': ' '.join(s.text.strip() for s in segs), 'dur': m['dur'], 'segments': m['segments'],
         'fall_st': m.get('fall_st'), 'tail8_st': m.get('tail8_st'), 'peak': round(float(np.abs(a).max()), 3)}
    out.append(r); print(json.dumps(r, ensure_ascii=False))
json.dump(out, open(os.environ['T'] + '/raw-final/final-english-check.json', 'w'), ensure_ascii=False, indent=1)
