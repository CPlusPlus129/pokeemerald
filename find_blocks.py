import map_tool
import os

def analyze_layouts():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    viz = map_tool.MapVisualizer(".")
    project = viz.project
    
    # Analyze a house in Littleroot (BrendansHouse_1F)
    # Analyze Pokemon Center in Petalburg
    # Analyze Mauville City center
    
    targets = [
        ("Petalburg_PokeCenter", "LAYOUT_POKEMON_CENTER_1F"),
        ("Mauville_Gym", "LAYOUT_MAUVILLE_CITY_GYM")
    ]
    
    for name, layout_id in targets:
        print(f"\nAnalyzing {name} ({layout_id})...")
        try:
            blocks, width, height, path = project.read_blockdata(layout_id)
            print(f"Dimensions: {width}x{height}")
            # Print unique blocks
            unique_blocks = set()
            for val in blocks:
                unique_blocks.add(val & 0x3FF)
            sorted_unique = sorted(list(unique_blocks))
            print(f"Unique Metatiles: {[hex(b) for b in sorted_unique]}")
            
            # Print a 5x5 slice of the center to see floor/wall patterns
            cx, cy = width // 2, height // 2
            print(f"Slice around ({cx}, {cy}):")
            for y in range(max(0, cy-2), min(height, cy+3)):
                row = []
                for x in range(max(0, cx-2), min(width, cx+3)):
                    idx = y * width + x
                    row.append(hex(blocks[idx] & 0x3FF))
                print(f"Y={y}: {row}")

        except Exception as e:
            print(f"Error reading {name}: {e}")

if __name__ == "__main__":
    analyze_layouts()
