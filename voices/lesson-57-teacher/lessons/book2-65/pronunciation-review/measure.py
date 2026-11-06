import json, sys
import numpy as np, soundfile as sf, parselmouth

def regions(mask, hop):
    out, begin = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and begin is None: begin = i
        if not m and begin is not None: out.append((begin * hop, i * hop)); begin = None
    return out

def measure(path, start=0.0):
    x, sr = sf.read(path, dtype='float32')
    x = x[round(start * sr):]
    hop = 0.01; f = round(sr * hop)
    rms = np.sqrt(np.mean(x[:len(x) // f * f].reshape(-1, f) ** 2, axis=1))
    thr = max(rms.max() * 0.025, 0.0005)
    act = regions(rms > thr, hop)
    merged = []
    for a, b in act:
        if merged and a - merged[-1][1] < 0.08: merged[-1] = (merged[-1][0], b)
        else: merged.append((a, b))
    seg_peak = [float(rms[round(a/hop):round(b/hop)].max()) for a, b in merged]
    main = int(np.argmax([(b - a) * p for (a, b), p in zip(merged, seg_peak)]))
    pre = merged[:main]
    snd = parselmouth.Sound(x.astype('float64'), sr)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=100, pitch_ceiling=600, octave_jump_cost=0.7)
    ts = pitch.xs(); f0 = pitch.selected_array['frequency']
    fr = np.minimum((ts / hop).astype(int), len(rms) - 1)
    ok = (f0 > 0) & (rms[fr] > rms.max() * 0.05) & (rms[fr] > 0.001)
    v_t, v_f = ts[ok], f0[ok]
    res = {'file': path.split('/')[-1], 'dur': round(len(x) / sr + start, 3),
           'segments': [[round(a + start, 2), round(b + start, 2), round(p, 4)] for (a, b), p in zip(merged, seg_peak)],
           'main': [round(merged[main][0] + start, 2), round(merged[main][1] + start, 2)],
           'pre_noise': [[round(a + start, 2), round(b + start, 2)] for a, b in pre]}
    if len(v_f) >= 3:
        k = int(np.argmax(v_f)); tail = float(np.median(v_f[-3:]))
        res.update({'f0_peak': [round(float(v_f[k]), 1), round(float(v_t[k]) + start, 3)], 'f0_tail': round(tail, 1),
                    'fall_st': round(12 * np.log2(v_f[k] / tail), 2),
                    'tail8_st': round(12 * np.log2(v_f[-1] / v_f[max(0, len(v_f) - 8)]), 2),
                    'f0_track': [[round(float(t) + start, 2), round(float(v))] for t, v in zip(v_t[::3], v_f[::3])]})
    return res

if __name__ == '__main__':
    start = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    for p in sys.argv[1].split(','):
        print(json.dumps(measure(p, start)))
