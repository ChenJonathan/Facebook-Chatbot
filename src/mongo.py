import os
import pymongo

from enums import Location, Talent

_chatbot = None


def init_mongo(client):
    _chatbot = client


_db = pymongo.MongoClient(os.environ.get("MONGODB_URI")).get_database()
_db_self = _db["Self"]
_db_users = _db["Users"]
_db_groups = _db["Groups"]


def load_state(command):
    document = _db_self.find_one({"_id": command})
    if not document:
        _db_self.insert_one({"_id": command, command: {}})
        document = _db_self.find_one({"_id": command})
    return document[command]


def save_state(command, state):
    _db_self.update_one({"_id": command}, {"$set": {command: state}}, upsert=True)


def user_get(user_id):
    return _user_try_get(user_id)


def user_update(user_id, update):
    _user_try_get(user_id)
    _db_users.update_one({"_id": user_id}, update)


def user_query_one(query):
    return _db_users.find_one(query)


def user_query_all(query):
    return _db_users.find(query)


def group_get(group_id):
    return _group_try_get(group_id)


def group_update(group_id, update):
    _group_try_get(group_id)
    _db_groups.update_one({"_id": group_id}, update)


def group_query_one(query):
    return _db_groups.find_one(query)


def group_query_all(query):
    return _db_groups.find(query)


# - Must be used to add users so that document constraints are enforced
def _user_try_get(user_id):
    user = _db_users.find_one({"_id": user_id})
    if user:
        return user
    name = _chatbot.fetchThreadInfo(user_id)[user_id].name
    _db_users.insert_one({
        "_id": user_id,
        "Name": name,
        "Priority": 1,
        "Gold": 0,
        "GoldFlow": 0,
        "Location": Location["Lith Harbor"].name,
        "LocationProgress": {
            Location["Maple Island"].name: 1,
            Location["Lith Harbor"].name: 1,
            Location["Henesys"].name: 1,
            Location["Ellinia"].name: 1,
            Location["Perion"].name: 1,
            Location["Kerning City"].name: 1,
            Location["New Leaf City"].name: 1,
            Location["Orbis"].name: 1,
            Location["Ludibrium"].name: 1,
            Location["Leafre"].name: 1,
            Location["Ariant"].name: 1
        },
        "Stats": {
            "Level": 1,
            "Experience": 0
        },
        "Equipment": {
            "Weapon": {
                "Name": "Iron Longsword",
                "ATK": 5,
                "DEF": 0,
                "SPD": 0
            },
            "Armor": {
                "Name": "Leather Armor",
                "ATK": 0,
                "DEF": 5,
                "SPD": 0
            },
            "Accessory": {
                "Name": "Sapphire Amulet",
                "ATK": 0,
                "DEF": 0,
                "SPD": 5
            }
        },
        "Talents": {talent.value: 0 for talent in list(Talent)},
        "Inventory": {},
        "Quest": {"Type": "Vocab"},
        "Flags": {}
    })
    return _db_users.find_one({"_id": user_id})


# - Must be used to add groups so that document constraints are enforced
def _group_try_get(group_id):
    group = _db_groups.find_one({"_id": group_id})
    if group:
        return group
    _db_groups.insert_one({
        "_id": group_id
    })
    return _db_groups.find_one({"_id": group_id})
