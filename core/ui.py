import streamlit as st
import json

def inject_custom_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    :root {
      --bg-color: #1a1c24; /* Dark Gunmetal */
      --panel-bg: #222530; /* Lighter Gunmetal */
      --border-color: #2f3445;
      --accent-primary: #5c7cfa; /* Professional Blue */
      --text-main: #e6e6e6;
      --text-dim: #8c90a0;
    }

    .stApp {
        background-color: var(--bg-color);
        background-image: none;
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }
    
    /* Remove Padding */
    .main .block-container {
        padding: 1rem 1rem !important;
        max-width: 100% !important;
    }
    header, footer {visibility: hidden;}
    
    /* PANELS (Professional Cards) */
    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        border-radius: 8px;
        padding: 15px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    
    .panel-header {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        color: var(--text-dim);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* LEFT: STAT CARDS (Clean List) */
    .stat-card {
        background: transparent;
        border-bottom: 1px solid var(--border-color);
        padding: 10px 5px;
        transition: background 0.2s;
        border-left: 2px solid transparent;
    }
    .stat-card:hover { background: rgba(255,255,255,0.03); }
    .stat-card.active { 
        border-left-color: var(--accent-primary);
        background: rgba(92, 124, 250, 0.05);
    }
    
    .stat-name { 
        font-weight: 600; 
        font-size: 0.95rem; 
        color: var(--text-main); 
    }
    
    /* CENTER: MAP (Technical Look) */
    .map-container {
        width: 100%;
        aspect-ratio: 1/1;
        background: #111;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        overflow: hidden;
    }
    
    .map-marker {
        position: absolute;
        width: 60%; height: 60%;
        top: 20%; left: 20%;
        border-radius: 50%;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.2);
        z-index: 10;
        transition: all 0.2s;
    }
    
    /* RIGHT: STORY FEED (Terminal/Log Style or Clean Doc) */
    .story-feed {
        overflow-y: auto;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #d1d5db;
        height: 100%;
        padding-right: 5px;
    }
    
    .story-feed::-webkit-scrollbar { width: 5px; }
    .story-feed::-webkit-scrollbar-thumb { background: #374151; border-radius: 2px; }
    
    /* BUTTONS (Standard UI) */
    .stButton button {
        background: #374151;
        color: #fff;
        border: 1px solid #4b5563;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        padding: 8px 16px;
        border-radius: 6px;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: var(--accent-primary);
        border-color: var(--accent-primary);
        color: #fff;
    }

</style>
    """, unsafe_allow_html=True)

def render_dashboard(characters, world_time, map_layout, map_colors, story_text, logs, map_objects=None):
    
    inject_custom_css()
    
    # Ensure Map Grid is strictly sized
    grid_size = len(map_layout)
    
    # Time Formatting (Minutes -> HH:MM)
    h = world_time // 60
    m = world_time % 60
    day = (world_time // 1440) + 1
    time_display = f"{h:02d}:{m:02d}"
    
    # Header Neutral
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #2f3445; padding-bottom:10px; margin-bottom:20px;">
        <div style="font-weight:600; font-size:1.2rem; color:#fff;">SIMULATION CONTROL</div>
        <div style="font-family:'Inter'; font-size:0.9rem; color:#8c90a0;">
            <span style="margin-right:15px;">⏱ {time_display}</span>
            <span>📅 JOUR {day}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1, 2, 1], gap="medium")
    
    # LEFT PANEL
    with col_left:
        left_html = f"""<div class="panel" style="height: 80vh; overflow-y: auto;">
            <div class="panel-header"><span>AGENTS ACTIFS</span> <span>{len(characters)}</span></div>"""
        
        for name, v in characters.items():
            active_class = "active" if v.get('pos') != v.get('dest', v['pos']) else "" 
            
            # Icons
            role_icon = "👤"
            if "Prof" in v['role']: role_icon = "🎓"
            if "Fantôme" in v['role']: role_icon = "👻"
            if "Chat" in v['role'] or "Chien" in v['role']: role_icon = "🐾"
            
            # Stats Ratios
            lvl = v.get('level', 1)
            xp = v.get('xp', 0)
            
            # XP Bar width (Scaled by Level: Lv1=100, Lv2=200...)
            xp_needed = lvl * 100
            xp_pct = min(100, int((xp / xp_needed) * 100)) 
            
            # Stats (M: Magie, S: Social, P: Physique, K: Savoir)
            stats = v.get('stats', {})
            s_m = stats.get('MAGIE', 0)
            s_s = stats.get('SOCIAL', 0)
            s_p = stats.get('PHYSIQUE', 0)
            s_k = stats.get('SAVOIR', 0)
            
            stats_html = f"""
            <div style="margin-top:5px; font-size:0.7rem; color:#8c90a0; display:flex; justify-content:space-between;">
                <span>✨{s_m}</span> <span>💬{s_s}</span> <span>💪{s_p}</span> <span>📚{s_k}</span>
            </div>
            <div style="margin-top:5px; background:#374151; height:4px; border-radius:2px; width:100%;">
                <div style="background:#10b981; height:100%; border-radius:2px; width:{xp_pct}%;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:2px; font-size:0.65rem; opacity:0.7;">
                <span>LVL {lvl}</span> <span>{xp} XP</span>
            </div>
            """
            
            left_html += f"""<div class="stat-card {active_class}">
                <div class="stat-name">{role_icon} {name} <span style="float:right; font-weight:normal; opacity:0.6; font-size:0.8rem;">{v['role']}</span></div>
                {stats_html}
                <div style="font-size:0.7rem; color:#6b7280; margin-top:2px;">📍 {v['pos']}</div>
            </div>"""
            
        left_html += "</div>"
        st.markdown(left_html, unsafe_allow_html=True)

    # CENTER PANEL (TABS)
    with col_center:
        tab_map, tab_rel = st.tabs(["🗺️ CARTE", "❤️ RELATIONS"])
        
        with tab_map:
            center_html = '<div class="panel" style="height: 80vh; padding:0; background:#111; display:flex; align-items:center; justify-content:center;">'
            
            cells_html = ""
            for y in range(grid_size):
                for x in range(grid_size):
                    char = map_layout[y][x]
                    col = map_colors.get(char, "#111")
                    
                    markers = ""
                    # 1. Villagers
                    for v_name, v_data in characters.items():
                        if v_data['pos'] == [x, y]:
                             # Professional Dot
                             color = "#fff" 
                             if "Prof" in v_data['role']: color = "#eab308" # Gold
                             if "Étudiant" in v_data['role']: color = "#3b82f6" # Blue
                             markers += f'<div class="map-marker" style="background:{color};" title="{v_name}"></div>'
                    
                    # 2. Objects
                    if map_objects:
                        for obj in map_objects:
                            if obj['pos'] == [x, y]:
                                markers += f'<div style="position:absolute; bottom:0; right:0; width:6px; height:6px; background:#10b981; border-radius:50%;"></div>'

                    cells_html += f'<div class="map-cell" style="background:{col}; position:relative; width:100%; height:100%; border:0.5px solid rgba(255,255,255,0.03);">{markers}</div>'
                    
            # GRID
            center_html += f"""<div style="display: grid; grid-template-columns: repeat({grid_size}, 1fr); grid-template-rows: repeat({grid_size}, 1fr); width: 100%; aspect-ratio: 1/1; max-height: 100%;">
    {cells_html}
    </div>"""
            center_html += "</div>"
            st.markdown(center_html, unsafe_allow_html=True)
            
        with tab_rel:
            # Heatmap Matrix using CSS Grid
            names = list(characters.keys())
            count = len(names)
            
            matrix_html = f'<div class="panel" style="height: 80vh; overflow:auto;">'
            matrix_html += f'<div style="display:grid; grid-template-columns: 80px repeat({count}, 1fr); gap:2px; font-size:0.7rem;">'
            
            # Header Row
            matrix_html += "<div></div>" # Corner
            for n in names:
                matrix_html += f'<div style="transform: rotate(-45deg); height:50px; display:flex; align-items:flex-end;">{n[:6]}</div>'
            
            # Rows
            for source in names:
                matrix_html += f'<div style="font-weight:bold; text-align:right; padding-right:5px;">{source[:8]}</div>'
                for target in names:
                    if source == target:
                        matrix_html += '<div style="background:#333;"></div>'
                    else:
                        rel_val = characters[source].get('rel', {}).get(target, 0)
                        # Color Scale
                        bg = "#444"
                        if rel_val > 50: bg = "#064e3b" # Dark Green
                        elif rel_val > 10: bg = "#065f46"
                        elif rel_val < -50: bg = "#7f1d1d" # Red
                        elif rel_val < -10: bg = "#991b1b"
                        
                        matrix_html += f'<div style="background:{bg}; color:#fff; display:flex; align-items:center; justify-content:center;" title="{source}->{target}: {rel_val}">{rel_val}</div>'
                        
            matrix_html += "</div></div>"
            st.markdown(matrix_html, unsafe_allow_html=True)

    # RIGHT PANEL
    with col_right:
        safe_text = story_text.replace("\n", "<br>")
        right_html = f"""<div class="panel" style="height: 80vh;">
            <div class="panel-header"><span>JOURNAL NARRATIF</span> <span>LIVE</span></div>
            <div class="story-feed">{safe_text}</div>
        </div>"""
        st.markdown(right_html, unsafe_allow_html=True)

