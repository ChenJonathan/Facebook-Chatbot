import requests

from battle import generate_battle, cancel_battle
from craft import generate_craft_info, craft_item
from data import random_emoji, patch_notes
from duel import send_duel_request, cancel_duel_request, cancel_duel
from enums import ChatState
from info import generate_user_info, generate_group_info
from location import *
from mongo import *
from quest import set_quest_type, generate_quest
from shop import generate_shop_info, shop_purchase
from util import *


def run_user_command(client, author, command, text):
    author_id = author['_id']

    if command == 'alias' or command == 'a':
        alias, user, *_ = text.split(' ', 1) + ['']
        alias = alias.lower()
        if len(alias) == 0:
            generate_user_info(client, author, 'alias')
            return
        elif len(user) > 0:
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
            reply = '!' + command + ' has been redefined!'
        elif len(command) > 0:
            del client.defines[command]
            reply = '!' + command + ' has been cleared to default.'
        else:
            generate_user_info(client, author, 'define')
            return
        client.send(Message(reply), thread_id=author_id)

    elif command == 'equip' or command == 'e':
        try:
            level, attack, defence, speed = [int(num) for num in text.split(' ')]
            level_set(author_id, level)
            equip_item(author_id, 'Weapon', {
                'Name': 'Oversized Banhammer',
                'ATK': attack,
                'DEF': 0,
                'SPD': 0
            })
            equip_item(author_id, 'Armor', {
                'Name': 'Master Priority',
                'ATK': 0,
                'DEF': defence,
                'SPD': 0
            })
            equip_item(author_id, 'Accessory', {
                'Name': 'CTCI, 7th Edition',
                'ATK': 0,
                'DEF': 0,
                'SPD': speed
            })
        except:
            generate_user_info(client, author, 'equip')
        else:
            client.send(Message('Level and stats changed!'), thread_id=author_id)

    elif command == 'explore':
        reply = str(len(client.explore_record))
        reply += (' person has' if len(client.explore_record) == 1 else ' people have')
        reply += ' explored this hour.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'help' or command == 'h':
        generate_user_info(client, author, text)

    elif command == 'message' or command == 'm':
        alias, reply, *_ = text.split(' ', 1) + ['']
        if len(alias) == 0:
            generate_user_info(client, author, 'message')
            return
        user = user_from_alias(alias.lower())
        if not user:
            client.send(Message('Alias not found.'), thread_id=author_id)
        elif len(reply) > 0:
            client.send(Message(reply), thread_id=user['_id'])
        else:
            client.send(Message(emoji_size=EmojiSize.SMALL), thread_id=user['_id'])

    elif command == 'perm' or command == 'p':
        try:
            priority, alias = text.split(' ', 1)
            priority = int(priority)
        except:
            generate_user_info(client, author, 'perm')
            return
        user = user_from_alias(alias.lower())
        if not user:
            message = Message('Alias not found.')
        elif user['_id'] == master_id:
            message = Message('Cannot modify master priority.')
        elif priority < 0 or priority >= master_priority:
            message = Message('Invalid priority value.')
        else:
            priority_set(user['_id'], priority)
            reply = user['Name'] + '\'s priority has been set to ' + str(priority)
            reply += ' (' + priority_names[priority] + ').'
            message = Message(reply)
        client.send(message, thread_id=author_id)

    elif command == 'response' or command == 'r':
        if len(text) > 0:
            client.responses.append(text)
            reply = 'Response added!'
        else:
            client.responses.clear()
            reply = 'All responses cleared.'
        client.send(Message(reply), thread_id=author_id)

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

    elif command == 'warp' or command == 'w':
        if len(text) == 0:
            generate_group_info(client, author, 'warp', author_id)
            return
        location = query_location(text)
        if location is None:
            reply = 'Not a valid location.'
        else:
            location_set(author_id, location)
            if client.user_states.get(author_id, (UserState.IDLE, {}))[0] == UserState.TRAVEL:
                del client.user_states[author_id]
            reply = 'You have been warped to ' + location + '!'
        client.send(Message(reply), thread_id=author_id)

    else:
        client.send(Message('Not a valid command.'), thread_id=author_id)


def run_group_command(client, author, command, text, thread_id):
    author_id = author['_id']

    if command == 'alias' or command == 'a':
        if author_id == master_id:
            alias, user, *_ = text.split(' ', 1) + ['']
            alias = alias.lower()
            if len(alias) == 0:
                generate_group_info(client, author, 'alias', thread_id)
                return
            elif len(user) > 0:
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
        elif client.user_health.get(author_id, author['Stats']['Health']) <= 0:
            now = datetime.today()
            later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
            reply = 'You\'re on the brink of death! Buy a life elixir from the shop '
            reply += 'or wait until the next hour to restore your health. ('
            reply += format_time((later - now).seconds) + ' remaining)'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            generate_battle(client, author, thread_id)

    elif command == 'bully':
        if len(text) == 0:
            generate_group_info(client, author, 'bully', thread_id)
            return
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
            reply = 'There is no crafting station in this location. Try looking elsewhere.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif len(text) == 0:
            generate_craft_info(client, author, thread_id)
        else:
            try:
                slot = int(text)
            except:
                generate_group_info(client, author, 'craft', thread_id)
            else:
                craft_item(client, author, slot, thread_id)

    elif command == 'daily':
        if text not in ['color', 'emoji']:
            generate_group_info(client, author, 'daily', thread_id)
            return
        subscriptions = subscription_get(thread_id)
        if text in subscriptions:
            subscription_remove(thread_id, text)
            reply = 'This conversation has been unsubscribed from daily ' + text + 's.'
        else:
            subscription_add(thread_id, text)
            reply = 'This conversation has been subscribed to daily ' + text + 's.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'duel' or command == 'd':
        state, details = client.user_states.get(author_id, (UserState.IDLE, {}))
        request = state == UserState.DUEL and details['Status'] == ChatState.REQUEST
        if not request and _check_busy(client, author, thread_id):
            return
        elif text.lower() == 'cancel':
            cancel_duel_request(client, author, thread_id)
        elif len(text) > 0:
            try:
                amount, user = text.split(' ', 1)
                amount = int(amount)
                assert amount >= 0
            except:
                reply = 'Invalid amount of gold.'
            else:
                user = client.match_user(thread_id, user)
                gold = author['Gold']
                if request:
                    gold += details['Gold']
                if gold < amount:
                    reply = 'Not enough gold.'
                elif user is None:
                    reply = 'User not found.'
                elif author_id == user.uid:
                    reply = 'You can\'t duel yourself.'
                else:
                    send_duel_request(client, author, user_from_id(user.uid), amount, thread_id)
                    return
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            generate_group_info(client, author, 'duel', thread_id)

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
        accessory = user['Equipment']['Accessory']
        reply = '<<' + user['Name'] + '>>\n'
        reply += 'Weapon: ' + weapon['Name'] + '\n'
        reply += '-> ATK: ' + format_num(weapon['ATK'], sign=True) + '\n'
        reply += '-> DEF: ' + format_num(weapon['DEF'], sign=True) + '\n'
        reply += '-> SPD: ' + format_num(weapon['SPD'], sign=True) + '\n'
        reply += 'Armor: ' + armor['Name'] + '\n'
        reply += '-> ATK: ' + format_num(armor['ATK'], sign=True) + '\n'
        reply += '-> DEF: ' + format_num(armor['DEF'], sign=True) + '\n'
        reply += '-> SPD: ' + format_num(armor['SPD'], sign=True) + '\n'
        reply += 'Accessory: ' + accessory['Name'] + '\n'
        reply += '-> ATK: ' + format_num(accessory['ATK'], sign=True) + '\n'
        reply += '-> DEF: ' + format_num(accessory['DEF'], sign=True) + '\n'
        reply += '-> SPD: ' + format_num(accessory['SPD'], sign=True)
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'explore' or command == 'e':
        if author_id in client.explore_record:
            now = datetime.today()
            later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
            reply = 'You can only explore once per hour. ('
            reply += format_time((later - now).seconds) + ' remaining)'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif not _check_busy(client, author, thread_id):
            if author_id != master_id:
                client.explore_record.add(author_id)
            explore_location(client, author, thread_id)

    elif command == 'flee' or command == 'f':
        state, details = client.user_states.get(author_id, (UserState.IDLE, {}))
        if state == UserState.BATTLE:
            cancel_battle(client, author)
        elif state == UserState.DUEL:
            cancel_duel(client, author)

    elif command == 'give' or command == 'g':
        try:
            amount, user = text.split(' ', 1)
            assert len(amount) > 0
        except:
            generate_group_info(client, author, 'give', thread_id)
            return
        try:
            amount = int(amount)
            assert amount > 0 or author_id == master_id
        except:
            reply = 'Invalid amount of gold.'
        else:
            user = client.match_user(thread_id, user)
            if author['Gold'] < amount:
                reply = 'Not enough gold.'
            elif user is None:
                reply = 'User not found.'
            elif author_id == user.uid:
                reply = 'Cannot give gold to self.'
            else:
                gold_add(author_id, -amount)
                gold_add(user.uid, amount)
                reply = author['Name'] + ' gives ' + str(amount)
                reply += ' gold to ' + user.name + '.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'help' or command == 'h':
        generate_group_info(client, author, text, thread_id)

    elif command == 'inventory' or command == 'i':
        reply = 'Your inventory has been sent to you. Check your private messages (or message requests).'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        reply = ['<<Inventory>>']
        for item_key in sorted(author['Inventory'].keys(), key=lambda x: Item[x].value):
            reply.append('-> ' + item_key + ' x ' + str(author['Inventory'][item_key]))
        reply = '\n'.join(reply) if len(reply) > 1 else 'Your inventory is empty.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'jail' or command == 'j':
        if author['Priority'] >= master_priority - 1:
            if len(text) == 0:
                generate_group_info(client, author, 'jail', thread_id)
                return
            user = client.match_user(thread_id, text)
            if not user:
                message = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            user = user_from_id(user.uid)
            if user['_id'] == master_id and author_id != master_id:
                user = author
            if Location[user['Location']] == Location['Maple Island']:
                location_set(user['_id'], Location['Lith Harbor'].name)
                if client.user_states.get(user['_id'], (UserState.IDLE, {}))[0] == UserState.TRAVEL:
                    del client.user_states[user['_id']]
                reply = user['Name'] + ' has been freed from jail.'
            else:
                location_set(user['_id'], Location['Maple Island'].name)
                if client.user_states.get(user['_id'], (UserState.IDLE, {}))[0] == UserState.TRAVEL:
                    del client.user_states[user['_id']]
                reply = user['Name'] + ' has been sent to jail!'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'map' or command == 'm':
        region = location_region(author['Location'])
        if region is None:
            message = Message('No map available for this region.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            path = './images/' + region.value + '.png'
            client.sendLocalImage(path, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'mute':
        if len(text) == 0:
            generate_group_info(client, author, 'mute', thread_id)
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

    elif command == 'notes' or command == 'n':
        reply = '<<Patch Notes>>\n\n' + patch_notes
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'perm' or command == 'p':
        if author_id == master_id:
            try:
                priority, user = text.split(' ', 1)
                priority = int(priority)
            except:
                generate_group_info(client, author, 'perm', thread_id)
                return
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
            user = user_from_id(author_id)
            reply = user['Name'] + '\'s priority has been set to 0'
            reply += ' (' + priority_names[0] + ').'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'quest' or command == 'q':
        if len(text) > 0:
            reply = set_quest_type(author, text)
        elif Location[author['Location']] == Location['Maple Island']:
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
        else:
            try:
                text = int(text)
                assert text > 0
            except:
                generate_group_info(client, author, 'roll', thread_id)
                return
            roll = str(random.randint(1, text))
            if roll[0] == '8' or (roll[0:2] == '18' and len(roll) % 3 == 2):
                roll = 'an ' + roll
            else:
                roll = 'a ' + roll
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
            assert page >= 0
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
            try:
                slot, amount, *_ = text.split(' ', 1) + ['']
                slot = int(slot)
                amount = int(amount) if len(amount) > 0 else 1
            except:
                generate_group_info(client, author, 'shop', thread_id)
            else:
                shop_purchase(client, author, slot, amount, thread_id)

    elif command == 'travel' or command == 't':
        if text.lower() == 'cancel':
            if client.user_states.get(author_id, (UserState.IDLE, {}))[0] == UserState.TRAVEL:
                del client.user_states[author_id]
                reply = author['Name'] + '\'s journey has been cancelled.'
            else:
                reply = 'You are not currently traveling anywhere.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif not _check_busy(client, author, thread_id):
            if len(text) == 0:
                check_travel(client, author, thread_id)
            else:
                travel_to_location(client, author, text, thread_id)

    elif command == 'warp' or command == 'w':
        if author_id == master_id:
            if len(text) == 0:
                generate_group_info(client, author, 'warp', author_id)
                return
            location = query_location(text)
            if location is None:
                reply = 'Not a valid location.'
            else:
                location_set(author_id, location)
                if client.user_states.get(author_id, (UserState.IDLE, {}))[0] == UserState.TRAVEL:
                    del client.user_states[author_id]
                reply = 'You have been warped to ' + location + '!'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    else:
        client.send(Message('Not a valid command.'), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _check_busy(client, user, thread_id):
    user_id = user['_id']
    if user_id not in client.user_states:
        return False

    state, details = client.user_states[user_id]

    if state == UserState.TRAVEL:
        seconds = int((details['EndTime'] - datetime.now()).total_seconds())
        reply = 'You\'re busy traveling to ' + details['Destination'] + '. (' + format_time(seconds) + ' remaining)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif state == UserState.BATTLE:
        reply = 'You\'re busy fighting a level ' + str(details['Monster']['Level'])
        reply += ' ' + details['Monster']['Name'] + '!'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif state == UserState.DUEL:
        if details['Status'] == ChatState.REQUEST:
            opponent_id, gold = details['OpponentID'], details['Gold']
            reply = 'You\'re busy requesting a duel with ' + user_from_id(opponent_id)['Name']
            reply += ' for ' + str(gold) + ' gold!'
        else:
            opponent = user_from_id(details['OpponentID'])
            reply = 'You\'re busy dueling ' + opponent['Name'] + ' for ' + str(details['Gold']) + ' gold!'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    return True


def _check_to_string(client, user):
    state, details = client.user_states.get(user['_id'], (UserState.IDLE, {}))

    text = '<<' + user['Name'] + '>>' + ((' (' + user['Alias'] + ')\n') if 'Alias' in user else '\n')
    text += 'Priority: ' + priority_names[user['Priority']] + '\n'
    text += 'Level: ' + str(user['Stats']['Level']) + ' (' + str(user['Stats']['Experience']) + '/100 exp)\n'
    base_stat_val = str(base_stat(user['Stats']['Level']))
    text += '-> ATK: ' + str(total_atk(user)) + ' (' + base_stat_val + format_num(equip_atk(user), sign=True) + ')\n'
    text += '-> DEF: ' + str(total_def(user)) + ' (' + base_stat_val + format_num(equip_def(user), sign=True) + ')\n'
    text += '-> SPD: ' + str(total_spd(user)) + ' (' + base_stat_val + format_num(equip_spd(user), sign=True) + ')\n'
    text += 'Health: ' + str(client.user_health.get(user['_id'], user['Stats']['Health'])) + \
            '/' + str(user['Stats']['Health']) + '\n'
    text += 'Gold: ' + format_num(user['Gold'], truncate=True)
    text += ' (' + format_num(user['GoldFlow'], sign=True, truncate=True) + '/hour)\n'
    text += 'Location: ' + user['Location']

    if state == UserState.TRAVEL:
        seconds = int((details['EndTime'] - datetime.now()).total_seconds())
        text += ' -> ' + details['Destination'] + '\n(' + format_time(seconds) + ' remaining)'
    elif state == UserState.BATTLE:
        text += '\n(In battle with ' + details['Monster']['Name'] + ')'
    elif state == UserState.DUEL:
        if details['Status'] != ChatState.REQUEST:
            opponent = user_from_id(details['OpponentID'])
            text += '\n(In a duel with ' + opponent['Name'] + ')'

    return text