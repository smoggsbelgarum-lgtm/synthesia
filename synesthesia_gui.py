import os, tkinter as tk
from tkinter import ttk, filedialog, messagebox

from song_to_gradient import song_to_gradient
from gradient_to_song import gradient_to_song

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(APP_DIR, "outputs")
GRADS_DIR = os.path.join(OUT_DIR, "gradients")
SONGS_DIR = os.path.join(OUT_DIR, "songs")
for d in (GRADS_DIR, SONGS_DIR): os.makedirs(d, exist_ok=True)

class SynesthesiaGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Synesthesia Machine — Menu Driven")
        self.geometry("500x220")

        ttk.Label(self, text="Synesthesia Machine", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Button(self, text="Song → Gradient", command=self.song_to_grad).pack(pady=10, ipadx=20, ipady=10)
        ttk.Button(self, text="Gradient → Song", command=self.grad_to_song).pack(pady=10, ipadx=20, ipady=10)

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status).pack(fill="x", pady=(15,0))

    def song_to_grad(self):
        audio = filedialog.askopenfilename(filetypes=[("Audio", "*.wav;*.mp3;*.flac;*.ogg;*.m4a")])
        if not audio: return
        base = os.path.splitext(os.path.basename(audio))[0]
        out = os.path.join(GRADS_DIR, f"{base} gradient.png")
        try:
            img, meta = song_to_gradient(audio)  # direct function call
            img.save(out)
            self.status.set(f"Saved {out}")
            messagebox.showinfo("Done", f"Gradient saved:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def grad_to_song(self):
        image = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if not image: return
        base = os.path.splitext(os.path.basename(image))[0]
        out = os.path.join(SONGS_DIR, f"{base} song.wav")
        try:
            wav, meta = gradient_to_song(image, out_wav=out, instrument="piano", assets_root="assets")
            self.status.set(f"Saved {wav}")
            messagebox.showinfo("Done", f"Song saved:\n{wav}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    SynesthesiaGUI().mainloop()
