import random

terms = []
definitions = []

with open('vocab.txt', 'r') as vocab:
    for line in vocab.readlines():
        term, definition = line.split(':', 1)
        term = term[0].upper() + term[1:]
        definition = definition[0].upper() + definition[1:]
        terms.append(term.strip())
        definitions.append(definition.strip())

def generate_quest(difficulty):
    indices = random.sample(range(0, len(terms)), difficulty + 1)
    correct = random.randint(0, difficulty)
    return {
        'question': definitions[indices[correct]],
        'answers': [terms[index] for index in indices],
        'correct': correct
    }