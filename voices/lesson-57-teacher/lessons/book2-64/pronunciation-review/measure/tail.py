import sys, numpy as np, soundfile as sf, parselmouth
p, a0, a1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
a, r = sf.read(p, dtype='float64'); fr = round(r*.02)
pk = max(np.sqrt(np.mean(a[i*fr:(i+1)*fr]**2)) for i in range(len(a)//fr))
snd = parselmouth.Sound(a, r)
pit = snd.to_pitch_ac(time_step=.02, pitch_floor=75, pitch_ceiling=900, octave_jump_cost=.7)
for i in range(int(a0/.02), int(a1/.02)):
    x = a[i*fr:(i+1)*fr]; rms = np.sqrt(np.mean(x**2))
    spec = np.abs(np.fft.rfft(x*np.hanning(len(x)))); f = np.fft.rfftfreq(len(x), 1/r)
    cen = (spec*f).sum()/spec.sum()
    t = i*.02+.01
    print(f"{t:.2f} rms%={100*rms/pk:5.1f} centroid={cen:6.0f} f0={pit.get_value_at_time(t) or 0:6.0f}")
