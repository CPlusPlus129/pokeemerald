import map_tool

def analyze_layouts():
    viz = map_tool.MapVisualizer(".")
    project = viz.project
    
    layouts = [
        ("MauvilleCity", "LAYOUT_MAUVILLE_CITY"),
        ("OldaleTown", "LAYOUT_OLDALE_TOWN")
    ]
    
    for name, layout_id in layouts:
        print(f"\nAnalyzing {name} ({layout_id})...")
        try:
            blocks, width, height, path = project.read_blockdata(layout_id)
            
            # Print a small section to identify ground/fence
            # For Mauville, let's look at the bottom row (Y=19) to find fences?
            # Or Y=0 (Top)
            
            if name == "MauvilleCity":
                print("--- Secondary Blocks in Mauville ---")
                secondary_blocks = {}
                for i, val in enumerate(blocks):
                     metatile = val & 0x3FF
                     if metatile >= 0x200:
                         secondary_blocks[metatile] = secondary_blocks.get(metatile, 0) + 1
                
                # Sort by frequency
                sorted_blocks = sorted(secondary_blocks.items(), key=lambda x: x[1], reverse=True)
                print(f"Top 10 Secondary Blocks: {sorted_blocks[:10]}")


            if name == "OldaleTown":
                # Print Center Area to see current ground
                print("--- Center Area (10,10) ---")
                for y in range(9, 12):
                    row = []
                    for x in range(9, 12):
                        idx = y * width + x
                        val = blocks[idx] & 0x3FF
                        row.append(hex(val))
                    print(f"Y={y}: {row}")
        
        except Exception as e:
            print(f"Error reading {name}: {e}")

if __name__ == "__main__":
    analyze_layouts()
