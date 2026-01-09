import arcade
import arcade.gui

print("Arcade Version:", arcade.__version__)
# Create hidden window for context
window = arcade.Window(100, 100, visible=False)

print("\n--- arcade.gui attributes ---")
for x in dir(arcade.gui):
    if "UI" in x:
        print(x)

print("\n--- UIAnchorLayout attributes ---")
try:
    layout = arcade.gui.UIAnchorLayout()
    for x in dir(layout):
        if "add" in x:
            print(f"Layout method: {x}")
            # Try to inspect signature? Hard in script.
except Exception as e:
    print(f"Error creating layout: {e}")

window.close()
