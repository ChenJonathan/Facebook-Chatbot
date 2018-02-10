import random

# Beasts

beasts = []

with open('./data/beasts.txt', 'r') as data:
    for line in data.readlines():
        line = line.split(',')
        beasts.append((line[0].strip(), int(line[1]), int(line[2])))

# Emojis

EMOJI_RANGES_UNICODE = [
        (0x0001F300, 0x0001F320),
        (0x0001F330, 0x0001F335),
        (0x0001F337, 0x0001F37C),
        (0x0001F380, 0x0001F393),
        (0x0001F3A0, 0x0001F3C4),
        (0x0001F3C6, 0x0001F3CA),
        (0x0001F3E0, 0x0001F3F0),
        (0x0001F400, 0x0001F43E),
        (0x0001F440, 0x0001F440),
        (0x0001F442, 0x0001F4F7),
        (0x0001F4F9, 0x0001F4FC),
        (0x0001F500, 0x0001F53C),
        (0x0001F540, 0x0001F543),
        (0x0001F550, 0x0001F567),
        (0x0001F5FB, 0x0001F5FF),
]

emojis = []
for r in EMOJI_RANGES_UNICODE:
    emojis += range(r[0], r[-1])

# Vocab

terms = []
definitions = []

with open('./data/vocab.txt', 'r') as data:
    for line in data.readlines():
        term, definition = line.split(':', 1)
        term = term[0].upper() + term[1:]
        definition = definition[0].upper() + definition[1:]
        terms.append(term.strip())
        definitions.append(definition.strip())


# Methods

def random_beast():
    return random.choice(beasts)


def random_emoji():
    emoji_decimal = random.choice(emojis)
    emoji_escaped = b'\\U%08x' % emoji_decimal
    return emoji_escaped.decode('unicode-escape')