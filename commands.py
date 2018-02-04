from fbchat.models import *
import random
import requests

from emoji import random_emoji
from mongo import *
from quest import generate_quest

master_id = '1564703352'

def run_user_command(client, command, text, author_id, thread_id):
    if command == 'alias' or command == 'a':
        alias, user, *_ = text.split(' ', 1) + ['']
        alias = alias.lower()
        if len(user) > 0:
            user = client.searchForUsers(user)[0]
            alias_add(user.uid, alias)
            message = Message(user.name + '\'s alias has been set to ' + alias + '.')
        else:
            user = user_from_alias(alias)
            if user:
                alias_remove(alias)
                message = Message(user['name'] + '\'s alias has been unset.')
            else:
                message = Message('Alias not found.')
        client.send(message, thread_id=thread_id)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            users = [user_from_alias(text.lower())]
            if not users:
                client.send(Message('Alias not found'), thread_id=thread_id)
                return
        else:
            users = alias_get_all()
        reply = []
        for user in users:
            line = user['alias'] + ': '
            line += '<' + user['name'] + ' (' + user['_id'] + ')>: '
            line += priority_names[priority_get(user['_id'])]
            reply.append(line)
        reply = '\n'.join(reply) if reply else 'No aliases set.'
        client.send(Message(reply), thread_id=thread_id)

    elif command == 'define' or command == 'd':
        command, text, *_ = text.split(' ', 1) + ['']
        command = command.lower()
        text = text.strip()
        if len(text) > 0:
            client.defines[command] = text
        else:
            del client.defines[command]

    elif command == 'message' or command == 'm':
        alias, reply, *_ = text.split(' ', 1) + ['']
        user = user_from_alias(alias.lower())
        if not user:
            client.send(Message('Alias not found.'), thread_id=thread_id)
        elif len(reply) > 0:
            client.send(Message(reply), thread_id=user['_id'])
        else:
            client.send(Message(emoji_size=EmojiSize.SMALL), thread_id=user['_id'])

    elif command == 'perm' or command == 'p':
        priority, alias = text.split(' ', 1)
        priority = int(priority)
        user = user_from_alias(alias.lower())
        if not user:
            message = Message('Alias not found.')
        elif user['_id'] == master_id:
            message = Message('Cannot modify master priority.')
        elif priority < 0 or priority >= priority_get(master_id):
            message = Message('Invalid priority.')
        else:
            priority_set(user['_id'], priority)
            reply = user['name'] + '\'s priority has been set to ' + str(priority)
            reply += ' (' + priority_names[priority] + ').'
            message = Message(reply)
        client.send(message, thread_id=thread_id)

    elif command == 'roll' or command == 'r':
        text = text.split(' ', 1)
        if len(text) == 2:
            count, text = text
            count = int(count)
            try: 
                int(text)
                if text[0] == '8' or (text[0:2] == '18' and len(text) % 3 == 2):
                    value = ['an ' + text, count]
                else:
                    value = ['a ' + text, count]
            except ValueError:
                value = [text, count]
            finally:
                if value[0] == client.rolls[-1][0]:
                    client.rolls[-1][1] += value[1]
                else:
                    client.rolls.append(value)
        elif len(text) == 0:
            client.rolls.clear()

    elif command == 'secret' or command == 's':
        reply = []
        if client.defines:
            section = '<Defines>\n'
            section += '\n'.join(['"' + i + '": ' + j for i, j in client.defines.items()])
            reply.append(section)
        if client.responses:
            section = '<Responses>\n'
            section += '\n'.join(['"' + i[0] + '": ' + str(i[1]) for i in client.responses])
            reply.append(section)
        if client.rolls:
            section = '<Rolls>\n'
            section += '\n'.join(['"' + i[0] + '": ' + str(i[1]) for i in client.rolls])
            reply.append(section)
        reply = '\n\n'.join(reply) if reply else 'No secrets active.'
        client.send(Message(reply), thread_id=thread_id)

    elif command == 'wong' or command == 'w':
        text = text.split(' ', 1)
        if len(text) == 2:
            count, text = text
            count = int(count)
            client.responses.append([text, count])
        elif len(text) == 1:
            client.responses.clear()

def run_group_command(client, command, text, author_id, thread_id):
    if command == 'alias' or command == 'a':
        if author_id != master_id:
            return
        alias, user, *_ = text.split(' ', 1) + ['']
        alias = alias.lower()
        if len(user) > 0:
            user = client.matchUser(thread_id, user)
            if user:
                alias_add(user.uid, alias)
                message = Message(user.name + '\'s alias has been set to ' + alias + '.')
            else:
                message = Message('User not found.')
        else:
            user = user_from_alias(alias)
            if user:
                alias_remove(alias)
                message = Message(user['name'] + '\'s alias has been unset.')
            else:
                message = Message('Alias not found.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'booli':
        message = Message('Deprecated - please use !bully instead.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'bully' or command == 'b':
        if len(text) == 0:
            user = client.fetchUserInfo(author_id)[author_id]
        else:
            user = client.matchUser(thread_id, text)
        if user:
            if exceeds_priority(user.uid, author_id):
                message = Message('{} is a cool guy.'.format(user.name))
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                user = client.fetchUserInfo(author_id)[author_id]
            url = 'https://insult.mattbas.org/api/insult.txt?who=' + user.name
            message = Message(requests.get(url).text + '.')
        else:
            message = Message('User not found.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            user = client.matchUser(thread_id, text)
            if not user:
                meessage = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            users = {user.uid: user}
        else:
            group = client.fetchGroupInfo(thread_id)[thread_id]
            users = client.fetchUserInfo(*group.participants)
        reply = []
        for user_id, user in users.items():
            line = '<' + user.name + ' (' + user.uid + ')>: '
            line += priority_names[priority_get(user_id)]
            reply.append(line)
        client.send(Message('\n'.join(reply)), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'daily' or command == 'd':
        text = text.strip().lower()
        if text not in ['color', 'emoji']:
            return
        subscriptions = subscription_get(thread_id)
        if text in subscriptions:
            subscription_remove(thread_id, text)
            reply = 'This conversation has been unsubscribed from daily ' + text + 's.'
        else:
            subscription_add(thread_id, text)
            reply = 'This conversation has been subscribed to daily ' + text + 's.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'exp' or command == 'e':
        user = user_from_id(author_id)
        reply = user['name'] + ' has ' + str(user['experience']) + ' experience total.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'image' or command == 'i':
        if len(text) > 0:
            image = image_get(author_id, int(text)) % 96
            if image:
                path = './images/' + str(image) + '.jpg'
                client.sendLocalImage(path, thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            reply = 'You have ' + str(len(user_from_id(author_id)['images'])) + ' images.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'mute' or command == 'm':
        if len(text) == 0:
            client.removeUserFromGroup(author_id, thread_id)
            return
        user = client.matchUser(thread_id, text)
        if user:
            if exceeds_priority(user.uid, author_id):
                client.removeUserFromGroup(author_id, thread_id)
            else:
                client.removeUserFromGroup(user.uid, thread_id)
        else:
            message = Message('User not found.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'perm' or command == 'p':
        if author_id == master_id:
            priority, user = text.split(' ', 1)
            priority = int(priority)
            user = client.matchUser(thread_id, user)
            if not user:
                message = Message('User not found.')
            elif user.uid == master_id:
                message = Message('Cannot modify master priority.')
            elif priority < 0 or priority >= priority_get(master_id):
                message = Message('Invalid priority.')
            else:
                priority_set(user.uid, priority)
                reply = user.name + '\'s priority has been set to ' + str(priority)
                reply += ' (' + priority_names[priority] + ').'
                message = Message(reply)
        else:
            user = client.fetchUserInfo(author_id)[author_id]
            reply = user.name + '\'s priority has been set to 0'
            reply += ' (' + priority_names[0] + ').'
            message = Message(reply)
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'quest' or command == 'q':
        user = user_from_id(author_id)
        experience = user['experience']
        quest = generate_quest(1 if experience < 0 else len(str(experience)))
        client.quest_record[author_id] = quest
        reply = user['name'] + ', which word means "' + quest['question'] + '"?'
        for i, answer in enumerate(quest['answers']):
            reply += '\n' + str(i + 1) + '. ' + quest['answers'][i]
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'roll' or command == 'r':
        user = client.fetchUserInfo(author_id)[author_id]
        if author_id == master_id and client.rolls:
            roll = client.rolls[0][0]
            client.rolls[0][1] -= 1
            if client.rolls[0][1] == 0:
                client.rolls.pop(0)
        elif len(text) == 0:
            roll = 'a ' + str(random.randint(1, 6))
        elif len(text) > 0 and int(text) > 0:
            roll = str(random.randint(1, int(text)))
            if roll[0] == '8' or (roll[0:2] == '18' and len(roll) % 3 == 2):
                roll = 'an ' + roll
            else:
                roll = 'a ' + roll
        else:
            return
        message = Message(user.name + ' rolls ' + roll + '.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'shop' or command == 's':
        text = text.strip().lower()
        if len(text) == 0:
            reply = ['<Wong\'s Shoppe>']
            reply.append('1. 0100 exp: Charity donation')
            reply.append('2. 1000 exp: Reaction image')
            reply.append('3. 9999 exp: Rank boost')
            reply.append('(Buy things with "!shop <item>")')
            reply = '\n'.join(reply)
        else:
            text = int(text)
            experience = experience_get(author_id)
            if text == 1 and experience >= 100:
                charities = [
                    'Flat Earth Society', 
                    'Westboro Baptist Church', 
                    'Church of Scientology'
                ]
                experience_add(author_id, -100)
                reply = 'The ' + random.choice(charities) + ' thanks you for your donation.'
            elif text == 2 and experience >= 1000:
                experience_add(author_id, -1000)
                image = random.randint(0, 999999)
                image_add(author_id, image)
                reply = 'You\'ve received an image!\n'
                reply += 'It has been placed in slot ' + str(image_count(author_id)) + '.\n'
                reply += '(Use it with "!image <slot>")'
            elif text == 3 and experience >= 9999:
                priority = priority_get(author_id) + 1
                if priority < priority_get(master_id):
                    experience_add(author_id, -9999)
                    priority_set(author_id, priority)
                    name = user_from_id(author_id)['name']
                    reply = name + '\'s rank is now ' + priority_names[priority] + '!'
                else:
                    reply = 'You\'ve already reached the highest rank.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'test' or command == 't':
        colors = list(ThreadColor)
        group = client.fetchGroupInfo(thread_id)[thread_id]
        color = group.color
        while color == group.color:
            color = random.choice(colors)
        client.changeThreadColor(color, thread_id=thread_id)
        emoji = group.emoji
        while emoji == group.emoji:
            emoji = random_emoji()
        client.changeThreadEmoji(emoji, thread_id=thread_id)