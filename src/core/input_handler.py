from src.models.command import Command


def parse_input(text):
    """Parse user input text into a Command object.

    Args:
        text: Raw input string from user

    Returns:
        Command object with action, args, and index attributes

    Examples:
        "go forest" -> Command(action="go", args=["forest"])
        "1" or "select 1" -> Command(action="select", index=1)
        "" -> Command(action="")
    """
    tokens = text.strip().lower().split()
    if not tokens:
        return Command(action="")

    first = tokens[0]
    rest = tokens[1:]

    # Handle numeric input for dialog/selection (e.g., "1", "2")
    if first.isdigit():
        return Command(action="select", args=rest, index=int(first))

    # Handle explicit "select <number>" command
    if first == "select" and rest and rest[0].isdigit():
        return Command(action="select", args=rest[1:], index=int(rest[0]))

    return Command(action=first, args=rest)
