import streamlit as st

def inject_custom_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap');

    :root {
      --bg-color: #0f0518; /* Deep Void Purple */
      --panel-bg: rgba(30, 15, 45, 0.7); /* Glassy Purple */
      --border-color: rgba(189, 147, 249, 0.2);
      --accent-gold: #d4af37;
      --accent-neon: #ff00ff;
      --text-main: #e0d0f5;
      --text-dim: #9aa5b1;
    }

    .stApp {
        background: radial-gradient(circle at 50% 20%, #2a0e45 0%, #05010a 100%);
        font-family: 'Lato', sans-serif;
        color: var(--text-main);
    }
    
    /* Remove Padding */
    .main .block-container {
        padding: 1rem 2rem !important;
        max-width: 100% !important;
    }
    header, footer {visibility: hidden;}
    
    /* PANELS (Bento Grid style) */
    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .panel:hover {
        border-color: rgba(212, 175, 55, 0.3); /* Subtle Gold Glow */
    }
    
    .panel-header {
        font-family: 'Playfair Display', serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 1rem;
        color: var(--accent-gold);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* LEFT: STAT CARDS */
    .stat-card {
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border-left: 3px solid #332b40;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateX(5px); }
    .stat-card.active { 
        border-left-color: var(--accent-neon);
        box-shadow: inset 0 0 20px rgba(255, 0, 255, 0.05);
    }
    
    .stat-name { 
        font-family: 'Playfair Display', serif; 
        font-weight: 700; 
        font-size: 1.1rem; 
        color: #fff; 
    }
    
    /* CENTER: MAP */
    .map-container {
        width: 100%;
        aspect-ratio: 1/1;
        background: #050b14;
        border-radius: 8px;
        position: relative;
        box-shadow: inset 0 0 50px #000;
        overflow: hidden;
    }
    
    .map-grid {
        display: grid;
        width: 100%;
        height: 100%;
    }
    
    .map-marker {
        position: absolute;
        width: 70%; height: 70%;
        top: 15%; left: 15%;
        border-radius: 50%;
        border: 2px solid #fff;
        box-shadow: 0 0 10px var(--accent-neon);
        z-index: 10;
        transition: all 0.5s ease-in-out;
    }
    
    /* RIGHT: STORY FEED */
    .story-feed {
        overflow-y: auto;
        font-family: 'Georgia', serif; /* Book look */
        font-size: 1rem;
        line-height: 1.7;
        color: #eaddcf; /* Paper-ish text */
        height: 100%;
        padding-right: 10px;
    }
    
    .story-feed::-webkit-scrollbar { width: 6px; }
    .story-feed::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
    
    /* BUTTONS */
    .stButton button {
        background: linear-gradient(45deg, #2a0e45, #5a1e96);
        color: #fff;
        border: 1px solid rgba(255,255,255,0.1);
        font-family: 'Playfair Display', serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 10px 20px;
        border-radius: 30px;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: linear-gradient(45deg, #4b1a7a, #8a2be2);
        box-shadow: 0 0 15px rgba(138, 43, 226, 0.4);
        border-color: var(--accent-gold);
    }
    
    /* Remove Padding (Aggressive) */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
        margin-top: 0rem !important;
    }
    
    header, footer {visibility: hidden;}

</style>
    """, unsafe_allow_html=True)

def render_dashboard(characters, world_time, map_layout, map_colors, story_text, logs, map_objects=None):
    
    # ... (CSS Inject calls) ...
    inject_custom_css()
    
    # ... (Header) ...
    # ... (Header) ...
    # ... (Styles injected above) ...
    # Ensure Map Grid is strictly sized
    grid_size = len(map_layout)
    
    # ... (Header) ...
    st.markdown(f"""
    <div style="text-align:center; font-family:'Playfair Display', serif; color:#d4af37; font-size:1.5rem; letter-spacing:4px; margin-bottom:20px;">
        EROS CLUB <span style="font-size:0.8rem; color:#fff; vertical-align:middle; opacity:0.5;">| {world_time}H00 | JOUR {world_time//24 + 1}</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1, 2, 1], gap="medium")
    
    
    # LEFT PANEL
    with col_left:
        st.markdown('<div class="panel" style="height: 80vh; overflow-y: auto;">', unsafe_allow_html=True)
        st.markdown(f'<div class="panel-header"><span>CLUBBERS</span> <span>{len(characters)} PRÉSENTS</span></div>', unsafe_allow_html=True)
        
        for name, v in characters.items():
            active_class = "active" if v.get('excitation', 0) > 50 else ""
            
            # Icons
            role_icon = "👤"
            if "Barmaid" in v['role']: role_icon = "🍹"
            if "Hôtesse" in v['role']: role_icon = "🌸"
            if "Videur" in v['role']: role_icon = "🛡️"
            if "Barman" in v['role']: role_icon = "🍺"
            
            # HTML Construction (No Indent to avoid Code Block)
            stats_html = f"""<div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.8rem; color:#ccc;">
<span title="Energie">⚡ {v.get('energy', 100)}%</span>
<span title="Excitation" style="color:#ff69b4;">❤️ {v.get('excitation', 0)}%</span>
<span title="Alcool">🍷 {v.get('alcohol', 0.0)}g</span>
</div>"""
            
            card_html = f"""<div class="stat-card {active_class}">
<div class="stat-name">{role_icon} {name} <span style="float:right; font-size:0.7rem; opacity:0.7;">{v['role']}</span></div>
{stats_html}
<div class="stat-meta" style="margin-top:4px;">📍 {str(v['pos'])}</div>
<div class="stat-meta" style="font-style:italic; font-size:0.7rem; color:#888;">🎒 {', '.join(v.get('inventory', [])[:2])}</div>
</div>"""
            
            st.markdown(card_html, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # CENTER MAP
    with col_center:
        st.markdown('<div class="panel" style="height: 80vh; padding:0; background:#050b14; display:flex; align-items:center; justify-content:center;">', unsafe_allow_html=True)
        
        cells_html = ""
        for y in range(grid_size):
            for x in range(grid_size):
                char = map_layout[y][x]
                col = map_colors.get(char, "#111")
                
                markers = ""
                # 1. Villagers
                for v_name, v_data in characters.items():
                    if v_data['pos'] == [x, y]:
                         color = "red" # Client default
                         if "Hôtesse" in v_data['role']: color = "gold"
                         if "Barmaid" in v_data['role']: color = "cyan"
                         if "Barman" in v_data['role']: color = "cyan"
                         if "Videur" in v_data['role']: color = "#555"
                         markers += f'<div class="map-marker" style="background:{color}; box-shadow: 0 0 5px {color};" title="{v_name}"></div>'
                
                # 2. Objects
                if map_objects:
                    for obj in map_objects:
                        if obj['pos'] == [x, y]:
                            markers += f'<div style="position:absolute; bottom:0; right:0; font-size:10px; line-height:1;">🎁</div>'

                cells_html += f'<div class="map-cell" style="background:{col}; position:relative; width:100%; height:100%;">{markers}</div>'
                
        # GRID CONTAINER
        st.markdown(f"""
        <div style="
            display: grid;
            grid-template-columns: repeat({grid_size}, 1fr);
            grid-template-rows: repeat({grid_size}, 1fr);
            width: 100%;
            aspect-ratio: 1/1;
            max-height: 100%;
        ">
            {cells_html}
        </div>
        """, unsafe_allow_html=True)
        
        # LEGEND OVERLAY
        st.markdown("""
        <div style="position:absolute; bottom:10px; left:10px; color:#fff; font-size:0.7rem; background:rgba(0,0,0,0.7); padding:5px; border-radius:4px; pointer-events:none;">
            D: Dance | B: Bar | X: Calin | L: Lounge | P: Piscine
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT PANEL
    with col_right:
        st.markdown('<div class="panel" style="height: 80vh;">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header"><span>SCENARIO</span> <span>LIVE</span></div>', unsafe_allow_html=True)
        
        safe_text = story_text.replace("\n", "<br>")
        st.markdown(f'<div class="story-feed">{safe_text}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

