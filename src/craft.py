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
            'ATK': 5,
            'DEF': 1,
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
            'Type': 'Armor'
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
    reply += '(Craft things with "!craft <item>" in a group chat)\n'
    reply += '(Crafted equipment is automatically equipped)'
    for item_data in craft_data[location_names[user['_id']]]:
        reply += '\n\n' + item_data['Name']
        reply += '\nType: ' + item_data['Type']
        if item_data['Type'] == 'Item':
            reply += '\nDescription: ' + item_data['Description']
        else:
            reply += '\nATK: ' + item_data['ATK']
            reply += '\nDEF: ' + item_data['DEF']
            reply += '\nSPD: ' + item_data['SPD']
        reply += '\nMaterials:'
        for material, amount in item_data['Materials'].items():
            reply += '\n-> ' + material + ' x ' + str(amount)
    client.send(Message(reply), thread_id=user['_id'], thread_type=ThreadType.USER)

def craft_item(client, user, slot, thread_id):
    pass