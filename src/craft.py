from fbchat.models import *

from mongo import *
from util import location_names

craft_data = {
    'Perion': [
        {
            'Name': 'Earthborn Warhammer',
            'Type': 'Weapon',
            'ATK': 12,
            'DEF': 0,
            'SPD': -2,
            'Materials': {
                'Brutal Essence': 20,
                'Breathing Wood': 10,
                'Drop of Earth': 2,
                'Iron Shard': 10
            }
        },
        {
            'Name': 'Cloak of Thorns',
            'Type': 'Armor',
            'ATK': 4,
            'DEF': 2,
            'SPD': 4,
            'Materials': {
                'Wild Essence': 20,
                'Shifting Vines': 10,
                'Crystal Shard': 1
            }
        }
    ],
    'Sleepywood': [
        {
            'Name': 'Demon Soul',
            'Type': 'Item',
            'Description': 'Summons Crimson Balrog in Cursed Sanctuary.',
            'Materials': {
                'Brutal Essence': 25,
                'Wild Essence': 25,
                'Arcane Essence': 25,
                'Void Essence': 25,
                'Bottled Light': 1,
                'Bottled Darkness': 1
            }
        },
        {
            'Name': 'Decaying Shroud',
            'Type': 'Armor',
            'ATK': 0,
            'DEF': 6,
            'SPD': 6,
            'Materials': {
                'Void Essence': 20,
                'Touch of Death': 1,
                'Time Shard': 1
            }
        }
    ]
}

def generate_craft_info(client, user, thread_id):
    reply = 'Crafting information has been sent to you in private chat.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<' + location_names[user['location']] + ' Workshop>>\n'
    reply += 'Craft things with "!craft <item>" in a group chat. '
    reply += 'Crafted equipment is automatically equipped.'
    for i, item_data in enumerate(craft_data[location_names[user['location']]]):
        reply += '\n\n' + str(i + 1) + '. ' + item_data['Name']
        reply += '\n-> Type: ' + item_data['Type']
        if item_data['Type'] == 'Item':
            reply += '\n-> Description: ' + item_data['Description']
        else:
            reply += '\n-> ATK: ' + str(item_data['ATK'])
            reply += '\n-> DEF: ' + str(item_data['DEF'])
            reply += '\n-> SPD: ' + str(item_data['SPD'])
        reply += '\n-> Materials:'
        for material, amount in item_data['Materials'].items():
            reply += '\n---> ' + material + ' x ' + str(amount)
    client.send(Message(reply), thread_id=user['_id'])

def craft_item(client, user, slot, thread_id):
    try:
        slot = int(slot) - 1
        item_data_all = craft_data[location_names[user['location']]]
        assert slot >= 0 and slot < len(item_data_all)
    except:
        reply = 'Invalid slot number.'
    else:
        item_data = item_data_all[slot]

        # Check and deduct required materials
        materials_owned = True
        for material, amount in item_data['Materials'].items():
            if material not in user['inventory'] or user['inventory'][material] < amount:
                materials_owned = False
        if not materials_owned:
            reply = 'You don\'t have the materials necessary to craft this.'
        else:
            for material, amount in item_data['Materials'].items():
                if user['inventory'][material] > amount:
                    inventory_add(user['_id'], material, -amount)
                else:
                    inventory_remove_all(user['_id'], material)

            # Equip the item and send a message
            item_type = item_data['Type']
            if item_type == 'Item':
                inventory_add(user['_id'], item_data['Name'], 1)
                reply = user['name'] + ' has crafted the ' + item_data['Name'] + '!'
            else:
                item_data = item_data.copy()
                del item_data['Type']
                del item_data['Materials']
                equip_item(user['_id'], item_type, item_data)
                reply = user['name'] + ' has crafted and equipped the ' + item_data['Name'] + '!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)