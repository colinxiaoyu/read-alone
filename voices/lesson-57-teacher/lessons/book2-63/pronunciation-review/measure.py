import argparse, hashlib, json, pathlib, re
import numpy as np
import soundfile as sf
import parselmouth
from scipy.signal import butter, sosfiltfilt
from faster_whisper import WhisperModel

p=argparse.ArgumentParser()
p.add_argument('task',type=pathlib.Path)
a=p.parse_args()
task=a.task
model=WhisperModel('/Users/colin/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120',device='cpu',compute_type='int8',cpu_threads=1,download_root=str(pathlib.Path.home()/'.cache/read-alone/whisper'),local_files_only=True)

def runs(mask):
    edges=np.diff(np.r_[False,mask,False].astype(int))
    return list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))

def measure(path,trim=None):
    x,sr=sf.read(path,dtype='float64')
    offset=trim[0] if trim else 0
    if trim:x=x[round(trim[0]*sr):round(trim[1]*sr)]
    frame=round(sr*.01)
    times=(np.arange(len(x)//frame)+.5)*.01
    rms=np.sqrt(np.mean(x[:len(times)*frame].reshape(-1,frame)**2,axis=1))
    hi=sosfiltfilt(butter(6,3500,'highpass',fs=sr,output='sos'),x)
    high=np.sqrt(np.mean(hi[:len(times)*frame].reshape(-1,frame)**2,axis=1))
    snd=parselmouth.Sound(x,sampling_frequency=sr)
    pitch=snd.to_pitch_ac(time_step=.01,pitch_floor=100,pitch_ceiling=600,octave_jump_cost=.7)
    f0=np.array([pitch.get_value_at_time(t) for t in times])
    voiced=np.isfinite(f0)&(rms>max(rms.max()*.05,.001))
    f0[~voiced]=np.nan
    peak=float(rms[voiced].max()) if voiced.any() else None
    record={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'trim':trim,'duration':len(x)/sr}
    if not peak:
        record['error']='no_voiced_vowel'
        return record
    f0_peak_index=int(np.nanargmax(f0))
    voiced_indexes=np.flatnonzero(voiced)
    tail=voiced_indexes[-min(3,len(voiced_indexes)):]
    endpoint=float(np.median(f0[tail]))
    drop=float(12*np.log2(f0[f0_peak_index]/endpoint))
    last=voiced_indexes[-min(8,len(voiced_indexes)):]
    tail_rise=float(12*np.log2(f0[last[-1]]/f0[last[0]]))
    formant=snd.to_formant_burg(time_step=.01,maximum_formant=5500)
    f3=np.array([formant.get_value_at_time(3,t) if v else np.nan for t,v in zip(times,voiced)])
    stops=[]
    for b,e in runs(rms<peak*.1):
        if b==0 or e==len(times):continue
        prior=np.flatnonzero(voiced[:b])
        if not len(prior) or (b-prior[-1])*.01>.15:continue
        end=min(e+3,len(times))
        burst=e+int(np.argmax(high[e:end]))
        stops.append({'closure':[round(b*.01+offset,3),round(e*.01+offset,3)],'closure_ms':int((e-b)*10),'burst_time':round(times[burst]+offset,3),'burst_ratio':round(float(high[burst]/peak),4)})
    y=np.interp(np.arange(round(len(x)*16000/sr))/16000,np.arange(len(x))/sr,x).astype('float32')
    segs,_=model.transcribe(y,language='en',beam_size=3,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
    segs=list(segs)
    text=' '.join(s.text.strip() for s in segs)
    record.update({'recognized':text,'f0_peak_hz':round(float(f0[f0_peak_index]),1),'f0_peak_time':round(float(times[f0_peak_index]+offset),3),'f0_end_hz':round(endpoint,1),'f0_drop_st':round(drop,2),'f0_tail_change_st':round(tail_rise,2),'f3_min_hz':round(float(np.nanmin(f3)),1),'stops':stops,'frames':[{'t':round(float(t+offset),3),'rms':round(float(r),5),'high_ratio':round(float(h/peak),4),'f0':round(float(f),1) if np.isfinite(f) else None,'f3':round(float(ff),1) if np.isfinite(ff) else None} for t,r,h,f,ff in zip(times,rms,high,f0,f3)]})
    return record

out=task/'measurements.json'
records=json.loads(out.read_text()) if out.exists() else {}
paths=[]
for lesson in [62,63]:
    trim=json.loads((task/'before'/str(lesson)/'trims.json').read_text())
    job=json.loads((task/'before'/str(lesson)/'raw/raw-generation.json').read_text())
    for req in job['requests']:
        if req['language']=='en':paths.append((task/'before'/str(lesson)/'raw'/req['file'],trim[req['word']],req['word'],lesson,'old',None))
    for manifest in sorted((task/'candidates'/str(lesson)).glob('*/raw-generation.json')):
        for req in json.loads(manifest.read_text())['requests']:
            path=manifest.parent/req['file']
            if req['language']=='en' and path.exists():paths.append((path,None,req['word'],lesson,'candidate',req['seed']))
for path,trim,word,lesson,kind,seed in paths:
    key=str(path.relative_to(task))
    if key in records:continue
    r=measure(path,trim)
    r.update({'word':word,'lesson':lesson,'kind':kind,'seed':seed})
    records[key]=r
    temp=out.with_suffix('.tmp');temp.write_text(json.dumps(records,ensure_ascii=False,indent=2));temp.replace(out)
    print(json.dumps({k:v for k,v in r.items() if k not in ['frames','sha256']},ensure_ascii=False),flush=True)
print('MEASUREMENTS_COMPLETE',flush=True)
