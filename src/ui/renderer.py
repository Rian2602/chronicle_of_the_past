import os

ANSI = {
    "white": "\033[37m", "cyan": "\033[36m", "green": "\033[32m",
    "red": "\033[31m", "yellow": "\033[33m", "magenta": "\033[35m",
    "blue": "\033[34m", "gray": "\033[90m", "reset": "\033[0m",
}

_UNICODE_BORDER = {
    "normal": ("┌", "─", "┐", "│", "└", "┘"),
    "double": ("╔", "═", "╗", "║", "╚", "╝"),
}
_ASCII_BORDER = ("+", "-", "+", "|", "+", "+")


def supports_unicode():
    if os.name == "nt":
        return False
    term = os.environ.get("TERM", "")
    return term != "dumb"


def _border(border_style):
    if supports_unicode():
        return _UNICODE_BORDER.get(border_style, _UNICODE_BORDER["normal"])
    return _ASCII_BORDER


def box(text, border_style="normal"):
    tl, h, tr, v, bl, br = _border(border_style)
    lines = text.split("\n")
    width = max((len(line) for line in lines), default=0)
    out = [f"{tl}{h * (width + 2)}{tr}"]
    for line in lines:
        out.append(f"{v} {line}{' ' * (width - len(line))} {v}")
    out.append(f"{bl}{h * (width + 2)}{br}")
    return "\n".join(out)


def bar(current, total, width=14):
    if total <= 0:
        return "░" * width
    filled = round(current / total * width)
    return "█" * filled + "░" * (width - filled)
