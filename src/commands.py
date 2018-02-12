from fbchat.models import *
from datetime import datetime
import random
import requests

from battle import generate_battle
from craft import generate_craft_info, craft_item
from data import random_emoji
from info import generate_user_info, generate_group_info
from location import location_features, explore_location
from mongo import *
from quest import set_quest_type, generate_quest
from shop import generate_shop_info, shop_purchase
from travel import check_travel, travel_to_location
from util import *


def run_user_command(client, author, command, text):
    author_id = author['_id']
    if author_id != master_id:
        return

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
                message = Message(user['Name'] + '\'s alias has been unset.')
            else:
                message = Message('Alias not found.')
        client.send(message, thread_id=author_id)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            users = [user_from_alias(text.lower())]
            if not users[0]:
                client.send(Message('Alias not found.'), thread_id=author_id)
                return
        else:
            users = alias_get_all()
        reply = []
        for user in users:
            reply.append(_check_to_string(client, user))
        reply = '\n\n'.join(reply) if reply else 'No aliases set.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'define' or command == 'd':
        command, text, *_ = text.split(' ', 1) + ['']
        command = command.lower()
        text = text.strip()
        if len(text) > 0:
            client.defines[command] = text
        elif len(command) > 0:
            del client.defines[command]

    elif command == 'help' or command == 'h':
        generate_user_info(client, text, author)

    elif command == 'message' or command == 'm':
        alias, reply, *_ = text.split(' ', 1) + ['']
        user = user_from_alias(alias.lower())
        if not user:
            client.send(Message('Alias not found.'), thread_id=author_id)
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
        elif priority < 0 or priority >= master_priority:
            message = Message('Invalid priority.')
        else:
            priority_set(user['_id'], priority)
            reply = user['Name'] + '\'s priority has been set to ' + str(priority)
            reply += ' (' + priority_names[priority] + ').'
            message = Message(reply)
        client.send(message, thread_id=author_id)

    elif command == 'secret' or command == 's':
        reply = []
        if client.defines:
            section = '<<Defines>>\n'
            section += '\n'.join(['"' + i + '": ' + j for i, j in client.defines.items()])
            reply.append(section)
        if client.responses:
            section = '<<Responses>>\n'
            section += '\n'.join(['"' + response + '"' for response in client.responses])
            reply.append(section)
        reply = '\n\n'.join(reply) if reply else 'No secrets active.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'wong' or command == 'w':
        if len(text) > 0:
            client.responses.append(text)
        elif len(text) == 1:
            client.responses.clear()


def run_group_command(client, author, command, text, thread_id):
    author_id = author['_id']

    if command == 'alias' or command == 'a':
        if author_id == master_id:
            alias, user, *_ = text.split(' ', 1) + ['']
            alias = alias.lower()
            if len(user) > 0:
                user = client.match_user(thread_id, user)
                if user:
                    alias_add(user.uid, alias)
                    reply = user.name + '\'s alias has been set to ' + alias + '.'
                else:
                    reply = 'User not found.'
            else:
                user = user_from_alias(alias)
                if user:
                    alias_remove(alias)
                    reply = user['Name'] + '\'s alias has been unset.'
                else:
                    reply = 'Alias not found.'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'battle' or command == 'b':
        if _check_busy(client, author, thread_id):
            return
        elif client.user_health.get(author_id, author['Stats']['HP']) <= 0:
            reply = 'You\'re on the brink of death! Wait until the next hour or '
            reply += 'buy a life elixir from the shop to restore your health.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            generate_battle(client, author, thread_id)

    elif command == 'bully':
        if len(text) == 0:
            user = client.fetchUserInfo(author_id)[author_id]
        else:
            user = client.match_user(thread_id, text)
        if user:
            if exceeds_priority(user.uid, author_id):
                reply = user.name + ' is a cool guy.'
                client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
                user = client.fetchUserInfo(author_id)[author_id]
            url = 'https://insult.mattbas.org/api/insult.txt?who=' + user.name
            reply = requests.get(url).text + '.'
        else:
            reply = 'User not found.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            user = client.match_user(thread_id, text)
            if not user:
                message = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            user = user_from_id(user.uid)
        else:
            user = author
        reply = _check_to_string(client, user)
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'craft':
        if _check_busy(client, author, thread_id):
            return
        elif 'Crafting' not in location_features(author['Location']):
            reply = 'There is no crafting station in this location. '
            reply += 'Try going to Perion or Sleepywood.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif len(text) == 0:
            generate_craft_info(client, author, thread_id)
        else:
            craft_item(client, author, text, thread_id)

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

    elif command == 'equip':
        if len(text) > 0:
            user = client.match_user(thread_id, text)
            if not user:
                message = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            user = user_from_id(user.uid)
        else:
            user = author
        weapon = user['Equipment']['Weapon']
        armor = user['Equipment']['Armor']
        reply = '<<Equipment>>\n'
        reply += 'Weapon: ' + weapon['Name'] + '\n'
        reply += '-> ATK: ' + str(weapon['ATK']) + '\n'
        reply += '-> DEF: ' + str(weapon['DEF']) + '\n'
        reply += '-> SPD: ' + str(weapon['SPD']) + '\n'
        reply += 'Armor: ' + armor['Name'] + '\n'
        reply += '-> ATK: ' + str(armor['ATK']) + '\n'
        reply += '-> DEF: ' + str(armor['DEF']) + '\n'
        reply += '-> SPD: ' + str(armor['SPD'])
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'explore' or command == 'e':
        if author_id in client.explore_record:
            reply = 'You can only explore once per hour.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif not _check_busy(client, author, thread_id):
            if author_id != master_id:
                client.explore_record.add(author_id)
            explore_location(client, author, thread_id)

    elif command == 'give' or command == 'g':
        amount, user = text.split(' ', 1)
        amount = int(amount)
        if amount < 1 and author_id != master_id:
            reply = 'Invalid amount of gold.'
        else:
            user = client.match_user(thread_id, user)
            gold = author['Gold']
            if gold < amount:
                reply = 'Not enough gold.'
            elif author_id == user.uid:
                reply = 'Cannot give gold to self.'
            else:
                gold_add(author_id, -amount)
                gold_add(user.uid, amount)
                reply = author['Name'] + ' gives ' + str(amount)
                reply += ' gold to ' + user.name + '.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'help' or command == 'h':
        generate_group_info(client, text, author, thread_id)

    elif command == 'inventory' or command == 'i':
        reply = 'Your inventory has been sent to you. Check your private messages (or message requests).'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        reply = ['<<Inventory>>']
        for item, amount in author['Inventory'].items():
            reply.append(item + ' x ' + str(amount))
        reply = '\n'.join(reply) if len(reply) > 1 else 'Your inventory is empty.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'jail' or command == 'j':
        if author['Priority'] >= master_priority - 1:
            if len(text) == 0:
                reply = 'Please specify a user.'
            else:
                user = client.match_user(thread_id, text)
                if not user:
                    message = Message('User not found.')
                    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                    return
                user = user_from_id(user.uid)
                if user['_id'] == master_id and author_id != master_id:
                    user = author
                if location_names_reverse[user['Location']] == 0:
                    location_set(user['_id'], location_names[1])
                    if client.user_states.get(user['_id'], (UserState.Idle, {}))[0] == UserState.Travel:
                        del client.travel_record[user['_id']]
                    reply = user['Name'] + ' has been freed from jail.'
                else:
                    location_set(user['_id'], location_names[0])
                    if client.user_states.get(user['_id'], (UserState.Idle, {}))[0] == UserState.Travel:
                        del client.travel_record[user['_id']]
                    reply = user['Name'] + ' has been sent to jail!'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'location' or command == 'l':
        if _check_busy(client, author, thread_id):
            return
        features = location_features(author['Location'])
        reply = 'Welcome to ' + author['Location'] + '! '
        if features:
            reply += 'The following services are available here:'
            for feature in features:
                reply += '\n-> ' + feature
        else:
            reply += 'There are no services available here.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'mute' or command == 'm':
        if len(text) == 0:
            client.removeUserFromGroup(author_id, thread_id)
            return
        user = client.match_user(thread_id, text)
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
            user = client.match_user(thread_id, user)
            if not user:
                reply = 'User not found.'
            elif user.uid == master_id:
                reply = 'Cannot modify master priority.'
            elif priority < 0 or priority >= master_priority:
                reply = 'Invalid priority.'
            else:
                priority_set(user.uid, priority)
                reply = user.name + '\'s priority has been set to ' + str(priority)
                reply += ' (' + priority_names[priority] + ').'
        else:
            user = client.fetchUserInfo(author_id)[author_id]
            reply = user.name + '\'s priority has been set to 0'
            reply += ' (' + priority_names[0] + ').'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'quest' or command == 'q':
        if len(text) > 0:
            reply = set_quest_type(author, text)
        elif location_names_reverse[author['Location']] == 0:
            reply = 'There are no quests to be found here.'
        else:
            quest = generate_quest(author['Quest']['Type'])
            client.quest_record[author_id] = quest
            reply = author['Name'] + ': ' + quest['Question']
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'random':
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

    elif command == 'roll' or command == 'r':
        user = client.fetchUserInfo(author_id)[author_id]
        if len(text) == 0:
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

    elif command == 'score':
        group = client.fetchGroupInfo(thread_id)[thread_id].participants
        group = user_get_all_in(list(group))
        users = sorted(group, key=lambda x: calculate_score(x), reverse=True)
        users = [user for user in users if user['_id'] != master_id and user['_id'] != client.uid]
        while calculate_score(users[-1]) == 0:
            users.pop()
        try:
            page = int(text) - 1
        except:
            page = 0
        if len(users) <= page * 9:
            reply = 'There aren\'t enough players in the chat.'
        else:
            users = users[(page * 9):]
            if len(users) > 9:
                users = users[:9]
            reply = '<<Chat Scoreboard>>'
            for i, user in enumerate(users):
                reply += '\n' + str(page * 9 + i + 1) + '. ' + user['Name']
                reply += ' (' + str(calculate_score(user)) + ' points)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'shop' or command == 's':
        if _check_busy(client, author, thread_id):
            return
        elif 'Shop' not in location_features(author['Location']):
            message = Message('There is no shop in this location.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif len(text) == 0:
            generate_shop_info(client, author, thread_id)
        else:
            shop_purchase(client, author, text, thread_id)

    elif command == 'travel' or command == 't':
        if not _check_busy(client, author, thread_id):
            if len(text) == 0:
                check_travel(client, author, thread_id)
            else:
                travel_to_location(client, author, text, thread_id)


def _check_busy(client, user, thread_id):
    user_id = user['_id']
    if user_id not in client.user_states:
        return False

    state, details = client.user_states[user_id]

    # Check if user has finished traveling
    if state == UserState.Travel:
        seconds = int((details['EndTime'] - datetime.now()).total_seconds())
        minutes, seconds = seconds // 60, seconds % 60
        reply = 'You\'re busy traveling to ' + details['Destination'] + '. ('
        reply += ((str(minutes) + ' min ') if minutes > 0 else '')
        reply += str(seconds) + ' secs remaining)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    # Check if user is in battle
    elif state == UserState.Battle:
        reply = 'You\'re busy fighting a level ' + str(details['Monster']['Level'])
        reply += ' ' + details['Monster']['Name'] + '!'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    return True


def _check_to_string(client, user):
    text = '<<' + user['Name'] + '>>' + ((' (' + user['Alias'] + ')\n') if 'Alias' in user else '\n')
    text += 'Priority: ' + priority_names[user['Priority']] + '\n'
    text += 'Level: ' + str(user['Stats']['Level']) + ' (' + str(user['Stats']['EXP']) + '/100 exp)\n'
    text += 'Health: ' + str(client.user_health.get(user['_id'], user['Stats']['HP'])) + \
            '/' + str(user['Stats']['HP']) + '\n'
    text += 'Stats: ' + str(user['Stats']['ATK']) + '/' + str(user['Stats']['DEF']) + \
            '/' + str(user['Stats']['SPD']) + '\n'
    text += 'Gold: ' + str(user['Gold']) + ' (+' + str(user['GoldFlow']) + '/hour)\n'
    text += 'Location: ' + user['Location']
    state, details = client.user_states.get(user['_id'], (UserState.Idle, {}))
    if state == UserState.Travel:
        seconds = int((details['EndTime'] - datetime.now()).total_seconds())
        minutes, seconds = seconds // 60, seconds % 60
        text += ' -> ' + details['Destination'] + '\n('
        text += ((str(minutes) + ' min ') if minutes > 0 else '')
        text += str(seconds) + ' secs remaining)'
    elif state == UserState.Battle:
        text += '\n(In battle with ' + details['Monster']['Name'] + ')'
    return text