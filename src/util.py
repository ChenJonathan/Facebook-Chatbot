from enum import Enum
import math

priority_names = ['Peasant', 'User', 'Mod', 'Admin', 'Master']

master_priority = len(priority_names) - 1
master_id = '1564703352'


class UserState(Enum):
    Idle = 0
    Travel = 1
    Battle = 2
    Duel = 3


class ChatState(Enum):
    Preparing = 0
    Ready = 1
    Delay = 2
    Quest = 3


location_names = ['Maple Island', 'Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
location_names += ['Sleepywood', 'Cursed Sanctuary', 'New Leaf City', 'Krakian Jungle', 'Bigger Ben']
location_names += ['Orbis', 'El Nath', 'Dead Mine', 'Zakum\'s Altar', 'Aqua Road', 'Cave of Pianus']
location_names += ['Ariant', 'Magatia', 'Ludibrium', 'Path of Time', 'Papulatus Clock Tower']
location_names += ['Korean Folk Town', 'Omega Sector', 'Leafre', 'Minar Forest', 'Horntail\'s Lair', 'Temple of Time']

location_names_reverse = {location_names[i]: i for i in range(len(location_names))}

item_names = ['Demon Soul', 'Ancient Pearl', 'Eye of Fire', 'Cracked Dimension Piece', 'Dragon Soul']
item_names += ['Brutal Essence', 'Wild Essence', 'Arcane Essence', 'Void Essence']
item_names += ['Touch of Life', 'Touch of Death', 'Touch of Chaos', 'Touch of Magic']
item_names += ['Bottled Light', 'Bottled Darkness', 'Lost Song', 'Lost Memory']
item_names += ['Sunlight Fragment', 'Moonlight Fragment', 'Time Fragment', 'Space Fragment']
item_names += ['Howling Wind', 'Soft Breeze', 'Deformed Water', 'Shapeless Ice']
item_names += ['Drop of Earth', 'Drop of Sand', 'Living Flame', 'Dying Magma']
item_names += ['Mithril Shard', 'Crystal Shard', 'Clockwork Shard', 'Plasma Shard']
item_names += ['Breathing Wood', 'Shifting Vines', 'Weeping Herb', 'Astral Flower']
item_names += ['Mutated Moss', 'Wistful Wool', 'Hallowed Feather', 'Primal Taint']
item_names += ['Warped Bones', 'Warped Entrails', 'Warped Debris', 'Warped Spirit']

item_names_reverse = {item_names[i]: i for i in range(len(item_names))}


def base_stat_float(level):
    return (math.sqrt(level + 64) - 7) * 10


def base_stat(level):
    return int(base_stat_float(level))


def equip_atk(user):
    return user['Equipment']['Weapon']['ATK'] + \
           user['Equipment']['Armor']['ATK'] + \
           user['Equipment']['Accessory']['ATK']


def equip_def(user):
    return user['Equipment']['Weapon']['DEF'] + \
           user['Equipment']['Armor']['DEF'] + \
           user['Equipment']['Accessory']['DEF']


def equip_spd(user):
    return user['Equipment']['Weapon']['SPD'] + \
           user['Equipment']['Armor']['SPD'] + \
           user['Equipment']['Accessory']['SPD']


def total_atk(user):
    return base_stat(user['Stats']['Level']) + equip_atk(user)


def total_def(user):
    return base_stat(user['Stats']['Level']) + equip_def(user)


def total_spd(user):
    return base_stat(user['Stats']['Level']) + equip_spd(user)


def format_num(num, sign=False, truncate=False):
    suffixes = ['', 'k', 'm', 'b', 't']
    scale = 0
    if truncate:
        while abs(num) >= 100000 and scale < len(suffixes) - 1:
            num = num // 1000
            scale += 1
    num = ('+' + str(num)) if sign and num >= 0 else str(num)
    return num + suffixes[scale]


def calculate_score(user):
    score = math.sqrt(max(user['Gold'] + user['GoldFlow'] * 125, 0))
    score += (total_atk(user) + total_def(user) + total_spd(user) - 36) * 25
    for location, progress in user['LocationProgress'].items():
        if progress == 1:
            score += 50
    score -= 11 * 50
    return int(score)