import json
import math
import random

GRID_SIZE = 32
CENTER = GRID_SIZE / 2
ISLAND_RADIUS = 12

def get_terrain(x, y):
    # Distance du centre
    dist = math.sqrt((x - CENTER)**2 + (y - CENTER)**2)
    
    # Bruit aléatoire pour des côtes irrégulières
    noise = random.uniform(-1.5, 1.5)
    d = dist + noise
    
    if d > ISLAND_RADIUS:
        return "~" # Mer
    elif d > ISLAND_RADIUS - 2:
        return "." # Plage
    elif d > ISLAND_RADIUS - 6:
        return "#" # Jungle
    else:
        return "T" # Terre / Montagne

# Génération de la grille
layout = []
for y in range(GRID_SIZE):
    row = ""
    for x in range(GRID_SIZE):
        row += get_terrain(x, y)
    layout.append(list(row)) # Mutable list for items

# Placement du Crash (A)
crash_x, crash_y = int(CENTER), int(CENTER)
layout[crash_y][crash_x] = "A"
layout[crash_y+1][crash_x] = "?"
layout[crash_y][crash_x+1] = "?"

# Dispersion des débris (?)
for _ in range(15):
    rx = random.randint(0, GRID_SIZE-1)
    ry = random.randint(0, GRID_SIZE-1)
    if layout[ry][rx] not in ["~", "A"]:
        layout[ry][rx] = "?"

# Reconversion en strings
final_layout = ["".join(row) for row in layout]

# Données existantes (Personnages)
characters = {
    "John": {
      "role": "Pilote",
      "age": 30,
      "description": "Sérieux, respecte les procédures. Le leader naturel.",
      "pos": [crash_x, crash_y+2],
      "energy": 80,
      "inventory": ["Uniforme déchiré"],
      "gold": 0,
      "rel": {}
    },
    "Barbie": {
      "role": "Influenceuse",
      "age": 20,
      "description": "Obsédée par son téléphone (inutile ici). Superficielle mais peut surprendre.",
      "pos": [crash_x+1, crash_y+2],
      "energy": 90,
      "inventory": ["Smartphone (0% batterie)", "Maillot de bain"],
      "gold": 0,
      "rel": {}
    },
    "Ken": {
      "role": "Docteur en Électronique",
      "age": 45,
      "description": "Grand inventeur, voyageur expérimenté. Capable de réparer la radio.",
      "pos": [crash_x-1, crash_y+2],
      "energy": 70,
      "inventory": ["Lunettes cassées"],
      "gold": 0,
      "rel": {}
    }
}

seed_data = {
  "scenario_name": "Crash sur l'Île (32x32)",
  "description": "Un avion s'est écrasé sur une île thaïlandaise inhabitée.",
  "grid_size": GRID_SIZE,
  "map_legend": {
    "~": "Mer (Bleu)",
    ".": "Plage (Jaune)",
    "#": "Jungle (Vert)",
    "T": "Terre (Marron)",
    "A": "Site du Crash (Blanc)",
    "?": "Débris/Affaires (Rouge)"
  },
  "map_colors": {
    "~": "#1E90FF",
    ".": "#F0E68C",
    "#": "#228B22",
    "T": "#8B4513",
    "A": "#FFFFFF",
    "?": "#FF0000"
  },
  "map_layout": final_layout,
  "characters": characters,
  "loot_table": [
    "Mallette de premiers secours",
    "Bouteille d'eau",
    "Radio cassée",
    "Couteau suisse",
    "Conserve",
    "Batterie externe",
    "Vêtements",
    "Machette rouillée"
  ]
}

with open("world_seed.json", "w", encoding='utf-8') as f:
    json.dump(seed_data, f, indent=2, ensure_ascii=False)

print("Map 32x32 generated in world_seed.json")
