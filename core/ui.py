import streamlit as st

def inject_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    :root {
      --glass-bg: rgba(255, 255, 255, 0.08);
      --glass-border: rgba(255, 255, 255, 0.15);
      --accent-color: #00f2ff;
      --text-color: #e0e0e0;
    }

    /* Override Streamlit Base */
    .stApp {
        background: radial-gradient(circle at center, #1a2a3a 0%, #0a0f14 100%);
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }
    
    /* Hide Streamlit Elements */
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    
    /* Custom App Container */
    .app-container {
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        backdrop-filter: blur(20px);
        background: var(--glass-bg);
        padding: 20px;
    }

    /* Header & Avatars */
    .ui-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--glass-border);
      margin-bottom: 20px;
    }
    
    .scenario-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--accent-color);
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .character-group {
      display: flex;
      gap: 15px;
    }

    .avatar-box {
      position: relative;
      cursor: pointer;
    }

    .avatar {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      border: 2px solid transparent;
      padding: 2px;
      transition: all 0.3s ease;
      filter: grayscale(0.8);
      object-fit: cover;
      background: #222;
    }

    .avatar:hover, .avatar.active {
      border-color: var(--accent-color);
      filter: grayscale(0);
      box-shadow: 0 0 15px var(--accent-color);
    }
    
    .avatar-badge {
        position: absolute;
        bottom: -5px;
        right: -5px;
        background: #000;
        color: white;
        font-size: 0.7rem;
        padding: 2px 5px;
        border-radius: 4px;
        border: 1px solid #444;
    }

    /* Map Panel */
    .map-placeholder {
      background: rgba(0,0,0,0.3);
      border-radius: 16px;
      border: 1px solid var(--glass-border);
      padding: 10px;
      box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }

    /* Grid Styling */
    .map-grid {
        display: grid;
        grid-template-columns: repeat(32, 1fr);
        gap: 1px;
        aspect-ratio: 1/1;
        width: 100%;
    }
    
    .map-cell {
        position: relative;
        width: 100%;
        height: 100%;
    }
    
    .char-marker {
        font-size: 2rem; 
        filter: drop-shadow(0 0 5px var(--accent-color));
        animation: pulse 2s infinite;
        background: radial-gradient(circle, rgba(0,0,0,0.8) 0%, transparent 70%);
        border-radius: 50%;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }

    /* Story Panel */
    .story-panel {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 16px;
      padding: 25px;
      height: 600px;
      overflow-y: auto;
      border: 1px solid var(--glass-border);
    }
    
    .story-content {
        font-family: 'Georgia', serif;
        line-height: 1.8;
        font-size: 1.1rem;
        color: #ddd;
    }
    
    .story-block {
        margin-bottom: 25px;
        padding-left: 15px;
        border-left: 2px solid #444;
        animation: fadeIn 1s ease-in;
    }
    
    .current-writing {
        border-left: 3px solid var(--accent-color);
        background: linear-gradient(90deg, rgba(0,242,255,0.05) 0%, transparent 100%);
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    /* Buttons */
    div[data-testid="stButton"] button {
        background: var(--glass-bg);
        border: 1px solid var(--accent-color);
        color: var(--accent-color);
        width: 100%;
        border-radius: 12px;
        font-size: 18px;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    div[data-testid="stButton"] button:hover {
        background: var(--accent-color);
        color: #000;
        box-shadow: 0 0 20px var(--accent-color);
        border-color: var(--accent-color);
    }
    
    /* Loading Animation */
    .glass-loader {
        display: inline-block;
        position: relative;
        width: 80px;
        height: 80px;
    }
    .glass-loader:after {
        content: " ";
        display: block;
        border-radius: 50%;
        width: 0;
        height: 0;
        margin: 8px;
        box-sizing: border-box;
        border: 32px solid var(--accent-color);
        border-color: var(--accent-color) transparent var(--accent-color) transparent;
        animation: glass-loader 1.2s infinite;
    }
    @keyframes glass-loader {
        0% { transform: rotate(0); animation-timing-function: cubic-bezier(0.55, 0.055, 0.675, 0.19); }
        50% { transform: rotate(900deg); animation-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1); }
        100% { transform: rotate(1800deg); }
    }
    
    /* Page Turn Animation */
    .slide-in-right {
        animation: slideInRight 0.5s ease-out forwards;
    }
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(50px); }
        to { opacity: 1; transform: translateX(0); }
    }

</style>
""", unsafe_allow_html=True)

def render_header(scenario_name, world_time, villagers):
    avatars_html = ""
    for name, v in villagers.items():
        icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png"
        if "John" in name: icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140037.png"
        if "Barbie" in name: icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"
        
        # Flattened HTML for Markdown compatibility
        avatars_html += f'<div class="avatar-box" title="{name} | 🔋{v["energy"]}%"><img src="{icon_url}" class="avatar active"><div class="avatar-badge">{v["energy"]}%</div></div>'

    header_html = f'''
    <div class="ui-header">
    <div class="scenario-title">{scenario_name} <span style="font-size:0.8rem; opacity:0.6">| Jour {world_time // 24 + 1} - {world_time}h00</span></div>
    <div class="character-group">
    {avatars_html}
    </div>
    </div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)

def render_map(grid_size, map_layout, map_colors, villagers):
    grid_html = '<div class="map-grid">'
    for y in range(grid_size):
        for x in range(grid_size):
            char_terrain = map_layout[y][x]
            color = map_colors.get(char_terrain, "#111")
            
            content = ""
            for p_name, p_data in villagers.items():
                if p_data['pos'] == [x, y]:
                    avatar = "👱‍♀️" if "Barbie" in p_name else "👮‍♂️" if "John" in p_name else "👨‍🔬"
                    content = f'<div class="char-marker">{avatar}</div>'
            
            if not content:
                if char_terrain == "?": content = "📦"
                if char_terrain == "A": content = "✈️"
                
            grid_html += f'<div class="map-cell" style="background-color: {color}; display:flex; align-items:center; justify-content:center;">{content}</div>'
            
    grid_html += '</div>'
    
    st.markdown('<div class="map-placeholder">', unsafe_allow_html=True)
    st.markdown(grid_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_loader():
    st.markdown('<div style="display:flex; justify-content:center; align-items:center; height:600px;"><div class="glass-loader"></div></div>', unsafe_allow_html=True)

def render_story_page(content, page_num, total_pages):
    st.markdown('<div class="story-panel">', unsafe_allow_html=True)
    if content:
        clean_page = content.replace("### ", "").replace("\n", "<br>")
        st.markdown(f'<div class="story-content slide-in-right"><div class="story-block">{clean_page}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; opacity:0.5; font-size:0.8rem; margin-top:20px;">Page {page_num} / {total_pages}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="story-content"><i>Le livre est vide...</i></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
