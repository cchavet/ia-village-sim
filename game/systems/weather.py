import random
from core.bus import bus

WEATHER_STATES = [
    "Ensoleillé ☀️",
    "Pluvieux 🌧️",
    "Orageux ⛈️",
    "Nuageux ☁️",
    "Venteux 💨",
    "Brumeux 🌫️"
]


def update_weather(current_weather=None):
    if random.random() < 0.2: # 20% de chance de changer
        new_weather = random.choice(WEATHER_STATES)
        if new_weather != current_weather:
             bus.publish("WEATHER_CHANGE", {"type": new_weather})
        return new_weather
    return current_weather if current_weather else "Ensoleillé ☀️"
