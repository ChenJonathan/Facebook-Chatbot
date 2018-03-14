from html import unescape
import json
import random

# Beasts
beast_data = []
with open('./data/beasts.txt') as data:
    for line in data.readlines():
        line = line.split(',')
        beast_data.append((line[0].strip(), int(line[1]), int(line[2])))


def random_beast():
    return random.choice(beast_data)


# Crafting
craft_data = json.load(open('./data/craft.json'))

# Datasets
terms = []
definitions = []
with open('./data/vocab.txt') as data:
    for line in data.readlines():
        term, definition = line.split(':', 1)
        term = term[0].upper() + term[1:]
        definition = definition[0].upper() + definition[1:]
        terms.append(term.strip())
        definitions.append(definition.strip())


def _parse_mcq_dataset(file_name):
    with open('./data/' + file_name, encoding='utf8') as data:
        quests = []
        quest = {'Answers': []}
        for line in data.readlines():
            line = unescape(line.strip())
            if len(line) == 0:
                if 'Question' in quest:
                    quests.append(quest)
                quest = {'Answers': []}
            elif 'Question' not in quest:
                quest['Question'] = line
            else:
                correct, answer = line.split(' ', 1)
                correct = int(correct)
                if correct:
                    quest['Correct'] = len(quest['Answers'])
                quest['Answers'].append(answer[0].upper() + answer[1:])
        return quests


econ_dataset = _parse_mcq_dataset('econ.txt')
gov_dataset = _parse_mcq_dataset('gov.txt')
history_dataset = _parse_mcq_dataset('history.txt')
psych_dataset = _parse_mcq_dataset('psych.txt')

science_dataset = []
with open('./data/science.json') as data:
    data = json.load(data)
    for datum in data:
        try:
            quest = {
                'Question': datum['question'],
                'Answers': []
            }
            for i in range(1, 4):
                answer = datum['distractor' + str(i)]
                quest['Answers'].append(answer[0].upper() + answer[1:])
            quest['Correct'] = random.randint(0, len(quest['Answers']))
            correct_answer = datum['correct_answer'][0].upper() + datum['correct_answer'][1:]
            quest['Answers'].insert(quest['Correct'], correct_answer)
            science_dataset.append(quest)
        except:
            pass

# Emoji
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


def random_emoji():
    emoji_decimal = random.choice(emojis)
    emoji_escaped = b'\\U%08x' % emoji_decimal
    return emoji_escaped.decode('unicode-escape')


# Item drops
item_drop_data = json.load(open('./data/drops.json'))

# Monsters
monster_data = json.load(open('./data/monsters.json'))

# Patch notes
with open('./data/notes.txt') as data:
    patch_notes = data.read()