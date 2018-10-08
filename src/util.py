import math

from enums import Talent

priority_names = ["Peasant", "User", "Mod", "Admin", "Master"]

master_priority = len(priority_names) - 1
master_id = "1564703352"

default_health = 100
default_health_regen = 10

talent_constants = {
    Talent.TITAN: 2,
    Talent.BERSERKER: 2,
    Talent.VANGUARD: 2,
    Talent.SURVIVOR: 10,
    Talent.MISTWEAVER: 10,
    Talent.MERCHANT: 10,
    Talent.EXPLORER: 20,
    Talent.WANDERER: 20
}


def talent_bonus(user, talent):
    return user["Talents"][talent.value] * talent_constants[talent]


def base_stat_float(level):
    return (math.sqrt(level + 64) - 7) * 10


def base_stat(level):
    return int(base_stat_float(level))


def base_atk(user):
    return base_stat(user["Stats"]["Level"]) + \
           talent_bonus(user, Talent.TITAN) + \
           talent_bonus(user, Talent.BERSERKER)


def base_def(user):
    return base_stat(user["Stats"]["Level"]) + \
           talent_bonus(user, Talent.TITAN) + \
           talent_bonus(user, Talent.VANGUARD)


def base_spd(user):
    return base_stat(user["Stats"]["Level"]) + \
           talent_bonus(user, Talent.BERSERKER) + \
           talent_bonus(user, Talent.VANGUARD)


def base_health(user):
    return default_health + talent_bonus(user, Talent.SURVIVOR)


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


def calculate_score(user):
    score = math.pow(max(user["Gold"] + user["GoldFlow"] * 50, 0), 0.25) * 50
    score += (total_atk(user) + total_def(user) + total_spd(user) - 45) * 25
    for location, progress in user["LocationProgress"].items():
        if progress == 1:
            score += 50
    score -= 11 * 50
    return int(score)


def split(text):
    a, b, *_ = text.split(None, 1) + ["", ""]
    return a, b
