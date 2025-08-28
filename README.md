# synthesia

# 🎨🎶 Synthesia Machine
Turn songs into color gradients—and color gradients back into songs.

This repo demonstrates how information is **encoded, translated, and reconstructed**. We compress a song into a slim image strip (Song → Gradient) and then rebuild new audio from the pixels (Gradient → Song). The round-trip is intentionally **lossy**, just like real-world compression and AI generation.

> If you’re here from the blog: this is the code behind that post.

---

## 📂 Project Files

You can download the three main files here:
- [`song_to_gradient.py`](song_to_gradient.py) — encode audio → gradient  
- [`gradient_to_song.py`](gradient_to_song.py) — decode gradient → audio  
- [`synesthesia_gui.py`](synesthesia_gui.py) — simple Tkinter GUI to run both directions

Optional piano sample set:  
👉 [smoggsbelgarum-lgtm/piano-scale](https://github.com/smoggsbelgarum-lgtm/piano-scale)  

Place the piano note files into:
assets/instruments/piano/

yaml
Copy code

---

## ✨ Features
- **Song → Gradient**: Map pitch classes, harmonic density, and loudness to hue/saturation/value.
- **Gradient → Song**: Decode pixels to notes, synthesize or sample-play them, and export WAV.
- **GUI included** (Tkinter): Run both directions without touching the CLI.
- **Flexible assets**: Works with provided piano note samples, or defaults to a built-in synth.

---

## 📦 Install

```bash
git clone https://github.com/smoggsbelgarum-lgtm/synthesia.git
cd synthesia
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -U pip
pip install numpy pillow librosa soundfile
On some systems you may also need ffmpeg for librosa to load MP3/OGG/M4A.

🚀 Usage
GUI (recommended)
bash
Copy code
python synesthesia_gui.py
Song → Gradient: choose a WAV/MP3/FLAC/OGG/M4A. Output PNG goes to outputs/gradients/.

Gradient → Song: choose a PNG. Output WAV goes to outputs/songs/.

CLI
bash
Copy code
# Encode a song to a gradient (returns a PIL image + metadata dictionary)
python -c "from song_to_gradient import song_to_gradient; import sys; img,meta = song_to_gradient(sys.argv[1]); img.save('outputs/gradients/out.png'); print(meta)" input.wav

# Decode a gradient back to audio
python gradient_to_song.py outputs/gradients/out.png --instrument piano --assets assets
🧠 How it works
Encoding (Song → Gradient)
Load audio (librosa.load) and compute:

Chroma CQT (12-bin pitch-class timeline)

RMS loudness (resampled to align to chroma frames)

Map to HSV:

Hue: dominant pitch class per frame

Saturation: mean chroma energy (clipped 0.15–0.95)

Value: normalized loudness (0.35 + 0.65·RMS, clipped 0.20–1.00)

Resample to the target image width and tile to a fixed height.

File: song_to_gradient.py

Decoding (Gradient → Song)
Read PNG (+ optional "synesthesia_meta" JSON payload).

Sample 1D color timeline (mid-row) with cols evenly spaced positions.

Convert RGB→HSV and map:

Hue → pitch class (rounded to 12 bins)

Saturation → octave (3..5)

Value → velocity (0.18..1.0)

Synthesize notes:

Piano: nearest sample + semitone pitch-shift, trimmed/tiled to note length, small fades

Synth: blend sine + saw with short attack/decay

Concatenate frames and export 44.1 kHz WAV.

File: gradient_to_song.py

🎹 Piano sample assets
Optional: clone and slice notes from this repo:
👉 smoggsbelgarum-lgtm/piano-scale

Supported names:

Note + octave: C4.wav, F#3.flac, Bb5.ogg

MIDI number: midi60.wav

The loader trims silence (top_db=40), finds the nearest note to the requested MIDI, and pitch-shifts as needed.

🧩 Metadata for perfect round-trips (optional)
The decoder reads "synesthesia_meta" from PNGs (duration_s, cols, pixels_per_col).
The GUI currently saves a plain PNG; to embed metadata, add:

python
Copy code
from PIL import PngImagePlugin
info = PngImagePlugin.PngInfo()
info.add_text("synesthesia_meta", '{"duration_s": 7.2, "cols": 800, "pixels_per_col": 1}')
img.save(out_path, pnginfo=info)
🧪 Known limitations
One note per column: chords/timbre are not reconstructed.

Pitch is quantized to 12 bins; octaves limited to 3..5.

Timing is discretized to cols → “blocky” feel at low resolution.

Pitch-shifting of samples may introduce artifacts (expected).
