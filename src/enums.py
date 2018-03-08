from enum import Enum


class UserState(Enum):
    IDLE = 0
    TRAVEL = 1
    BATTLE = 2
    DUEL = 3


class ChatState(Enum):
    PREPARING = 0
    READY = 1
    DELAY = 2
    QUEST = 3


class Region(Enum):
    MAPLE_ISLAND = 'maple_island'
    VICTORIA_ISLAND = 'victoria_island'
    SLEEPYWOOD = 'sleepywood'
    MASTERIA = 'masteria'
    EL_NATH_MOUNTAINS = 'el_nath_mountains'
    DEAD_MINE = 'dead_mine'
    AQUA_ROAD = 'aqua_road'
    NIHAL_DESERT = 'nihal_desert'
    LUDUS_LAKE = 'ludus_lake'
    CLOCK_TOWER = 'clock_tower'
    MINAR_FOREST = 'minar_forest'
    TEMPLE_OF_TIME = 'temple_of_time'


_location_names = ['Maple Island', 'Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
_location_names += ['Sleepywood', 'Cursed Sanctuary', 'New Leaf City', 'Krakian Jungle', 'Bigger Ben']
_location_names += ['Orbis', 'El Nath', 'Dead Mine', 'Zakum\'s Altar', 'Aqua Road', 'Cave of Pianus']
_location_names += ['Ariant', 'Magatia', 'Ludibrium', 'Path of Time', 'Papulatus Clock Tower']
_location_names += ['Korean Folk Town', 'Omega Sector', 'Leafre', 'Minar Forest', 'Horntail\'s Lair', 'Temple of Time']

Location = Enum('Location', _location_names)

_item_names = ['Demon Soul', 'Ancient Pearl', 'Eye of Fire', 'Cracked Dimension Piece', 'Dragon Soul']
_item_names += ['Brutal Essence', 'Wild Essence', 'Arcane Essence', 'Void Essence']
_item_names += ['Touch of Life', 'Touch of Death', 'Touch of Chaos', 'Touch of Magic']
_item_names += ['Bottled Light', 'Bottled Darkness', 'Lost Song', 'Lost Memory']
_item_names += ['Sunlight Fragment', 'Moonlight Fragment', 'Time Fragment', 'Space Fragment']
_item_names += ['Howling Wind', 'Soft Breeze', 'Deformed Water', 'Shapeless Ice']
_item_names += ['Drop of Earth', 'Drop of Sand', 'Living Flame', 'Dying Magma']
_item_names += ['Mythril Shard', 'Crystal Shard', 'Clockwork Shard', 'Plasma Shard']
_item_names += ['Breathing Wood', 'Shifting Vines', 'Weeping Herb', 'Astral Flower']
_item_names += ['Mutated Moss', 'Wistful Wool', 'Hallowed Feather', 'Primal Taint']
_item_names += ['Warped Bones', 'Warped Entrails', 'Warped Debris', 'Warped Spirit']

Item = Enum('Item', _item_names)