import random


def pick(items: list, k: int) -> list:
    return random.sample(items, k=min(k, len(items)))