import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel

def tokens(t): return re.findall(r'[a-z]+', t.lower())
pub = Path(sys.argv[1]); lesson = int(sys.argv[2])
data = json.loads((pub / f'data/book2/lesson-{lesson}.json').read_text())
model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=1,
                     download_root=str(Path.home() / '.cache/read-alone/whisper'), local_files_only=True)
out = []
for w in data['words']:
    if len(sys.argv) > 4 and w['word'] != sys.argv[4]:
        continue
    for kind in ['slow', 'normal', 'meaning']:
        a, r = sf.read(pub / w['audio'][kind], dtype='float32')
        x = np.interp(np.arange(round(len(a) * 16000 / r)) / 16000, np.arange(len(a)) / r, a).astype('float32')
        segs, _ = model.transcribe(x, language='zh' if kind == 'meaning' else 'en', beam_size=3,
                                   vad_filter=False, condition_on_previous_text=False)
        text = ' '.join(s.text.strip() for s in segs)
        fr = round(r * .01); rms = np.sqrt(np.mean(a[:len(a)//fr*fr].reshape(-1, fr)**2, axis=1)); pk = rms.max()
        act = np.flatnonzero(rms > pk * .025)
        gaps = np.flatnonzero(np.diff(act) > 15)
        rec = {'word': w['word'], 'kind': kind, 'asr': text, 'duration': round(len(a)/r, 3),
               'first_active_s': round(act[0]*.01, 2), 'internal_gaps_ge150ms': [[round(act[g]*.01+.01, 2), round(act[g+1]*.01, 2)] for g in gaps]}
        if kind != 'meaning':
            rec['strict'] = tokens(text) == tokens(w['word']) and '?' not in text
        out.append(rec); print(json.dumps(rec, ensure_ascii=False), flush=True)
Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
