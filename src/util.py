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
location_names += ['Korean Folk Town', 'Omega Sector', 'Ludibrium', 'Path of Time', 'Papulatus Clock Tower']
location_names += ['Nihal Desert', 'Magatia', 'Leafre', 'Minar Forest', 'Cave of Life', 'Temple of Time']

location_names_reverse = {location_names[i]: i for i in range(len(location_names))}

item_names = ['Demon Soul', 'Truffle Worm', 'Eye of Fire', 'Cracked Dimension Piece', 'Dragon Soul']
item_names += ['Brutal Essence', 'Wild Essence', 'Arcane Essence', 'Void Essence']
item_names += ['Bottled Light', 'Bottled Darkness', 'Touch of Life', 'Touch of Death']
item_names += ['Howling Wind', 'Formless Ice', 'Drop of Earth', 'Living Flame']
item_names += ['Clockwork Shard', 'Crystal Shard', 'Iron Shard', 'Time Shard']
item_names += ['Breathing Wood', 'Shifting Vines', 'Astral Coral', 'Warped Bones']


def level_to_stat_scale(level):
    return (math.sqrt(level + 64) - 7) * 10


def total_atk(user):
    return user['Stats']['ATK'] + user['Equipment']['Weapon']['ATK'] + \
           user['Equipment']['Armor']['ATK'] + user['Equipment']['Accessory']['ATK']


def total_def(user):
    return user['Stats']['DEF'] + user['Equipment']['Weapon']['DEF'] + \
           user['Equipment']['Armor']['DEF'] + user['Equipment']['Accessory']['DEF']


def total_spd(user):
    return user['Stats']['SPD'] + user['Equipment']['Weapon']['SPD'] + \
           user['Equipment']['Armor']['SPD'] + user['Equipment']['Accessory']['SPD']


def calculate_score(user):
    score = math.sqrt(max(user['Gold'] + user['GoldFlow'] * 125, 0))
    score += (total_atk(user) + total_def(user) + total_spd(user) - 36) * 25
    for location, progress in user['LocationProgress'].items():
        if progress == 1:
            score += 50
    score -= 6 * 50
    return int(score)