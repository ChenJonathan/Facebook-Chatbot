from fbchat.models import *

from items import item_data
from mongo import *
from util import location_names


def generate_craft_info(client, user, thread_id):
    reply = 'Crafting information has been sent to you in private chat.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<' + user['Location'] + ' Workshop>>\n'
    reply += 'Craft things with "!craft <item>" in a group chat. '
    reply += 'Crafted equipment is automatically equipped.'
    for i, item_datum in enumerate(item_data[user['Location']]):
        reply += '\n\n' + str(i + 1) + '. ' + item_datum['Name']
        reply += '\n-> Type: ' + item_datum['Type']
        if item_datum['Type'] == 'Item':
            reply += '\n-> Description: ' + item_datum['Description']
        else:
            reply += '\n-> ATK: ' + str(item_datum['ATK'])
            reply += '\n-> DEF: ' + str(item_datum['DEF'])
            reply += '\n-> SPD: ' + str(item_datum['SPD'])
        reply += '\n-> Materials:'
        for material, amount in item_datum['Materials'].items():
            reply += '\n---> ' + material + ' x ' + str(amount)
    client.send(Message(reply), thread_id=user['_id'])


def craft_item(client, user, slot, thread_id):
    try:
        slot = int(slot) - 1
        item_list = item_data[user['Location']]
        assert 0 >= slot < len(item_list)
    except:
        reply = 'Invalid slot number.'
    else:
        item_datum = item_list[slot]

        # Check and deduct required materials
        materials_owned = True
        for material, amount in item_datum['Materials'].items():
            if material not in user['Inventory'] or user['Inventory'][material] < amount:
                materials_owned = False
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
                del item_datum['Materials']
                equip_item(user['_id'], item_type, item_datum)
                reply = user['Name'] + ' has crafted and equipped the ' + item_datum['Name'] + '!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)