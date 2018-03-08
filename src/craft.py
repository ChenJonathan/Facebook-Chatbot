from fbchat.models import *

from data import craft_data
from enums import Item
from mongo import *
from util import *


def generate_craft_info(client, user, thread_id):
    reply = user['Location'] + ' crafting information has been sent to you. '
    reply += 'Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<' + user['Location'] + ' Workshop>>\n'
    reply += 'Craft things with "!craft <slot>" in a group chat, where <slot> is the item slot number. '
    reply += 'Crafted equipment is automatically equipped and old equipment is discarded.'
    for i, item_datum in enumerate(craft_data[user['Location']]):
        reply += '\n\n' + str(i + 1) + '. ' + item_datum['Name']
        reply += '\n-> Type: ' + item_datum['Type']
        if item_datum['Type'] == 'Item':
            reply += '\n-> Description: ' + item_datum['Description']
        else:
            current = user['Equipment'][item_datum['Type']]
            reply += '\n-> ATK: ' + str(item_datum['ATK']) + ' ('
            reply += format_num(item_datum['ATK'] - current['ATK'], sign=True) + ' change)'
            reply += '\n-> DEF: ' + str(item_datum['DEF']) + ' ('
            reply += format_num(item_datum['DEF'] - current['DEF'], sign=True) + ' change)'
            reply += '\n-> SPD: ' + str(item_datum['SPD']) + ' ('
            reply += format_num(item_datum['SPD'] - current['SPD'], sign=True) + ' change)'
        reply += '\n-> Level Required: ' + str(item_datum['Level'])
        reply += '\n-> Materials Required:'
        for material_key in sorted(item_datum['Materials'].keys(), key=lambda x: Item[x].value):
            required = str(item_datum['Materials'][material_key])
            owned = str(user['Inventory'].get(material_key, 0))
            reply += '\n---> ' + material_key + ' x ' + required + ' (' + owned + '/' + required + ')'
    client.send(Message(reply), thread_id=user['_id'])


def craft_item(client, user, slot, thread_id):
    item_list = craft_data[user['Location']]
    slot -= 1
    if slot < 0 or slot >= len(item_list):
        reply = 'Invalid slot number.'
    else:
        item_datum = item_list[slot]

        # Check level
        if user['Stats']['Level'] < item_datum['Level']:
            reply = 'Your level is not high enough to craft this.'
        else:

            # Check and deduct required materials
            materials_owned = True
            for material, amount in item_datum['Materials'].items():
                if user['Inventory'].get(material, 0) < amount:
                    materials_owned = False
                    break
            if not materials_owned:
                reply = 'You don\'t have the materials necessary to craft this.'
            else:
                for material, amount in item_datum['Materials'].items():
                    if user['Inventory'][material] > amount:
                        inventory_add(user['_id'], material, -amount)
                    else:
                        inventory_remove_all(user['_id'], material)

                # Equip the item and send a message
                item_type = item_datum['Type']
                if item_type == 'Item':
                    inventory_add(user['_id'], item_datum['Name'], 1)
                    reply = user['Name'] + ' has crafted the ' + item_datum['Name'] + '!'
                else:
                    item_datum = item_datum.copy()
                    del item_datum['Type']
                    del item_datum['Level']
                    del item_datum['Materials']
                    equip_item(user['_id'], item_type, item_datum)
                    reply = user['Name'] + ' has crafted and equipped the ' + item_datum['Name'] + '!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)