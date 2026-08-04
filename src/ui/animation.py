import time

from src.ui.renderer import bar


def progress(label, frames=10):
    """Bangun frame animasi progress bar untuk satu label."""
    return [
        f"{label} {bar(i, frames, width=frames)}" for i in range(1, frames + 1)
    ]


def delay_for(mode):
    """Jeda antar frame sesuai mode animasi (None = nonaktif)."""
    return {"normal": 0.05, "fast": 0.01, "off": None}[mode]


def animate(frames, delay=0.05, sleep=time.sleep):
    """Cetak frame animasi di baris yang sama dengan jeda tertentu."""
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        sleep(delay)
    print()
