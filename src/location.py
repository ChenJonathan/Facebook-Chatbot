from fbchat.models import *
import math
import random

from data import random_beast
from mongo import *
from travel import edges
from util import location_names, location_names_reverse

feature_map = {
    'Lith Harbor': ['Shop'],
    'Henesys': ['Shop'],
    'Ellinia': ['Meditation - Coming soon!', 'Shop'],
    'Perion': ['Crafting', 'Shop'],
    'Kerning City': ['Shop'],
    'Sleepywood': ['Crafting', 'Shop'],
    'Cursed Sanctuary': ['Boss Fight - Coming soon!'],
    'New Leaf City': ['Gambling - Coming soon!', 'Shop']
}


def location_features(location):
    return feature_map.get(location, [])


def explore_location(client, user, thread_id):
    seed = random.uniform(0.8, 1.2)
    location = location_names_reverse[user['Location']]

    # Apply location specific modifiers
    gold_multiplier = 1
    beast_multiplier = 1
    item_drop_rates = {}
    if location == 0:
        gold_multiplier = 0
        beast_multiplier = 0
    elif location == 1:
        gold_multiplier = 0.5
        item_drop_rates['Bottled Light'] = 0.1
    elif location == 2:
        beast_multiplier = 3
        item_drop_rates['Wild Essence'] = 0.7
    elif location == 3:
        item_drop_rates['Arcane Essence'] = 0.7
        item_drop_rates['Crystal Shard'] = 0.1
        item_drop_rates['Breathing Wood'] = 0.5
    elif location == 4:
        item_drop_rates['Brutal Essence'] = 0.7
        item_drop_rates['Drop of Earth'] = 0.2
        item_drop_rates['Iron Shard'] = 0.5
    elif location == 5:
        item_drop_rates['Void Essence'] = 0.7
        item_drop_rates['Bottled Darkness'] = 0.1
    elif location == 6:
        beast_multiplier = 0
        item_drop_rates['Breathing Wood'] = 0.5
        item_drop_rates['Shifting Vines'] = 0.2
    elif location == 7:
        beast_multiplier = 0
        item_drop_rates['Arcane Essence'] = 0.3
        item_drop_rates['Void Essence'] = 0.3
        item_drop_rates['Bottled Darkness'] = 0.1
        item_drop_rates['Touch of Death'] = 0.05
        item_drop_rates['Warped Bones'] = 0.1
    elif location == 8:
        gold_multiplier = 2
        beast_multiplier = 0
    elif location == 9:
        beast_multiplier = 5
        item_drop_rates['Wild Essence'] = 0.4
        item_drop_rates['Breathing Wood'] = 0.5
        item_drop_rates['Shifting Vines'] = 0.5
    elif location == 10:
        item_drop_rates['Howling Wind'] = 0.1
        item_drop_rates['Clockwork Shard'] = 0.6
        item_drop_rates['Time Shard'] = 0.05
    elif location == 11:
        pass
    elif location == 12:
        pass
    elif location == 13:
        pass
    elif location == 14:
        pass
    elif location == 15:
        pass
    elif location == 16:
        pass
    elif location == 17:
        pass
    elif location == 18:
        pass
    elif location == 19:
        pass
    elif location == 20:
        pass
    elif location == 21:
        pass
    elif location == 22:
        pass
    elif location == 23:
        pass
    elif location == 24:
        pass
    elif location == 25:
        pass
    elif location == 26:
        pass
    elif location == 27:
        pass

    # Calculate item drops
    item_drops = {}
    for item, rate in item_drop_rates.items():
        trials = []
        for _ in range(9):
            amount = 0
            while rate > random.random():
                amount += 1
            trials.append(amount)
        final_amount = sorted(trials)[-3]
        if final_amount > 0:
            item_drops[item] = final_amount
            inventory_add(user['_id'], item, final_amount)

    # Calculate gold gain
    delta_gold = int(seed * (250 + random.randint(-50, 50)) * gold_multiplier)
    gold_add(user['_id'], delta_gold)

    # Check for discovered hunting pet
    beast = None
    if seed / 100 * beast_multiplier > random.random():
        beast = random_beast()
        delta_rate = beast[1] * beast[2]
        gold_rate_add(user['_id'], delta_rate)

    # Check for discovered location
    current = location_names_reverse[user['Location']]
    progress = user['LocationProgress']
    unlocked = []
    presence = False
    for i, time in enumerate(edges[current]):
        if time >= 0 and progress.get(location_names[i], 0) < 1:
            new_progress = progress.get(location_names[i], 0) + seed / edges[current][i]
            if new_progress >= 1:
                location_progress_set(user['_id'], location_names[i], 1)
                unlocked.append(i)
            else:
                location_progress_set(user['_id'], location_names[i], new_progress)
                presence = True

    # Create message
    reply = []
    line = 'You spent some time exploring ' + location_names[current]
    line += ' and found ' + str(delta_gold) + ' gold.'
    reply.append(line)
    if beast:
        line = 'A wild ' + str(beast[1]) + '/' + str(beast[2]) + ' '
        line += beast[0] + ' took a liking to you! It follows you around, '
        line += 'granting you an additional ' + str(delta_rate) + ' gold per hour.'
        reply.append(line)
    if len(unlocked) > 0:
        line = 'During this time, you randomly stumbled upon '
        line += ' and '.join([location_names[new] for new in unlocked]) + '!'
        reply.append(line)
    if presence:
        line = 'On the way back, you sensed the presence of an'
        line += ('other' if unlocked else '') + ' undiscovered location nearby.'
        reply.append(line)
    reply = ' '.join(reply)
    if len(item_drops) > 0:
        singular = len(item_drops) == 1 and list(item_drops.values())[0] == 1
        reply += '\n\nYou found the following item' + ('' if singular else 's') + ':'
        for item, amount in item_drops.items():
            reply += '\n-> ' + item + ' x ' + str(amount)

    message = Message(reply)
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)