from src.models.command import Command


def parse_input(text):
    tokens = text.strip().lower().split()
    if not tokens:
        return Command(action="")
    first = tokens[0]
    rest = tokens[1:]
    if first.isdigit():
        return Command(action="select", args=rest, index=int(first))
    return Command(action=first, args=rest)
