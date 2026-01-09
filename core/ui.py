import streamlit as st

def inject_custom_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

    :root {
      --bg-color: #0e1117;
      --map-bg: #1a1c24;
      --text-main: #e6e6e6;
      --accent: #5c7cfa;
    }

    .stApp {
        background-color: var(--bg-color);
        font-family: 'Outfit', sans-serif;
        color: var(--text-main);
    }
    
    /* MAXIMIZE CONTAINER */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    header, footer {display: none !important;}
    
    /* IMMERSIVE MAP CONTAINER */
    .immersive-map-container {
        position: relative;
        width: 100vw;
        height: 90vh;
        background: var(--map-bg);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* GRID SYSTEM */
    .map-grid {
        display: grid;
        /* Grid Template set inline based on size */
        width: 90vh; /* Square based on height */
        height: 90vh;
        box-shadow: 0 0 50px rgba(0,0,0,0.5);
    }
    
    .map-cell {
        position: relative;
        border: 0.5px solid rgba(255,255,255,0.02);
    }
    
    /* ANIMATED MARKERS */
    .marker-container {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none; /* Let clicks pass to cell if needed */
        transition: all 0.8s cubic-bezier(0.25, 1, 0.5, 1); /* SMOOTH MOVEMENT */
    }
    
    .avatar {
        width: 70%;
        height: 70%;
        background: white;
        border-radius: 50%;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        z-index: 10;
        border: 2px solid rgba(255,255,255,0.8);
        transition: transform 0.2s;
    }
    
    /* HUD OVERLAY */
    .hud-overlay {
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(10px);
        padding: 15px 25px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        z-index: 100;
        text-align: right;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .hud-time { font-size: 2.5rem; font-weight: 600; line-height: 1; }
    .hud-date { font-size: 0.9rem; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase; margin-top: 5px; }
    .hud-weather { font-size: 1.2rem; margin-top: 5px; color: #CBD5E1; }

    /* TOOLTIP */
    .avatar:hover::after {
        content: attr(data-name);
        position: absolute;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.9);
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        white-space: nowrap;
        pointer-events: none;
    }

</style>
    """, unsafe_allow_html=True)

def render_dashboard(characters, world_time, map_layout, map_colors, story_text, logs, map_objects=None):
    """
    Renders the Immersive UI.
    """
    inject_custom_css()
    
    grid_size = len(map_layout)
    
    # --- TIME CALC ---
    h = world_time // 60
    m = world_time % 60
    day = (world_time // 1440) + 1
    time_str = f"{h:02d}:{m:02d}"
    
    # --- WEATHER ICON ---
    weather_state = st.session_state.get('weather', {'condition': 'Clair', 'temp': 20})
    
    # Safety Check: Handle String Legacy State
    if isinstance(weather_state, str):
        weather_state = {'condition': weather_state, 'temp': 20}
        
    w_cond = weather_state.get('condition', 'Clair')
    w_icon = "☀️"
    if "Pluie" in w_cond: w_icon = "🌧️"
    if "Nuage" in w_cond: w_icon = "☁️"
    if "Orage" in w_cond: w_icon = "⛈️"
    if "Nuit" in w_cond: w_icon = "🌙" # Crude check, better logic needed based on time
    if h >= 22 or h < 6: w_icon = "🌙"
    
    # --- HUD OVERLAY ---
    # We use st.markdown with absolute positioning inside the main container, 
    # but since Streamlit structure is rigid, we put it first.
    st.markdown(f"""
    <div class="hud-overlay">
        <div class="hud-time">{time_str}</div>
        <div class="hud-date">JOUR {day} • {w_icon} {weather_state['temp']}°C</div>
        <div class="hud-weather">{w_cond}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- SIDEBAR (LOGS & STATS) ---
    with st.sidebar:
        st.markdown("### 📜 Journal de Bord")
        # Reverse logs for newest first
        visible_logs = logs[-20:]
        visible_logs.reverse()
        log_html = "<div style='font-size:0.8rem; opacity:0.8; height: 300px; overflow-y:auto;'>" + "<br><br>".join(visible_logs) + "</div>"
        st.markdown(log_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 👥 Agents")
        for name, v in characters.items():
             busy_icon = "⏳" if v.get('busy_until', 0) > world_time else "🟢"
             st.markdown(f"**{name}** {busy_icon} <br><span style='font-size:0.8rem; color:#aaa'>{v['pos']} | {v.get('action_desc', '')}</span>", unsafe_allow_html=True)

    # --- MAP RENDERING ---
    # To achieve "Animation", we need to ensure the grid is static and only markers move.
    # In Streamlit, everything rerenders. 
    # BUT, if we use CSS Grid and place markers based on (row, col), 
    # changing the style/class/grid-pos might trigger CSS transition?
    # Actually, standard Streamlit rerender replaces the DOM. 
    # CSS transitions ONLY work if the element IDENTITY is preserved or if we use specific tricks.
    # Trick: The Grid Cells are static. The Markers are children of the GRID (not the cell) ?
    # Let's try putting Markers inside the cells first.
    
    cells_html = ""
    
    # Pre-calculate Markers per cell to stack them?
    # Or just loop cells.
    
    for y in range(grid_size):
        for x in range(grid_size):
            char = map_layout[y][x]
            col = map_colors.get(char, "#111")
            
            # Find characters here
            markers = ""
            for name, v in characters.items():
                if v['pos'] == [x, y]:
                    # Determine Avatar
                    av = name[0]
                    role = v['role']
                    if "Chat" in role: av = "🐱"
                    elif "Proff" in role: av = "🧙‍♂️"
                    elif "Etudiant" in role: av = "🎓"
                    elif "Fantôme" in role: av = "👻"
                    
                    # Tooltip data
                    markers += f'<div class="marker-container"><div class="avatar" data-name="{name}">{av}</div></div>'
            
            cells_html += f'<div class="map-cell" style="background:{col};">{markers}</div>'

    map_html = f"""
    <div class="immersive-map-container">
        <div class="map-grid" style="grid-template-columns: repeat({grid_size}, 1fr); grid-template-rows: repeat({grid_size}, 1fr);">
            {cells_html}
        </div>
    </div>
    """
    
    st.markdown(map_html, unsafe_allow_html=True)
