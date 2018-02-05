from fbchat.models import *
import random

from mongo import *

terms = []
definitions = []

with open('vocab.txt', 'r') as vocab:
    for line in vocab.readlines():
        term, definition = line.split(':', 1)
        term = term[0].upper() + term[1:]
        definition = definition[0].upper() + definition[1:]
        terms.append(term.strip())
        definitions.append(definition.strip())

def generate_quest(client, author_id, thread_id):
    user = user_from_id(author_id)
    experience = user['experience']
    difficulty = 1 if experience < 0 else len(str(experience))
    indices = random.sample(range(0, len(terms)), difficulty + 1)
    correct = random.randint(0, difficulty)
    quest = {
        'question': definitions[indices[correct]],
        'answers': [terms[index] for index in indices],
        'correct': correct
    }
    client.quest_record[author_id] = quest
    reply = user['name'] + ', which word means "' + quest['question'] + '"?'
    for i, answer in enumerate(quest['answers']):
        reply += '\n' + str(i + 1) + '. ' + quest['answers'][i]
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def check_quest(client, text, author_id, thread_id):
    if author_id in client.quest_record:
        text = text.lower()
        quest = client.quest_record[author_id]
        correct = quest['correct']
        del client.quest_record[author_id]
        if text == str(correct + 1) or text == quest['answers'][correct].lower():
            delta = random.randint(10, 99)
            experience_add(author_id, delta)
            user = user_from_id(author_id)
            reply = user['name'] + ' has gained ' + str(delta)
            reply += ' experience points and is now at '
            reply += str(user['experience']) + ' experience total!'
        else:
            delta = random.randint(-99, -10)
            experience_add(author_id, delta)
            user = user_from_id(author_id)
            reply = user['name'] + ' has lost ' + str(-delta)
            reply += ' experience points and is now at '
            reply += str(user['experience']) + ' experience total.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)