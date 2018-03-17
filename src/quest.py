from fbchat.models import *
import requests
import string

from data import *
from mongo import *
from util import *

trivia_categories = list(range(9, 25)) + list(range(27, 31)) + [32]


def set_quest_type(user, text):
    quest_type = string.capwords(text)
    if quest_type in ['Vocab', 'Trivia', 'Econ', 'Gov', 'History', 'Psych', 'Science']:
        quest_type_set(user['_id'], quest_type)
        reply = 'Quest type set to ' + quest_type[0].upper() + quest_type[1:] + '.'
    else:
        reply = 'Not a valid quest type.'
    return reply


def generate_quest(quest_type):
    if quest_type == 'Vocab':
        return _generate_vocab_quest(5)
    elif quest_type == 'Econ':
        return _generate_mcq_quest(econ_dataset)
    elif quest_type == 'Gov':
        return _generate_mcq_quest(gov_dataset)
    elif quest_type == 'History':
        return _generate_mcq_quest(history_dataset)
    elif quest_type == 'Psych':
        return _generate_mcq_quest(psych_dataset)
    elif quest_type == 'Science':
        return _generate_mcq_quest(science_dataset)
    elif quest_type == 'Trivia':
        return _generate_trivia_quest()
    return None


def _generate_vocab_quest(choices):
    indices = random.sample(range(0, len(terms)), choices)
    correct = random.randint(0, choices - 1)
    if random.random() > 0.5:
        quest = {
            'Question': 'Which word means "' + definitions[indices[correct]] + '"?',
            'Answers': [terms[index] for index in indices],
            'Correct': correct
        }
    else:
        quest = {
            'Question': 'What does "' + terms[indices[correct]] + '" mean?',
            'Answers': [definitions[index] for index in indices],
            'Correct': correct
        }
    for i, answer in enumerate(quest['Answers']):
        quest['Question'] += '\n' + str(i + 1) + '. ' + quest['Answers'][i]
    return quest


def _generate_mcq_quest(dataset):
    quest = random.choice(dataset).copy()
    answers = quest['Answers']
    correct_answer = answers.pop(quest['Correct'])
    random.shuffle(answers)
    quest['Correct'] = random.randint(0, len(answers))
    answers.insert(quest['Correct'], correct_answer)
    for i, answer in enumerate(quest['Answers']):
        quest['Question'] += '\n' + str(i + 1) + '. ' + answer
    return quest


def _generate_trivia_quest():
    category = random.choice(trivia_categories)
    url = 'https://opentdb.com/api.php?amount=1&category=' + str(category) + '&type=multiple'
    trivia = requests.get(url).json()['results'][0]
    answers = [unescape(answer) for answer in trivia['incorrect_answers']]
    random.shuffle(answers)
    correct = random.randint(0, len(answers))
    answers.insert(correct, unescape(trivia['correct_answer']))
    reply = unescape(trivia['question'])
    for i, answer in enumerate(answers):
        reply += '\n' + str(i + 1) + '. ' + answer
    return {
        'Question': reply,
        'Answers': answers,
        'Correct': correct
    }


def complete_quest(client, user, text, thread_id):
    user_id = user['_id']
    quest_type = user['Quest']['Type']
    quest = client.quest_record[user_id]
    correct = quest['Correct']
    del client.quest_record[user_id]

    delta = user['GoldFlow'] / 100 + 10

    if text == str(correct + 1):
        if quest_type == 'Vocab':
            delta *= random.uniform(4, 20)
        else:
            delta *= random.uniform(6, 30)
        delta = int(delta * (1 + talent_bonus(user, Talent.MERCHANT) / 100))
        gold_add(user_id, delta)
        quest_stat_track(user_id, quest_type, True)
        reply = user['Name'] + ' has gained ' + format_num(delta, truncate=True) + ' gold and is now at '
        reply += format_num(user['Gold'] + delta, truncate=True) + ' gold total!'

    else:
        delta *= random.uniform(-10, -2)
        delta = int(delta)
        gold_add(user_id, delta)
        quest_stat_track(user_id, quest_type, False)
        reply = user['Name'] + ' has lost ' + format_num(-delta, truncate=True) + ' gold and is now at '
        reply += format_num(user['Gold'] + delta, truncate=True) + ' gold total. '
        reply += 'The correct answer was "' + quest['Answers'][correct] + '".'

    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)