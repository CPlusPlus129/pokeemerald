#!/usr/bin/env python3
import argparse
import json
import os
import sys
import struct
import re
import subprocess
from collections import OrderedDict
from PIL import Image, ImageOps

# --- PoryCLI Classes (Simplified/Copied) ---

class BitPacker:
    def __init__(self, mask):
        self.mask = mask
        self.shift = 0
        temp = mask
        while temp > 0 and (temp & 1) == 0:
            temp >>= 1
            self.shift += 1
        self.max_value = temp

    def unpack(self, data):
        return (data & self.mask) >> self.shift

    def pack(self, value):
        return (value << self.shift) & self.mask

packer_metatile = BitPacker(0x3FF)
packer_collision = BitPacker(0xC00)
packer_elevation = BitPacker(0xF000)

class PoryProject:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.map_groups_path = os.path.join(self.root, "data", "maps", "map_groups.json")
        self.layouts_path = os.path.join(self.root, "data", "layouts", "layouts.json")
        self.maps = {}
        self.layouts = {}
        self.load_project()

    def load_project(self):
        if not os.path.exists(self.map_groups_path):
            raise FileNotFoundError(f"Could not find {self.map_groups_path}")
        if not os.path.exists(self.layouts_path):
            raise FileNotFoundError(f"Could not find {self.layouts_path}")

        with open(self.map_groups_path, "r") as f:
            self.map_groups = json.load(f, object_pairs_hook=OrderedDict)

        with open(self.layouts_path, "r") as f:
            layouts_data = json.load(f, object_pairs_hook=OrderedDict)
            if "layouts" in layouts_data and isinstance(layouts_data["layouts"], list):
                for layout in layouts_data["layouts"]:
                    if "id" in layout:
                        self.layouts[layout["id"]] = layout
            else:
                self.layouts = layouts_data

    def get_map_path(self, map_name):
        return os.path.join(self.root, "data", "maps", map_name, "map.json")

    def load_map(self, map_name):
        path = self.get_map_path(map_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Map file not found: {path}")
        with open(path, "r") as f:
            return json.load(f, object_pairs_hook=OrderedDict)

    def save_map(self, map_name, data):
        path = self.get_map_path(map_name)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def get_layout(self, layout_id):
        if layout_id not in self.layouts:
            raise ValueError(f"Unknown layout: {layout_id}")
        return self.layouts[layout_id]

    def read_blockdata(self, layout_id):
        layout = self.get_layout(layout_id)
        blockdata_path = os.path.join(self.root, layout["blockdata_filepath"])
        if not os.path.exists(blockdata_path):
            raise FileNotFoundError(f"Blockdata not found: {blockdata_path}")
        with open(blockdata_path, "rb") as f:
            data = f.read()
        blocks = []
        for i in range(0, len(data), 2):
            val = struct.unpack_from("<H", data, i)[0]
            blocks.append(val)
        return blocks, layout["width"], layout["height"], blockdata_path

    def write_blockdata(self, blockdata_path, blocks):
        with open(blockdata_path, "wb") as f:
            for val in blocks:
                f.write(struct.pack("<H", val))

# --- Visualizer ---

class MapVisualizer:
    def __init__(self, project_root):
        self.root = project_root
        self.project = PoryProject(project_root)

    def find_tileset_path(self, tileset_key):
        # e.g. gTileset_General -> general
        # gTileset_SecretBaseRedCave -> secret_base/red_cave
        
        name = tileset_key.replace("gTileset_", "")
        # Camel to Snake
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        snake_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Strategies to find the folder
        # 1. Direct match in primary/secondary
        for cat in ["primary", "secondary"]:
            p = os.path.join(self.root, "data", "tilesets", cat, snake_name)
            if os.path.exists(p):
                return p
        
        # 2. Recursive search
        # Search for folder that matches snake_name or is a suffix
        # e.g. snake_name = secret_base_red_cave, folder = red_cave
        
        best_match = None
        best_match_len = 0
        
        tilesets_dir = os.path.join(self.root, "data", "tilesets")
        for root, dirs, files in os.walk(tilesets_dir):
            dirname = os.path.basename(root)
            if dirname == snake_name:
                return root
            
            # Suffix check
            # if snake_name ends with dirname? 
            # e.g. secret_base_red_cave ends with red_cave
            if snake_name.endswith(dirname) and len(dirname) > best_match_len:
                 # Verify it's not a partial word match (e.g. "ave" matching "cave")
                 # Check if snake_name matches the path parts joined
                 # But we don't know the path parts easily without more logic.
                 # Let's just try it.
                 best_match = root
                 best_match_len = len(dirname)

        return best_match

    def load_tileset_graphics(self, tileset_path):
        if not tileset_path: return None, None
        img_path = os.path.join(tileset_path, "tiles.png")
        meta_path = os.path.join(tileset_path, "metatiles.bin")
        
        if not os.path.exists(img_path) or not os.path.exists(meta_path):
            # Fallback to .4bpp if .png missing? No, PIL needs image.
            return None, None
            
        try:
            img = Image.open(img_path).convert("RGBA")
            with open(meta_path, "rb") as f:
                meta_data = f.read()
            return img, meta_data
        except:
            return None, None

    def render_map(self, map_name, output_file):
        try:
            map_data = self.project.load_map(map_name)
        except Exception as e:
            print(f"Error loading map {map_name}: {e}")
            return

        layout_id = map_data["layout"]
        layout = self.project.get_layout(layout_id)
        blocks, width, height, _ = self.project.read_blockdata(layout_id)
        
        p_key = layout["primary_tileset"]
        s_key = layout["secondary_tileset"]
        
        p_path = self.find_tileset_path(p_key)
        s_path = self.find_tileset_path(s_key)
        
        p_img, p_meta = self.load_tileset_graphics(p_path)
        s_img, s_meta = self.load_tileset_graphics(s_path)
        
        if not p_img or not p_meta:
            print(f"Error: Could not load primary tileset {p_key}")
            # Create fallback
            p_img = Image.new("RGBA", (128, 128), (255, 0, 255, 255))
            p_meta = b'\0' * 10000

        if not s_img or not s_meta:
            print(f"Warning: Could not load secondary tileset {s_key}")
            s_img = p_img
            s_meta = p_meta

        canvas = Image.new("RGBA", (width * 16, height * 16), (0, 0, 0, 255))
        
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx >= len(blocks): continue
                
                block_val = blocks[idx]
                metatile_id = block_val & 0x3FF
                
                is_secondary = metatile_id >= 0x200
                local_id = metatile_id - 0x200 if is_secondary else metatile_id
                
                ts_img = s_img if is_secondary else p_img
                ts_meta = s_meta if is_secondary else p_meta
                
                offset = local_id * 16 # 8 tiles * 2 bytes
                if offset + 16 > len(ts_meta):
                    continue
                
                meta_entry = ts_meta[offset : offset + 16]
                tiles = struct.unpack("<8H", meta_entry)
                
                # Draw tiles
                # Layer 1: 0-3, Layer 2: 4-7
                for i in range(8):
                    tile_def = tiles[i]
                    tile_idx = tile_def & 0x3FF
                    h_flip = (tile_def >> 10) & 1
                    v_flip = (tile_def >> 11) & 1
                    
                    sub_idx = i % 4
                    layer = i // 4
                    
                    mx = (sub_idx % 2) * 8
                    my = (sub_idx // 2) * 8
                    dest_x = x * 16 + mx
                    dest_y = y * 16 + my
                    
                    src_x = (tile_idx % 16) * 8
                    src_y = (tile_idx // 16) * 8
                    
                    if src_y + 8 > ts_img.height: continue

                    try:
                        tile = ts_img.crop((src_x, src_y, src_x + 8, src_y + 8))
                        if h_flip: tile = ImageOps.mirror(tile)
                        if v_flip: tile = ImageOps.flip(tile)
                        
                        if layer == 1:
                             # Simple transparency check if not handled by RGBA
                             pass
                        
                        canvas.paste(tile, (dest_x, dest_y), tile)
                    except:
                        pass
                        
        canvas.save(output_file)
        print(f"Rendered map to {output_file}")

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Map Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    render_p = subparsers.add_parser("render")
    render_p.add_argument("map_name")
    render_p.add_argument("output")
    
    edit_p = subparsers.add_parser("set-block")
    edit_p.add_argument("map_name")
    edit_p.add_argument("x", type=int)
    edit_p.add_argument("y", type=int)
    edit_p.add_argument("metatile")
    
    build_p = subparsers.add_parser("build")
    
    args = parser.parse_args()
    
    viz = MapVisualizer(".")
    
    if args.command == "render":
        viz.render_map(args.map_name, args.output)
    
    elif args.command == "set-block":
        # Use PoryProject logic directly
        project = viz.project
        data = project.load_map(args.map_name)
        layout_id = data["layout"]
        blocks, width, height, path = project.read_blockdata(layout_id)
        
        x, y = args.x, args.y
        if 0 <= x < width and 0 <= y < height:
            idx = y * width + x
            current = blocks[idx]
            
            # Preserve collision/elevation
            # Just update metatile ID
            new_meta = int(args.metatile, 0)
            
            new_val = (current & 0xFC00) | (new_meta & 0x3FF)
            blocks[idx] = new_val
            project.write_blockdata(path, blocks)
            print(f"Updated {args.map_name} at {x},{y} to {new_meta}")
        else:
            print("Coordinates out of bounds")
            
    elif args.command == "build":
        print("Building ROM...")
        cpu_count = os.cpu_count() or 1
        subprocess.run(["make", f"-j{cpu_count}"], check=True)
        print("Build complete.")

if __name__ == "__main__":
    main()
