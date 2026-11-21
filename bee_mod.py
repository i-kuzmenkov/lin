import os, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
CUSTOM_MP3 = os.path.join(BASE, "pchelki.mp3")
WAV_PATH = os.path.join(BASE, "bee_song.wav")
LYRICS = "Кто пчёлок уважает, кто к ним не пристаёт, того они не жалят, тому приносят мёд!"

def ensure_wav():
    if os.path.exists(WAV_PATH):
        return
    if os.path.exists(CUSTOM_MP3) and shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", CUSTOM_MP3, WAV_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    tts = shutil.which("espeak-ng") or shutil.which("espeak")
    if tts:
        subprocess.run([tts, "-v", "ru", "-s", "145", "-p", "65", "-w", WAV_PATH, LYRICS], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_bee_music(app):
    if not getattr(app, "pe_mode", True): return
    ensure_wav()
    if getattr(app, "_bee_proc", None) and app._bee_proc.poll() is None:
        return
    p = shutil.which("paplay") or shutil.which("aplay")
    if p and os.path.exists(WAV_PATH):
        app._bee_proc = subprocess.Popen(["bash", "-c", f"while true; do {p} '{WAV_PATH}' >/dev/null 2>&1; done"], start_new_session=True)

def stop_bee_music(app):
    proc = getattr(app, "_bee_proc", None)
    if proc:
        try: os.killpg(os.getpgid(proc.pid), 15)
        except Exception: pass
        app._bee_proc = None

def draw_bee(canvas, px, py, vy, grid, tick, pe=True, sk=None):
    if not pe:
        sk = sk or {"fill": "#ffeaa7", "out": "#fdcb6e", "eye": "#2d3436"}
        tilt = max(-8, min(8, vy * 1.1))
        # Кубик-пилот в кабине (цвет и глаза из магазина)
        cx1, cy1 = px + 11, py + 5 + tilt * 0.3
        cx2, cy2 = px + 29, py + 23 + tilt * 0.3
        canvas.create_rectangle(cx1, cy1, cx2, cy2, fill=sk["fill"], outline=sk["out"], width=2)
        canvas.create_rectangle(cx1 + 9, cy1 + 4, cx1 + 12, cy1 + 7, fill=sk["eye"], outline="")
        canvas.create_rectangle(cx1 + 14, cy1 + 4, cx1 + 17, cy1 + 7, fill=sk["eye"], outline="")
        canvas.create_rectangle(cx1 + 9, cy1 + 10, cx1 + 17, cy1 + 12, fill=sk["eye"], outline="")
        # Корпус самолётика вокруг кубика
        canvas.create_polygon(
            px + 2, py + 20 - tilt * 0.4,
            px + 10, py + 36,
            px + 34, py + 36,
            px + grid, py + 24 + tilt,
            px + 28, py + 19 + tilt * 0.4,
            px + 10, py + 19 + tilt * 0.2,
            fill="#ff6b81", outline="white", width=2
        )
        return
    canvas.create_polygon(px-6, py+22, px+6, py+17, px+6, py+27, fill="#1e272e")
    wy = 4 if (tick // 4) % 2 == 0 else 9
    canvas.create_oval(px+12, py+wy, px+26, py+wy+13, fill="#dff9fb", outline="#7ed6df")
    canvas.create_oval(px+3, py+10, px+grid-2, py+grid-4, fill="#ffd32a", outline="#1e272e", width=2)
    canvas.create_line(px+13, py+11, px+13, py+grid-5, fill="#1e272e", width=3)
    canvas.create_line(px+21, py+11, px+21, py+grid-5, fill="#1e272e", width=3)
    canvas.create_oval(px+27, py+15, px+33, py+21, fill="white", outline="#1e272e")
