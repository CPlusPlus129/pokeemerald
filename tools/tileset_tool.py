#!/usr/bin/env python3
import argparse
import os
import struct
from PIL import Image, ImageOps, ImageDraw, ImageFont
import map_tool

class TilesetVisualizer:
    def __init__(self, project_root):
        self.root = project_root
        self.viz = map_tool.MapVisualizer(project_root)

    def render_tileset(self, tileset_key, output_file, is_secondary=False):
        ts_path = self.viz.find_tileset_path(tileset_key)
        if not ts_path:
            print(f"Error: Could not find tileset path for {tileset_key}")
            return

        ts_img, ts_meta = self.viz.load_tileset_graphics(ts_path)
        if not ts_img or not ts_meta:
            print(f"Error: Could not load graphics/metatiles for {ts_path}")
            return

        num_metatiles = len(ts_meta) // 16
        cols = 16
        rows = (num_metatiles + cols - 1) // cols
        
        canvas_width = cols * 16
        canvas_height = rows * 16
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Try to load a font for labeling
        try:
            font = ImageFont.load_default()
        except:
            font = None

        for i in range(num_metatiles):
            mx_start = (i % cols) * 16
            my_start = (i // cols) * 16
            
            offset = i * 16
            meta_entry = ts_meta[offset : offset + 16]
            tiles = struct.unpack("<8H", meta_entry)
            
            # Render the 4 base tiles (Layer 1) and 4 overlay tiles (Layer 2)
            for t_idx in range(8):
                tile_def = tiles[t_idx]
                tile_id = tile_def & 0x3FF
                h_flip = (tile_def >> 10) & 1
                v_flip = (tile_def >> 11) & 1
                
                sub_idx = t_idx % 4
                layer = t_idx // 4
                
                dx = mx_start + (sub_idx % 2) * 8
                dy = my_start + (sub_idx // 2) * 8
                
                src_x = (tile_id % 16) * 8
                src_y = (tile_id // 16) * 8
                
                if src_y + 8 > ts_img.height: continue
                
                try:
                    tile = ts_img.crop((src_x, src_y, src_x + 8, src_y + 8))
                    if h_flip: tile = ImageOps.mirror(tile)
                    if v_flip: tile = ImageOps.flip(tile)
                    canvas.paste(tile, (dx, dy), tile)
                except:
                    pass
            
            # Label with ID (Hex)
            display_id = hex(i + 0x200 if is_secondary else i)
            if font:
                draw.text((mx_start + 1, my_start + 1), display_id.replace("0x", ""), fill=(255, 255, 255, 128), font=font)

        canvas.save(output_file)
        print(f"Rendered tileset {tileset_key} to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Tileset Visualizer")
    parser.add_argument("tileset_key", help="e.g. gTileset_General or gTileset_Petalburg")
    parser.add_argument("output", help="Output filename (PNG)")
    parser.add_argument("--secondary", action="store_true", help="Treat as secondary tileset (offsets IDs by 0x200)")
    
    args = parser.parse_args()
    
    # Change dir to script location so relative imports work if needed
    # But map_tool is in root
    visualizer = TilesetVisualizer(".")
    visualizer.render_tileset(args.tileset_key, args.output, args.secondary)

if __name__ == "__main__":
    main()
