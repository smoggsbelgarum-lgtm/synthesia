#!/usr/bin/env python3
# gradient_to_song.py — reconstruct song from gradient PNG
# Supports: --instrument {piano,synth}, --assets for piano samples
# Reads metadata embedded in PNG to match original duration

import os, re, json, argparse, numpy as np
from PIL import Image
import soundfile as sf
import librosa

SAMPLE_RATE = 44100

NOTE_TO_SEMITONE = {
    'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,
    'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11
}

def name_to_midi(fname):
    base = os.path.splitext(os.path.basename(fname))[0]
    m = re.match(r'^[A-G](?:#|b)?\d+$', base)
    if m:
        note = re.match(r'^[A-G](?:#|b)?', base).group(0)
        octave = int(base[len(note):])
        return 12*(octave+1) + NOTE_TO_SEMITONE[note]
    m = re.match(r'^midi(\d+)$', base, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def load_piano_samples(piano_dir):
    samples = {}
    if not os.path.isdir(piano_dir):
        return samples
    for fn in os.listdir(piano_dir):
        if not fn.lower().endswith(('.wav','.flac','.ogg','.mp3','.m4a')):
            continue
        midi = name_to_midi(fn)
        if midi is None:
            continue
        y, sr = librosa.load(os.path.join(piano_dir, fn), sr=SAMPLE_RATE, mono=True)
        yt, _ = librosa.effects.trim(y, top_db=40)
        if yt.size == 0: yt = y
        samples[midi] = yt.astype(np.float32)
    return samples

def synth_tone(freq, duration_s, amplitude=0.28):
    n = int(duration_s * SAMPLE_RATE)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.linspace(0, duration_s, n, endpoint=False)
    sine = np.sin(2 * np.pi * freq * t)
    saw = 2.0 * (t * freq - np.floor(0.5 + t * freq))
    signal = 0.7 * sine + 0.3 * saw
    env = np.ones_like(signal)
    a = max(int(0.01 * SAMPLE_RATE), 1)
    a = min(a, len(signal)//2)
    env[:a] = np.linspace(0, 1, a)
    env[-a:] = np.linspace(1, 0, a)
    return (amplitude * signal * env).astype(np.float32)

def midi_to_freq(m): return 440.0 * (2 ** ((m - 69) / 12))

def render_note(midi, dur_s, vel, instrument, piano_samples):
    if instrument == "piano" and piano_samples:
        avail = np.array(sorted(piano_samples.keys()))
        base = int(avail[np.abs(avail - midi).argmin()])
        y = piano_samples[base]
        steps = midi - base
        if steps != 0:
            y = librosa.effects.pitch_shift(y, sr=SAMPLE_RATE, n_steps=steps)
        target = int(max(dur_s, 0.01) * SAMPLE_RATE)
        if len(y) > target:
            y = y[:target]
        else:
            reps = int(np.ceil(target / max(len(y), 1)))
            y = np.tile(y, reps)[:target]
        f = min(200, target)
        if f > 8:
            y[:f] *= np.linspace(0, 1, f)
            y[-f:] *= np.linspace(1, 0.7, f)
        return (vel * y).astype(np.float32)
    return synth_tone(midi_to_freq(midi), dur_s, amplitude=vel)

def rgb_to_hsv_array(rgb_arr):
    rgb = rgb_arr / 255.0
    out = np.zeros_like(rgb, dtype=np.float64)
    for i, (r, g, b) in enumerate(rgb):
        mx, mn = max(r, g, b), min(r, g, b)
        diff = mx - mn
        if diff == 0:
            h = 0.0
        elif mx == r:
            h = ((g - b) / diff) % 6
        elif mx == g:
            h = (b - r) / diff + 2
        else:
            h = (r - g) / diff + 4
        h = h / 6.0
        s = 0 if mx == 0 else diff / mx
        v = mx
        out[i] = [h, s, v]
    return out

def gradient_to_song(image_path, out_wav=None, instrument="piano", assets_root="assets"):
    im = Image.open(image_path).convert("RGB")
    info = im.info if hasattr(im, "info") else {}
    meta = {}
    if "synesthesia_meta" in info:
        try: meta = json.loads(info["synesthesia_meta"])
        except: meta = {}

    width, height = im.size
    px_per_col = int(meta.get("pixels_per_col", 1))
    cols = int(meta.get("cols", max(1, width // max(px_per_col,1))))
    duration_s = float(meta.get("duration_s", cols * 0.25))  # fallback
    ymid = height // 2
    xs = np.linspace(0, width-1, cols).astype(int)
    colors = np.array([im.getpixel((int(x), ymid)) for x in xs], dtype=np.uint8)
    hsv = rgb_to_hsv_array(colors)

    hue, sat, val = hsv[:,0], hsv[:,1], hsv[:,2]
    pcs = np.round(hue * 12).astype(int) % 12
    octs = np.clip(np.round(3 + 2 * sat), 3, 5).astype(int)
    midis = 12 * (octs + 1) + pcs
    vels = 0.18 + 0.82 * val

    dur_per_col = float(duration_s) / float(cols)
    piano_dir = os.path.join(assets_root, "instruments", "piano")
    piano_samples = load_piano_samples(piano_dir) if instrument == "piano" else {}

    audio = np.zeros(1, dtype=np.float32)
    for m, vel in zip(midis, vels):
        tone = render_note(int(m), float(dur_per_col), float(vel), instrument, piano_samples)
        audio = np.concatenate([audio, tone])

    if out_wav is None:
        out_dir = os.path.join("outputs", "songs")
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(image_path))[0]
        out_wav = os.path.join(out_dir, f"{base}_song.wav")
    sf.write(out_wav, audio, SAMPLE_RATE)
    return out_wav, {"duration_s": duration_s, "cols": cols, "instrument": instrument}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("-o","--out")
    ap.add_argument("--instrument", choices=["piano","synth"], default="piano")
    ap.add_argument("--assets", default="assets")
    args = ap.parse_args()
    out_wav, meta = gradient_to_song(args.image, out_wav=args.out,
                                     instrument=args.instrument, assets_root=args.assets)
    print("Saved:", out_wav)
    print("Meta used:", json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
