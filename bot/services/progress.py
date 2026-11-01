XP_CORRECT = 10
XP_PARTICIPATION = 2
XP_PER_LEVEL = 100
XP_VOTE = 2


def calc_level(xp: int) -> int:
    return 1 + xp // XP_PER_LEVEL
