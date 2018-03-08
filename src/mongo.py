import os
import pymongo

from enums import Location

db_groups = None
db_users = None

chatbot = None


def init_db(client):
    db = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
    db = db.get_database()

    global db_groups
    global db_users
    db_groups = db['Groups']
    db_users = db['Users']

    global chatbot
    chatbot = client


# Subscription methods

def subscription_get(group_id):
    group = db_groups.find_one(group_id)
    return group.get('Subscriptions', []) if group else []


def subscription_get_all():
    groups = db_groups.find({'Subscriptions': {'$exists': True}})
    return {group['_id']: group['Subscriptions'] for group in groups}


def subscription_add(group_id, subscription):
    subscription = subscription.lower()
    update = {'$addToSet': {'Subscriptions': subscription}}
    db_groups.update_one({'_id': group_id}, update, upsert=True)


def subscription_remove(group_id, subscription):
    subscription = subscription.lower()
    update = {'$pull': {'Subscriptions': subscription}}
    db_groups.update_one({'_id': group_id}, update)
    update = {'$unset': {'Subscriptions': None}}
    db_groups.update_one({'_id': group_id, 'Subscriptions': []}, update)


# User methods

def user_from_alias(alias):
    return db_users.find_one({'Alias': alias})


def user_from_id(user_id):
    user_try_add(user_id)
    return db_users.find_one(user_id)


def user_get_all_in(user_ids):
    return db_users.find({'_id': {'$in': user_ids}})


def user_get_all():
    return db_users.find()


# - Must be used to add users so that attribute constraints are enforced
def user_try_add(user_id):
    if not db_users.find_one({'_id': user_id}):
        name = chatbot.fetchThreadInfo(user_id)[user_id].name
        db_users.insert_one({
            '_id': user_id, 
            'Name': name,
            'Priority': 1,
            'Gold': 0,
            'GoldFlow': 0,
            'Location': Location['Lith Harbor'].name,
            'LocationProgress': {
                Location['Maple Island'].name: 1,
                Location['Lith Harbor'].name: 1,
                Location['Henesys'].name: 1,
                Location['Ellinia'].name: 1,
                Location['Perion'].name: 1,
                Location['Kerning City'].name: 1,
                Location['New Leaf City'].name: 1,
                Location['Orbis'].name: 1,
                Location['Ariant'].name: 1,
                Location['Ludibrium'].name: 1,
                Location['Leafre'].name: 1,
            },
            'Stats': {
                'Level': 1,
                'Experience': 0,
                'Health': 100
            },
            'Equipment': {
                'Weapon': {
                    'Name': 'Iron Longsword',
                    'ATK': 5,
                    'DEF': 0,
                    'SPD': 0
                },
                'Armor': {
                    'Name': 'Leather Armor',
                    'ATK': 0,
                    'DEF': 5,
                    'SPD': 0
                },
                'Accessory': {
                    'Name': 'Sapphire Amulet',
                    'ATK': 0,
                    'DEF': 0,
                    'SPD': 5
                }
            },
            'Inventory': {},
            'Quest': {'Type': 'Vocab'}
        })


# Alias methods

def alias_get_all():
    return db_users.find({'Alias': {'$exists': True}})


def alias_add(user_id, alias):
    user_try_add(user_id)
    alias_remove(alias)
    update = {'$set': {'Alias': alias}}
    db_users.update_one({'_id': user_id}, update)


def alias_remove(alias):
    update = {'$unset': {'Alias': None}}
    db_users.update_one({'Alias': alias}, update)


# Priority methods

def priority_get(user_id):
    user_try_add(user_id)
    return db_users.find_one(user_id)['Priority']


def exceeds_priority(user_id_1, user_id_2):
    return priority_get(user_id_1) > priority_get(user_id_2)


def priority_set(user_id, priority):
    user_try_add(user_id)
    update = {'$set': {'Priority': priority}}
    db_users.update_one({'_id': user_id}, update)


# Gold methods

def gold_add(user_id, gold):
    user_try_add(user_id)
    update = {'$inc': {'Gold': gold}}
    db_users.update_one({'_id': user_id}, update)


def gold_flow_add(user_id, rate):
    user_try_add(user_id)
    update = {'$inc': {'GoldFlow': rate}}
    db_users.update_one({'_id': user_id}, update)


# Location methods

def location_set(user_id, location):
    user_try_add(user_id)
    update = {'$set': {'Location': location}}
    db_users.update_one({'_id': user_id}, update)


def location_progress_set(user_id, location, progress):
    user_try_add(user_id)
    update = {'$set': {('LocationProgress.' + str(location)): progress}}
    db_users.update_one({'_id': user_id}, update)


# Level methods

def level_set(user_id, level):
    user_try_add(user_id)
    update = {'$set': {
        'Stats.Level': level
    }}
    db_users.update_one({'_id': user_id}, update)


def experience_set(user_id, experience):
    user_try_add(user_id)
    update = {'$set': {'Stats.Experience': experience}}
    db_users.update_one({'_id': user_id}, update)


# Equipment methods

def equip_item(user_id, slot, item):
    user_try_add(user_id)
    update = {'$set': {('Equipment.' + slot): item}}
    db_users.update_one({'_id': user_id}, update)


# Inventory methods

def inventory_add(user_id, item, amount):
    user_try_add(user_id)
    update = {'$inc': {('Inventory.' + item): amount}}
    db_users.update_one({'_id': user_id}, update)


def inventory_remove_all(user_id, item):
    user_try_add(user_id)
    update = {'$unset': {('Inventory.' + item): None}}
    db_users.update_one({'_id': user_id}, update)


# Quest methods

def quest_type_set(user_id, quest_type):
    user_try_add(user_id)
    update = {'$set': {'Quest.Type': quest_type}}
    db_users.update_one({'_id': user_id}, update)


def quest_stat_track(user_id, quest_type, correct):
    user_try_add(user_id)
    update = {'$inc': {
        ('Quest.' + quest_type + '.Correct'): 1 if correct else 0,
        ('Quest.' + quest_type + '.Total'): 1
    }}
    db_users.update_one({'_id': user_id}, update)