priority_names = ['Peasant', 'User', 'Mod', 'Admin', 'Master']

master_priority = len(priority_names) - 1
master_id = '1564703352'

location_names = ['Maple Island', 'Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
location_names += ['Sleepywood', 'Cursed Sanctuary', 'New Leaf City', 'Krakian Jungle', 'Bigger Ben']
location_names += ['Orbis', 'El Nath', 'Dead Mine', 'Zakum\'s Altar', 'Aqua Road', 'Cave of Pianus']
location_names += ['Ludibrium', 'Path of Time', 'Papulatus Tower', 'Korean Folk Town', 'Omega Sector']
location_names += ['Nihal Desert', 'Magatia', 'Leafre', 'Minar Forest', 'Cave of Life', 'Temple of Time']

def name_to_location(text):
    text = text.lower()
    for i, name in enumerate(location_names):
        name = name.strip().lower()
        if text == name or text in name.split():
            return i
    return None

def calculate_score(user):
    score = user['gold'] + user['gold_rate'] * 50
    score += (len(location_names) - len(user['location_progress'])) * 2500
    return score - 15000