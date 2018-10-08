import math

from enums import *
from mongo import *

priority_names = ["Peasant", "User", "Mod", "Admin", "Master"]

master_priority = len(priority_names) - 1
master_id = "1564703352"


def match_user_by_alias(query):
    query = query.strip().lower()
    return user_query_one({"Alias": query})


def match_user_by_search(client, query):
    user = client.searchForUsers(query)[0]
    return user_get(user.uid)


def match_user_in_group(client, group_id, query):
    group = client.fetchGroupInfo(group_id)[group_id]
    query = query.strip().lower()
    # - Alias match
    user = match_user_by_alias(query)
    if user and user["_id"] in group.participants:
        return user
    # - Full name match
    users = client.fetchUserInfo(*group.participants)
    for user_id, user in users.items():
        if query == user.name.lower():
            return user_get(user_id)
    # - Full word match
    query = query.split(None, 1)[0]
    for user_id, user in users.items():
        if query in user.name.lower().split():
            return user_get(user_id)
    # - String search
    for user_id, user in users.items():
        if user.name.lower().startswith(query):
            return user_get(user_id)
    return None


def user_state(client, user_id):
    state, details, handler = client.user_states.get(user_id, (UserState.IDLE, {}, None))
    return state, details


def format_num(num, sign=False, truncate=False):
    suffixes = ["", "k", "m", "b", "t", "q"]
    scale = 0
    if truncate:
        while abs(num) >= 100000 and scale < len(suffixes) - 1:
            num = num // 1000
            scale += 1
    num = ("+" + str(num)) if sign and num >= 0 else str(num)
    return num + suffixes[scale]


def format_time(seconds, minimal=False):
    minutes, seconds = seconds // 60, seconds % 60
    time = (str(minutes) + " min") if minutes > 0 else ""
    if not minimal or seconds > 0 or minutes == 0:
        time += " " if len(time) > 0 else ""
        time += str(seconds) + " sec" + ("" if seconds == 1 else "s")
    return time


def split(text):
    a, b, *_ = text.split(None, 1) + ["", ""]
    return a, b


def partition(text, args):
    arg, remaining = split(text)
    arg = arg.lower()
    return (arg, remaining.strip()) if arg in args else (None, text)


def base_stat_float(level):
    return (math.sqrt(level + 64) - 7) * 10


def base_stat(level):
    return int(base_stat_float(level))


def base_atk(user):
    return base_stat(user["Stats"]["Level"])


def base_def(user):
    return base_stat(user["Stats"]["Level"])


def base_spd(user):
    return base_stat(user["Stats"]["Level"])


def equip_atk(user):
    return user["Equipment"]["Weapon"]["ATK"] + \
           user["Equipment"]["Armor"]["ATK"] + \
           user["Equipment"]["Accessory"]["ATK"]


def equip_def(user):
    return user["Equipment"]["Weapon"]["DEF"] + \
           user["Equipment"]["Armor"]["DEF"] + \
           user["Equipment"]["Accessory"]["DEF"]


def equip_spd(user):
    return user["Equipment"]["Weapon"]["SPD"] + \
           user["Equipment"]["Armor"]["SPD"] + \
           user["Equipment"]["Accessory"]["SPD"]


def total_atk(user):
    return base_atk(user) + equip_atk(user)


def total_def(user):
    return base_def(user) + equip_def(user)


def total_spd(user):
    return base_spd(user) + equip_spd(user)


def calculate_score(user):
    score = math.pow(max(user["Gold"] + user["GoldFlow"] * 50, 0), 0.25) * 50
    score += (total_atk(user) + total_def(user) + total_spd(user) - 45) * 25
    for location, progress in user["LocationProgress"].items():
        if progress == 1:
            score += 50
    score -= 11 * 50
    return int(score)
