import sys
import numpy as np, parselmouth, soundfile as sf
for path in sys.argv[1:]:
    a, r = sf.read(path, dtype='float64')
    snd = parselmouth.Sound(a, r)
    p = snd.to_pitch_ac(time_step=.02, pitch_floor=100, pitch_ceiling=600, octave_jump_cost=.7)
    f = p.selected_array['frequency']
    fr = round(r*.02); rms = [float(np.sqrt(np.mean(a[i*fr:(i+1)*fr]**2))) for i in range(len(a)//fr)]
    pk = max(rms)
    print(path.split('/')[-1], ' '.join(f"{t:.2f}:{int(v)}" for t, v in zip(p.xs(), f) if v > 0 and rms[min(int(t/.02), len(rms)-1)] > pk*.05))
