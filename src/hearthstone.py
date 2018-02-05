import random

beasts = []

with open('./data/beasts.txt', 'r') as data:
    for line in data.readlines():
        line = line.split(',')
        beasts.append((line[0].strip(), int(line[1]), int(line[2])))

def random_beast():
    return random.choice(beasts)