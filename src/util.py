priority_names = ['Peasant', 'User', 'Mod', 'Admin', 'Master']

master_priority = len(priority_names) - 1
master_id = '1564703352'

location_names = ['Maple Island', 'Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
location_names += ['Sleepywood', 'Cursed Sanctuary', 'New Leaf City', 'Krakian Jungle', 'Bigger Ben']
location_names += ['Orbis', 'El Nath', 'Dead Mine', 'Zakum\'s Altar', 'Aqua Road', 'Cave of Pianus']
location_names += ['Ludibrium', 'Path of Time', 'Papulatus Tower', 'Korean Folk Town', 'Omega Sector']
location_names += ['Nihal Desert', 'Magatia', 'Leafre', 'Minar Forest', 'Cave of Life', 'Temple of Time']

item_names = ['Demon Soul', 'Truffle Worm', 'Eye of Fire', 'Cracked Dimension Piece', 'Dragon Soul']
item_names = ['Brutal Essence', 'Wild Essence', 'Arcane Essence', 'Void Essence']
item_names += ['Bottled Light', 'Bottled Darkness', 'Touch of Life', 'Touch of Death']
item_names += ['Howling Wind', 'Formless Ice', 'Drop of Earth', 'Living Flame']
item_names += ['Clockwork Shard', 'Crystal Shard', 'Iron Shard', 'Time Shard']
item_names += ['Breathing Wood', 'Shifting Vines', 'Astral Coral', 'Warped Bones']

def name_to_location(text):
    text = text.lower()
    for i, name in enumerate(location_names):
        name = name.strip().lower()
        if text == name or text in name.split():
            return i
    return None

def calculate_score(user):
    score = user['gold'] + user['gold_rate'] * 50
    score += (len(location_names) - len(user['location_progress'])) * 2000
    return score - 12000