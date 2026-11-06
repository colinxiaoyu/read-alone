import json, sys
import numpy as np, soundfile as sf, parselmouth
from scipy.signal import butter, sosfiltfilt

def analyse(path, start):
    x, sr = sf.read(path, dtype='float32')
    seg = x[round(start * sr):]
    hop = round(sr * 0.01)
    n = len(seg) // hop
    rms = np.sqrt(np.mean(seg[:n * hop].reshape(n, hop) ** 2, axis=1))
    hf = sosfiltfilt(butter(6, 3500, 'highpass', fs=sr, output='sos'), seg)
    hrms = np.sqrt(np.mean(hf[:n * hop].reshape(n, hop) ** 2, axis=1))
    snd = parselmouth.Sound(seg.astype('float64'), sr)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=100, pitch_ceiling=600, octave_jump_cost=0.7)
    f0 = np.array([p.get_value_at_time(i * 0.01 + 0.005) or 0 for i in range(n)])
    f0 = np.nan_to_num(f0)
    voiced = (f0 > 0) & (rms > rms.max() * 0.08)
    ratio = hrms / np.maximum(rms, 1e-6)
    vowel_runs, b = [], None
    for i, v in enumerate(list(voiced & (ratio < 0.25)) + [False]):
        if v and b is None: b = i
        if not v and b is not None:
            if i - b >= 3: vowel_runs.append((b, i))
            b = None
    out = []
    for a, e in vowel_runs:
        out.append({'t': [round(start + a * 0.01, 2), round(start + e * 0.01, 2)], 'dur_ms': (e - a) * 10,
                    'peak_rms': round(float(rms[a:e].max()), 4), 'f0_mean': round(float(f0[a:e][f0[a:e] > 0].mean()), 1),
                    'f0_max': round(float(f0[a:e].max()), 1)})
    fric = [round(start + i * 0.01, 2) for i in range(n) if ratio[i] > 0.4 and rms[i] > rms.max() * 0.02]
    return {'file': path, 'vowels': out, 'hf_frames': fric}

for arg in sys.argv[1:]:
    path, start = arg.rsplit('@', 1)
    print(json.dumps(analyse(path, float(start))))
