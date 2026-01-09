import arcade
import arcade.gui
import random
import copy
from collections import namedtuple

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TITLE = "MyVillage - Simulation Vie Artificielle"
TILE_SIZE = 24  # Base tile size in pixels
GRID_SIZE = 32  # Number of tiles per axis
MAP_PIXEL_SIZE = GRID_SIZE * TILE_SIZE

# Colors
COLOR_OCEAN = (30, 60, 100)
# Colors (Modern Palette)
COLOR_OCEAN = (100, 149, 237)   # Cornflower Blue
COLOR_GRASS = (144, 238, 144)   # Light Green
COLOR_FOREST = (34, 139, 34)    # Forest Green
COLOR_MOUNTAIN = (169, 169, 169) # Dark Gray
COLOR_VILLAGE = (222, 184, 135) # Burlywood

class AgentSprite(arcade.Sprite):
    """ Visual representation of an agent """
    def __init__(self, name, role, x, y):
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png", scale=0.5)
        self.agent_name = name
        self.role = role
        # Position in Grid Coords
        self.target_grid_x = x
        self.target_grid_y = y
        # Convert to screen (will be updated by window)
        self.center_x = x * TILE_SIZE + TILE_SIZE/2
        self.center_y = y * TILE_SIZE + TILE_SIZE/2
        
        # Color code by role? using `color` tint
        if "Maire" in role: self.color = arcade.color.RED
        elif "Forgeron" in role: self.color = arcade.color.ORANGE
        else: self.color = arcade.color.WHITE

    def update_position(self, grid_x, grid_y):
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        # Interpolation Logic would go here in update()

class VillageWindow(arcade.Window):
    def __init__(self, shared_state):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, resizable=True)
        self.background_color = arcade.color.BLACK
        
        self.shared_state = shared_state # Dict or Object shared with Engine Thread
        
        self.scene = None
        self.camera = None
        self.gui_camera = None
        self.tile_map = None
        
        self.agent_sprites = arcade.SpriteList()
        self.agents_map = {} # name -> sprite

    def setup(self):
        """ Set up the game and initialize the variables. """
        # Camera
        self.camera = arcade.camera.Camera2D(window=self)
        self.gui_camera = arcade.camera.Camera2D(window=self)
        
        # Performance Monitoring
        arcade.enable_timings()
        self.perf_graph = arcade.PerfGraph(width=200, height=40, graph_data="FPS")
        self.perf_graph.position = (SCREEN_WIDTH - 210, SCREEN_HEIGHT - 60)
        self.perf_list = arcade.SpriteList()
        self.perf_list.append(self.perf_graph)

        # UI Manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.setup_ui()

        # Persistent Text Objects (Optimization)
        self.hud_text = arcade.Text(
            "", SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10, 
            arcade.color.WHITE, font_size=16, width=200, 
            align="right", anchor_x="right", anchor_y="top", bold=True
        )
        self.debug_text = arcade.Text(
            "", 10, SCREEN_HEIGHT - 20, 
            arcade.color.YELLOW, font_size=12
        )

    def setup_ui(self):
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the Reset Button
        reset_button = arcade.gui.UIFlatButton(text="🗑️ Reset", width=100)
        
        # Arcade 3.0: with_padding is the correct method
        self.v_box.add(reset_button.with_padding(bottom=20))

        # Handle Click
        # Handle Click
        reset_button.on_click = self.reset_simulation
            

        # Create a widget to hold the v_box widget, that will center the buttons
        # Arcade 3.0: UIAnchorLayout replaces UIAnchorWidget
        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(child=self.v_box, anchor_x="left", anchor_y="bottom")
        
        self.manager.add(anchor_layout)

        
        # 1. Generate Map Texture/ShapeList
        # Optimization: use_spatial_hash=True for static map tiles
        self.tile_sprites = arcade.SpriteList(use_spatial_hash=True)
        
        map_layout = self.shared_state.get('map_layout', [])
        map_legend = self.shared_state.get('map_legend', {})
        
        offset_x = (SCREEN_WIDTH - MAP_PIXEL_SIZE) // 2
        offset_y = (SCREEN_HEIGHT - MAP_PIXEL_SIZE) // 2
        self.map_offset = (offset_x, offset_y)
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Build Map
        for y, row in enumerate(map_layout):
            for x, char in enumerate(row):
                screen_x = offset_x + (x * TILE_SIZE) + TILE_SIZE/2
                screen_y = offset_y + ((GRID_SIZE - 1 - y) * TILE_SIZE) + TILE_SIZE/2
                
                color = COLOR_OCEAN
                if char == '.': color = COLOR_GRASS
                elif char == 'T': color = COLOR_FOREST
                elif char == 'M': color = COLOR_MOUNTAIN
                elif char == 'H': color = COLOR_VILLAGE
                
                # Arcade 3.0: Use Sprites for tiles
                tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, color)
                tile.center_x = screen_x
                tile.center_y = screen_y
                self.tile_sprites.append(tile)

    def reset_simulation(self, event):
        """ Callback to reset the game state """
        print("🗑️ RESET GAME REQUESTED")
        # Clear State
        self.shared_state['logs'] = []
        self.shared_state['world_time'] = 1200
        self.shared_state['weather'] = "Chaud"
        
        # Reset Characters from SEED
        if 'initial_seed' in self.shared_state:
            seed = self.shared_state['initial_seed']
            self.shared_state['characters'] = copy.deepcopy(seed['characters'])
            self.agent_sprites.clear()
            self.agents_map.clear()
            print("✅ Game State Reset to Seed.")
        else:
             print("⚠️ Cannot reset: initial_seed not found in shared_state")

    def on_update(self, delta_time):
        """ Movement and game logic """
        # Sync with Shared State
        characters_data = self.shared_state.get('characters', {})
        
        # Add new agents
        for name, data in characters_data.items():
            if name not in self.agents_map:
                gx, gy = data['pos']
                role = data.get('role', 'Villager')
                sprite = AgentSprite(name, role, gx, gy)
                self.agent_sprites.append(sprite)
                self.agents_map[name] = sprite
            else:
                # Update existing
                sprite = self.agents_map[name]
                gx, gy = data['pos']
                
                # Convert Grid -> Screen
                ox, oy = self.map_offset
                screen_x = ox + (gx * TILE_SIZE) + TILE_SIZE/2
                screen_y = oy + ((GRID_SIZE - 1 - gy) * TILE_SIZE) + TILE_SIZE/2
                
                # Simple LERRP or Snap
                sprite.center_y = screen_y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """ Handle camera panning """
        if buttons == arcade.MOUSE_BUTTON_RIGHT:
            self.camera.position = (
                self.camera.position[0] - dx,
                self.camera.position[1] - dy
            )

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """ Handle camera zooming """
        zoom_speed = 0.1
        if scroll_y > 0:
            self.camera.zoom += zoom_speed
        elif scroll_y < 0:
            self.camera.zoom -= zoom_speed
            if self.camera.zoom < 0.1: self.camera.zoom = 0.1

    def on_draw(self):
        """ Render the screen. """
        self.clear()
        
        # World Projection
        self.camera.use()
        self.tile_sprites.draw() # Map
        self.agent_sprites.draw() # Agents
        
        # GUI Projection
        self.gui_camera.use()
        self.manager.draw()
        
        # HUD Top-Right
        time_min = self.shared_state.get('world_time', 0)
        h = time_min // 60
        m = time_min % 60
        weather = self.shared_state.get('weather', "?")
        
        # Update Text Content
        self.hud_text.text = f"{h:02d}h{m:02d}\n{weather}"
        self.hud_text.draw()

        # Agent Count Debug
        # Agent Count Debug
        self.debug_text.text = f"Agents: {len(self.agent_sprites)}"
        self.debug_text.draw()
        
        # Performance Graph
        self.perf_list.draw()
