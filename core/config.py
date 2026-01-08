# --- CONSTANTES GLOBALES ---
GRID_SIZE = 5

# Dictionnaire Nom -> Coordonnées [x, y]
LOCATIONS = {
    "La Forge": [0, 0],
    "L'Auberge": [4, 4],
    "La Place": [2, 2],
    "L'Apothicaire": [0, 4],
    "La Forêt": [4, 0]
}

# Inverse pour retrouver le nom depuis les coordonnées (si besoin)
MAP_LOCATIONS = {tuple(v): k for k, v in LOCATIONS.items()}

# --- ECONOMIE ---
STARTING_GOLD = 50
ITEMS_PRICES = {
    "Épée": 30,
    "Potion": 20,
    "Repas": 15,
    "Bois": 5,
    "Fleurs": 5
}
