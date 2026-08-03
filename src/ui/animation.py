import time


def progress(label, frames=10):
    return [f"{label} {'█' * i}{'░' * (frames - i)}" for i in range(1, frames + 1)]


def animate(frames, delay=0.05, sleep=time.sleep):
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        sleep(delay)
    print()
