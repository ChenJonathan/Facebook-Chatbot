from fbchat.models import *
from html import unescape
import random
import requests

from mongo import *

trivia_names = ['Animals', 'Anime', 'Entertainment', 'General Knowledge']
trivia_names += ['Mythology', 'Science', 'Social Studies', 'Sports']

trivia_categories = [[27], [31], [10, 11, 14, 15, 16, 32], [9]]
trivia_categories += [[20], [17, 18, 19], [22, 23, 24], [21]]

terms = []
definitions = []

with open('./data/vocab.txt', 'r') as data:
    for line in data.readlines():
        term, definition = line.split(':', 1)
        term = term[0].upper() + term[1:]
        definition = definition[0].upper() + definition[1:]
        terms.append(term.strip())
        definitions.append(definition.strip())

def set_quest_type(client, user, text, thread_id):
    user_id = user['_id']
    quest_type, topic, *_ = text.lower().split(' ', 1) + ['']
    if quest_type == 'vocab':
        client.quest_type_record[user_id] = [quest_type]
        reply = 'Quest type set to Vocab.'
    elif quest_type == 'trivia':
        try:
            topic = int(topic) - 1
            assert topic >= 0 and topic < len(trivia_names)
            trivia_name = trivia_names[topic]
            client.quest_type_record[user_id] = [quest_type, topic]
            reply = 'Quest type set to Trivia (' + trivia_name + ').'
        except:
            reply = 'Invalid topic number. The topics are as follows:\n'
            for i, trivia_name in enumerate(trivia_names):
                reply += str(i + 1) + '. ' + trivia_name + '\n'
            reply += 'Usage: "!quest trivia <topic_num>"'
    else:
        reply = 'Not a valid quest type.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def generate_quest(client, user, thread_id):
    if user['_id'] not in client.quest_type_record:
        _generate_vocab_quest(client, user, thread_id)
        return
    quest_type = client.quest_type_record[user['_id']]
    print('Testing: ', quest_type)
    if quest_type[0] == 'vocab':
        print('Testing: in vocab')
        _generate_vocab_quest(client, user, thread_id)
    elif quest_type[0] == 'trivia':
        _generate_trivia_quest(client, user, quest_type[1], thread_id)

def _generate_vocab_quest(client, user, thread_id):
    user_id = user['_id']
    gold = user['gold']
    difficulty = 1 if gold < 0 else len(str(gold))
    indices = random.sample(range(0, len(terms)), difficulty + 1)
    correct = random.randint(0, difficulty)
    if random.random() > 0.5:
        quest = {
            'question': definitions[indices[correct]],
            'answers': [terms[index] for index in indices],
            'correct': correct
        }
        client.quest_record[user_id] = quest
        reply = user['name'] + ': Which word means "' + quest['question'] + '"?'
    else:
        quest = {
            'question': terms[indices[correct]],
            'answers': [definitions[index] for index in indices],
            'correct': correct
        }
        client.quest_record[user_id] = quest
        reply = user['name'] + ': What does "' + quest['question'] + '" mean?'
    for i, answer in enumerate(quest['answers']):
        reply += '\n' + str(i + 1) + '. ' + quest['answers'][i]
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def _generate_trivia_quest(client, user, topic, thread_id):
    user_id = user['_id']
    category = random.choice(trivia_categories[topic])
    url = 'https://opentdb.com/api.php?amount=1&category=' + str(category) + '&type=multiple'
    trivia = requests.get(url).json()['results'][0]
    answers = [unescape(answer) for answer in trivia['incorrect_answers']]
    correct = random.randint(0, len(answers))
    answers.insert(correct, unescape(trivia['correct_answer']))
    quest = {
        'question': unescape(trivia['question']),
        'answers': answers,
        'correct': correct
    }
    client.quest_record[user_id] = quest
    reply = user['name'] + ': ' + quest['question']
    for i, answer in enumerate(quest['answers']):
        reply += '\n' + str(i + 1) + '. ' + quest['answers'][i]
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def complete_quest(client, user, text, thread_id):
    user_id = user['_id']
    text = text.lower()
    quest = client.quest_record[user_id]
    correct = quest['correct']
    del client.quest_record[user_id]
    if text == str(correct + 1) or text == quest['answers'][correct].lower():
        delta = random.randint(10, 99)
        gold_add(user_id, delta)
        reply = user['name'] + ' has gained ' + str(delta) + ' gold and is now at '
        reply += str(user['gold'] + delta) + ' gold total!'
    else:
        delta = random.randint(-99, -10)
        gold_add(user_id, delta)
        reply = user['name'] + ' has lost ' + str(-delta) + ' gold and is now at '
        reply += str(user['gold'] + delta) + ' gold total. The correct answer was '
        reply += '"' + quest['answers'][correct] + '".'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)