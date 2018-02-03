import os
import pymongo

db_groups = None
db_users = None

chatbot = None

def init_db(client):
    db = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
    db = db.get_default_database()

    global db_groups
    global db_users
    db_groups = db['Groups']
    db_users = db['Users']

    global chatbot
    chatbot = client

# Subscription methods

def subscription_get(group_id):
    group = db_groups.find_one(group_id)
    return group.get('subscriptions', []) if group else []

def subscription_get_all():
    groups = db_groups.find({'subscriptions': {'$exists': True}})
    return {group['_id']: group['subscriptions'] for group in groups}

def subscription_add(group_id, subscription):
    subscription = subscription.lower()
    update = {'$addToSet': {'subscriptions': subscription}}
    db_groups.update_one({'_id': group_id}, update, upsert=True)

def subscription_remove(group_id, subscription):
    subscription = subscription.lower()
    update = {'$pull': {'subscriptions': subscription}}
    db_groups.update_one({'_id': group_id}, update)
    update = {'$unset': {'subscriptions': None}}
    db_groups.update_one({'_id': group_id, 'subscriptions': []}, update)

# User methods

def user_from_alias(alias):
    return db_users.find_one({'alias': alias})

def user_from_id(user_id):
    user_try_add(user_id)
    return db_users.find_one(user_id)

# - Must be used to add users so that attribute constraints are enforced
def user_try_add(user_id):
    if not db_users.find_one({'_id': user_id}):
        name = chatbot.fetchThreadInfo(user_id)[user_id].name
        db_users.insert_one({
            '_id': user_id, 
            'name': name, 
            'priority': 1, 
            'experience': 0
        })

# Alias methods

def alias_get_all():
    return db_users.find({'alias': {'$exists': True}})

def alias_add(user_id, alias):
    user_try_add(user_id)
    alias_remove(alias)
    update = {'$set': {'alias': alias}}
    db_users.update_one({'_id': user_id}, update)

def alias_remove(alias):
    update = {'$unset': {'alias': None}}
    db_users.update_one({'alias': alias}, update)

# Priority methods

def priority_get(user_id):
    user_try_add(user_id)
    return db_users.find_one(user_id)['priority']

def priority_set(user_id, priority):
    user_try_add(user_id)
    update = {'$set': {'priority': priority}}
    db_users.update_one({'_id': user_id}, update)

# Experience methods