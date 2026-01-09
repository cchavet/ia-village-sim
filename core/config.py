# --- CONSTANTES GLOBALES ---
GRID_SIZE = 32

# Dictionnaire Nom -> Coordonnées [x, y]
# Doit correspondre à la map dans world_seed.json
LOCATIONS = {
    "Auberge du Chaudron": [4, 4],
    "Baguettes d'Olliv": [0, 4],
    "Apothicaire": [0, 8],
    "Bibliothèque": [20, 5],
    "Salle de Duel": [25, 25],
    "Grande Place": [15, 15],
    "Forêt Interdite": [30, 0]
}

# Inverse pour retrouver le nom depuis les coordonnées (si besoin)
MAP_LOCATIONS = {tuple(v): k for k, v in LOCATIONS.items()}

# --- ECONOMIE ---
STARTING_GOLD = 100
ITEMS_PRICES = {
    "Baguette Magique": 50,
    "Potion de Soin": 15,
    "Parchemin": 2,
    "Plume": 1,
    "Bierraubeurre": 5,
    "Grimoire": 100,
    "Ingrédients": 10
}
