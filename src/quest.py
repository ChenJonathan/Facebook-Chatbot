from fbchat.models import *
from html import unescape
import random
import requests

from data import terms, definitions
from mongo import *

trivia_categories = list(range(9, 25)) + list(range(27, 31)) + [32]


def set_quest_type(client, user, text, thread_id):
    user_id = user['_id']
    quest_type = text.lower()
    if quest_type in ['vocab', 'trivia']:
        client.quest_type_record[user_id] = quest_type
        reply = 'Quest type set to ' + quest_type[0].upper() + quest_type[1:] + '.'
    else:
        reply = 'Not a valid quest type.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def generate_quest(client, user, thread_id):
    if user['_id'] not in client.quest_type_record:
        client.quest_type_record[user['_id']] = 'vocab'
    quest_type = client.quest_type_record[user['_id']]
    if quest_type == 'vocab':
        _generate_vocab_quest(client, user, thread_id)
    elif quest_type == 'trivia':
        _generate_trivia_quest(client, user, thread_id)


def _generate_vocab_quest(client, user, thread_id):
    user_id = user['_id']
    gold = user['Gold']
    difficulty = 1 if gold < 0 else len(str(gold))
    indices = random.sample(range(0, len(terms)), difficulty + 1)
    correct = random.randint(0, difficulty)
    if random.random() > 0.5:
        quest = {
            'Question': definitions[indices[correct]],
            'Answers': [terms[index] for index in indices],
            'Correct': correct
        }
        client.quest_record[user_id] = quest
        reply = user['Name'] + ': Which word means "' + quest['Question'] + '"?'
    else:
        quest = {
            'Question': terms[indices[correct]],
            'Answers': [definitions[index] for index in indices],
            'Correct': correct
        }
        client.quest_record[user_id] = quest
        reply = user['Name'] + ': What does "' + quest['Question'] + '" mean?'
    for i, answer in enumerate(quest['Answers']):
        reply += '\n' + str(i + 1) + '. ' + quest['Answers'][i]
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _generate_trivia_quest(client, user, thread_id):
    user_id = user['_id']
    category = random.choice(trivia_categories)
    url = 'https://opentdb.com/api.php?amount=1&category=' + str(category) + '&type=multiple'
    trivia = requests.get(url).json()['results'][0]
    answers = [unescape(answer) for answer in trivia['incorrect_answers']]
    correct = random.randint(0, len(answers))
    answers.insert(correct, unescape(trivia['correct_answer']))
    quest = {
        'Question': unescape(trivia['question']),
        'Answers': answers,
        'Correct': correct
    }
    client.quest_record[user_id] = quest
    reply = user['Name'] + ': ' + quest['Question']
    for i, answer in enumerate(quest['Answers']):
        reply += '\n' + str(i + 1) + '. ' + quest['Answers'][i]
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def complete_quest(client, user, text, thread_id):
    user_id = user['_id']
    quest = client.quest_record[user_id]
    quest_type = client.quest_type_record[user['_id']]
    correct = quest['Correct']
    del client.quest_record[user_id]
    if text == str(correct + 1):
        if quest_type == 'vocab':
            delta = random.randint(20, 200)
        elif quest_type == 'trivia':
            delta = random.randint(30, 300)
        gold_add(user_id, delta)
        reply = user['Name'] + ' has gained ' + str(delta) + ' gold and is now at '
        reply += str(user['Gold'] + delta) + ' gold total!'
    else:
        if quest_type == 'vocab':
            delta = random.randint(-200, -20)
        elif quest_type == 'trivia':
            delta = random.randint(-100, -10)
        gold_add(user_id, delta)
        reply = user['Name'] + ' has lost ' + str(-delta) + ' gold and is now at '
        reply += str(user['Gold'] + delta) + ' gold total. The correct answer was '
        reply += '"' + quest['Answers'][correct] + '".'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)