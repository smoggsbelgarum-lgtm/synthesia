#!/usr/bin/env python3
# song_to_gradient.py — convert audio → gradient (function only, GUI friendly)

import numpy as np
from PIL import Image
import librosa

def song_to_gradient(path, width=800, height=120):
    """
    Convert an audio file into a gradient image.

    Args:
        path (str): Path to audio file (.wav, .mp3, etc.)
        width (int): Output gradient width in pixels
        height (int): Output gradient height in pixels

    Returns:
        PIL.Image: Gradient image
        dict: Metadata with duration
    """
    y, sr = librosa.load(path, sr=None, mono=True)

    # Chroma timeline
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)  # (12, T)
    T = chroma.shape[1]
    if T == 0:
        raise RuntimeError("Audio produced no chroma frames. Try a different file.")

    # RMS timeline (may be a different length)
    rms = librosa.feature.rms(y=y)[0]
    Tr = len(rms)

    if Tr == 0:
        rms_resampled = np.zeros(T, dtype=float)
    else:
        x_src = np.linspace(0, 1, Tr)
        x_tgt = np.linspace(0, 1, T)
        rms_resampled = np.interp(x_tgt, x_src, rms)

    if np.ptp(rms_resampled) == 0:
        rms_norm = np.zeros_like(rms_resampled)
    else:
        rms_norm = (rms_resampled - rms_resampled.min()) / rms_resampled.ptp()

    dom_pc = np.argmax(chroma, axis=0)

    def pitchclass_to_hue(pc): return (int(pc) % 12) / 12.0
    def hsv_to_rgb(h, s, v):
        i = int(h*6) % 6; f = h*6 - int(h*6)
        p = v*(1 - s); q = v*(1 - f*s); t = v*(1 - (1 - f)*s)
        if i==0:r,g,b=v,t,p
        elif i==1:r,g,b=q,v,p
        elif i==2:r,g,b=p,v,t
        elif i==3:r,g,b=p,q,v
        elif i==4:r,g,b=t,p,v
        else:   r,g,b=v,p,q
        return int(r*255), int(g*255), int(b*255)

    cols=[]
    for i in range(T):
        h = pitchclass_to_hue(dom_pc[i])
        s = float(np.clip(np.mean(chroma[:, i]) * 1.2, 0.15, 0.95))
        v = float(np.clip(0.35 + 0.65*rms_norm[i], 0.20, 1.00))
        cols.append(hsv_to_rgb(h,s,v))

    xs = np.linspace(0, len(cols)-1, width).astype(int)
    row = np.array([cols[x] for x in xs], dtype=np.uint8)
    img = np.repeat(row[np.newaxis,:,:], height, axis=0)

    duration_s = librosa.get_duration(y=y, sr=sr)
    return Image.fromarray(img, mode="RGB"), {"duration_s": duration_s}
