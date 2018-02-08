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
                'Brutal Essence': 40,
                'Breathing Wood': 20,
                'Drop of Earth': 4,
                'Iron Shard': 20
            }
        },
        {
            'Name': 'Cloak of Thorns',
            'Type': 'Armor',
            'ATK': 4,
            'DEF': 2,
            'SPD': 4,
            'Materials': {
                'Wild Essence': 40,
                'Shifting Vines': 20,
                'Crystal Shard': 2
            }
        }
    ],
    'Sleepywood': [
        {
            'Name': 'Demon Soul',
            'Type': 'Item',
            'Description': 'Summons Crimson Balrog in Cursed Sanctuary.',
            'Materials': {
                'Brutal Essence': 50,
                'Wild Essence': 50,
                'Arcane Essence': 50,
                'Void Essence': 50,
                'Bottled Light': 5,
                'Bottled Darkness': 5
            }
        },
        {
            'Name': 'Decaying Shroud',
            'Type': 'Armor',
            'ATK': 0,
            'DEF': 6,
            'SPD': 6,
            'Materials': {
                'Void Essence': 40,
                'Touch of Death': 2,
                'Time Shard': 2,
            }
        }
    ]
}

def generate_craft_info(client, user, thread_id):
    reply = 'Crafting information been sent to you in private chat.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<The Workbench>>\n'
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
    client.send(Message(reply), thread_id=user['_id'], thread_type=ThreadType.USER)

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