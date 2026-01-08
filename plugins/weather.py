import random
import streamlit as st

WEATHER_STATES = ["Ensoleillé ☀️", "Pluvieux 🌧️", "Orageux ⛈️", "Brumeux 🌫️"]

def get_current_weather():
    if 'weather' not in st.session_state:
        st.session_state.weather = "Ensoleillé ☀️"
    return st.session_state.weather

def update_weather(current_weather=None):
    if random.random() < 0.2: # 20% de chance de changer
        return random.choice(WEATHER_STATES)
    return current_weather if current_weather else "Ensoleillé ☀️"
