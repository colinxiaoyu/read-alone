import json, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, soundfile as sf, imageio_ffmpeg
from faster_whisper import WhisperModel

def tokens(t): return re.findall(r'[a-z]+', t.lower())
ff = imageio_ffmpeg.get_ffmpeg_exe()
model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=1,
                     download_root=str(Path.home() / '.cache/read-alone/whisper'), local_files_only=True)
word = sys.argv[1]
for path in sys.argv[2:]:
    res = {}
    for name, speed in [('raw', None), ('slow', .72), ('normal', .86)]:
        src = path
        if speed:
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-y', '-i', path, '-af', f'atempo={speed}', '-ac', '1', '-ar', '24000', '-c:a', 'pcm_s16le', tmp], check=True)
            src = tmp
        a, r = sf.read(src, dtype='float32')
        a = np.pad(a, (round(r*.08), round(r*.12)))
        x = np.interp(np.arange(round(len(a) * 16000 / r)) / 16000, np.arange(len(a)) / r, a).astype('float32')
        segs, _ = model.transcribe(x, language='en', beam_size=3, vad_filter=False, condition_on_previous_text=False)
        t = ' '.join(s.text.strip() for s in segs)
        res[name] = (t, tokens(t) == tokens(word) and '?' not in t)
    print(path, json.dumps(res, ensure_ascii=False), flush=True)
