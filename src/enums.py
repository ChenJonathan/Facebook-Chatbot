from enum import Enum


class UserState(Enum):
    IDLE = 0
    TRAVEL = 1
    BATTLE = 2
    DUEL = 3


class ChatState(Enum):
    REQUEST = 0
    PREPARING = 1
    READY = 2
    DELAY = 3
    QUEST = 4


class Region(Enum):
    MAPLE_ISLAND = 'maple_island'
    VICTORIA_ISLAND = 'victoria_island'
    SLEEPYWOOD = 'sleepywood'
    MASTERIA = 'masteria'
    EL_NATH_MOUNTAINS = 'el_nath_mountains'
    DEAD_MINE = 'dead_mine'
    AQUA_ROAD = 'aqua_road'
    LUDUS_LAKE = 'ludus_lake'
    CLOCK_TOWER = 'clock_tower'
    KOREAN_FOLK_TOWN = 'korean_folk_town'
    OMEGA_SECTOR = 'omega_sector'
    MINAR_FOREST = 'minar_forest'
    NIHAL_DESERT = 'nihal_desert'
    TEMPLE_OF_TIME = 'temple_of_time'


class Talent(Enum):
    UNSPENT = 'Unspent'
    TITAN = 'Titan'
    BERSERKER = 'Berserker'
    VANGUARD = 'Vanguard'
    SURVIVOR = 'Survivor'
    MISTWEAVER = 'Mistweaver'
    MERCHANT = 'Merchant'
    EXPLORER = 'Explorer'
    WANDERER = 'Wanderer'


_location_names = ['Maple Island']
_location_names += ['Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
_location_names += ['Sleepywood', 'Silent Swamp', 'Drake Cave', 'Temple Entrance', 'Cursed Sanctuary']
_location_names += ['New Leaf City', 'Meso Gears Tower', 'Krakian Jungle', 'Alien Base']
_location_names += ['Orbis', 'Cloud Park', 'Garden of Colors', 'Orbis Tower', 'El Nath', 'Ice Valley']
_location_names += ['Sharp Cliffs', 'Dead Mine', 'Caves of Trial', 'Altar of Flame']
_location_names += ['Aquarium', 'Coral Forest', 'Seaweed Road', 'Wrecked Ship Grave', 'Deepest Cave']
_location_names += ['Ludibrium', 'Toy Factory', 'Helios Tower', 'Eos Tower']
_location_names += ['Path of Time', 'Warped Passage', 'Forgotten Passage', 'Clock Tower Origin']
_location_names += ['Korean Folk Town', 'Black Mountain', 'Goblin Ridge']
_location_names += ['Omega Sector', 'Boswell Field', 'Mothership Interior']
_location_names += ['Leafre', 'Forest Valley', 'Dragon Forest', 'Dragon Canyon', 'Cave of Life']
_location_names += ['Ariant', 'Burning Sands', 'Sunset Road', 'Magatia', 'Zenumist Laboratory', 'Alcadno Laboratory']
_location_names += ['Temple of Time']

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
