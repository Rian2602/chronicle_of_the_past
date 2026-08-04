import time

from src.ui.renderer import bar


def progress(label, frames=10):
    return [f"{label} {bar(i, frames, width=frames)}" for i in range(1, frames + 1)]


def delay_for(mode):
    return {"normal": 0.05, "fast": 0.01, "off": None}[mode]


def animate(frames, delay=0.05, sleep=time.sleep):
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        sleep(delay)
    print()
