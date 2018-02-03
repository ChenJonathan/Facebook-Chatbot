import os
import pymongo

db = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
db = db.get_default_database()

db_groups = db['Groups']
db_users = db['Users']

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