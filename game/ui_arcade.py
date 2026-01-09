import arcade
import random
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
COLOR_GRASS = (34, 139, 34)
COLOR_FOREST = (0, 100, 0)
COLOR_MOUNTAIN = (139, 69, 19)
COLOR_VILLAGE = (210, 180, 140)

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
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)
        
        # 1. Generate Map Texture/ShapeList
        self.shape_list = arcade.ShapeElementList()
        
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
                # Flip Y for OpenGL (bottom-up) vs Grid (top-down)
                # Let's keep 0,0 at bottom left for rendering simplicity?
                # Or match grid: 0,0 top-left? 
                # Arcade 0,0 is bottom-left. 
                # Grid 0,0 is usually Top-Left (matrix style).
                # Render Y = HEIGHT - (y * TILE)
                
                screen_x = offset_x + (x * TILE_SIZE) + TILE_SIZE/2
                screen_y = offset_y + ((GRID_SIZE - 1 - y) * TILE_SIZE) + TILE_SIZE/2
                
                color = COLOR_OCEAN
                if char == '.': color = COLOR_GRASS
                elif char == 'T': color = COLOR_FOREST
                elif char == 'M': color = COLOR_MOUNTAIN
                elif char == 'H': color = COLOR_VILLAGE
                
                rect = arcade.create_rectangle_filled(screen_x, screen_y, TILE_SIZE, TILE_SIZE, color)
                self.shape_list.append(rect)

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
                sprite.center_x = screen_x
                sprite.center_y = screen_y

    def on_draw(self):
        """ Render the screen. """
        self.clear()
        
        # World Projection
        self.camera.use()
        self.shape_list.draw() # Map
        self.agent_sprites.draw() # Agents
        
        # GUI Projection
        self.gui_camera.use()
        
        # HUD Top-Right
        time_min = self.shared_state.get('world_time', 0)
        h = time_min // 60
        m = time_min % 60
        weather = self.shared_state.get('weather', "?")
        
        hud_text = f"{h:02d}h{m:02d}\n{weather}"
        arcade.draw_text(
            hud_text, 
            SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10, 
            arcade.color.WHITE, 
            font_size=16, 
            width=200, 
            align="right",
            anchor_x="right", 
            anchor_y="top",
            bold=True
        )

        # Agent Count Debug
        arcade.draw_text(
            f"Agents: {len(self.agent_sprites)}", 
            10, SCREEN_HEIGHT - 20, 
            arcade.color.YELLOW, 12
        )
