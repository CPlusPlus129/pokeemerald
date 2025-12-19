#!/usr/bin/env python3
import json
import os
import struct
import map_tool

class MapBuilder:
    def __init__(self, project_root):
        self.root = project_root
        self.project = map_tool.PoryProject(project_root)

    def fill_rect(self, map_name, x1, y1, x2, y2, metatile):
        data = self.project.load_map(map_name)
        layout_id = data["layout"]
        blocks, width, height, path = self.project.read_blockdata(layout_id)
        
        for y in range(max(0, y1), min(height, y2 + 1)):
            for x in range(max(0, x1), min(width, x2 + 1)):
                idx = y * width + x
                blocks[idx] = (blocks[idx] & 0xFC00) | (metatile & 0x3FF)
        
        self.project.write_blockdata(path, blocks)

    def draw_stamp(self, map_name, x, y, stamp):
        data = self.project.load_map(map_name)
        layout_id = data["layout"]
        blocks, width, height, path = self.project.read_blockdata(layout_id)
        
        for sy, row in enumerate(stamp):
            for sx, metatile in enumerate(row):
                if metatile is None: continue
                tx, ty = x + sx, y + sy
                if 0 <= tx < width and 0 <= ty < height:
                    idx = ty * width + tx
                    blocks[idx] = (blocks[idx] & 0xFC00) | (metatile & 0x3FF)
        
        self.project.write_blockdata(path, blocks)

# --- Updated Stamps (Based on tileset reference PNGs) ---

# General Primary
GRASS = 0x001
TALL_GRASS = 0x00D
PATH_DIRT = 0x1CE # Standard path Metatile
TREE_BORDER = 0x00E # Top of tree metatile for borders

# Petalburg Secondary Stamps
# PC
PETALBURG_PC_STAMP = [
    [0x220, 0x221, 0x222, 0x223, 0x224],
    [0x228, 0x229, 0x22A, 0x22B, 0x22C],
    [0x230, 0x231, 0x232, 0x233, 0x234],
    [0x238, 0x239, 0x061, 0x23B, 0x23C]  # 0x061 is PC Door in General
]

# Mart
PETALBURG_MART_STAMP = [
    [0x240, 0x241, 0x242, 0x243, 0x244],
    [0x248, 0x249, 0x24A, 0x24B, 0x24C],
    [0x250, 0x251, 0x252, 0x253, 0x254],
    [0x258, 0x259, 0x041, 0x25B, 0x25C]  # 0x041 is Mart Door in General
]

# Small House (Brendan/May style is complicated, let's use Petalburg simple house)
PETALBURG_HOUSE_STAMP = [
    [0x208, 0x209, 0x20A, 0x20B],
    [0x210, 0x211, 0x212, 0x213],
    [0x218, 0x219, 0x021, 0x21B]  # 0x021 is standard Door
]

# Mauville Secondary Stamps
MAUVILLE_POKECENTER_STAMP = [
    [0x280, 0x281, 0x282, 0x283, 0x284],
    [0x288, 0x289, 0x28A, 0x28B, 0x28C],
    [0x290, 0x291, 0x292, 0x293, 0x294],
    [0x298, 0x299, 0x061, 0x29B, 0x29C] # 0x061 is PC Door in General
]

MAUVILLE_POKEMART_STAMP = [
    [0x2A0, 0x2A1, 0x2A2, 0x2A3, 0x2A4],
    [0x2A8, 0x2A9, 0x2AA, 0x2AB, 0x2AC],
    [0x2B0, 0x2B1, 0x2B2, 0x2B3, 0x2B4],
    [0x2B8, 0x2B9, 0x041, 0x2BB, 0x2BC] # 0x041 is Mart Door in General
]

# Mauville Gym Footprint (based on 0x260+ area in Mauville_Tileset.png)
MAUVILLE_GYM_EXT_STAMP = [
    [0x26F, 0x270, 0x271, 0x272],
    [0x277, 0x278, 0x279, 0x27A],
    [0x27F, 0x280, 0x1CD, 0x282]  # 0x1CD is Gym Door
]

def build_nexus():
    builder = MapBuilder(".")
    builder.fill_rect("NexusTown", 0, 0, 19, 19, GRASS)
    # Tree border
    builder.fill_rect("NexusTown", 0, 0, 19, 1, TREE_BORDER)
    builder.fill_rect("NexusTown", 0, 18, 19, 19, TREE_BORDER)
    builder.fill_rect("NexusTown", 0, 0, 1, 19, TREE_BORDER)
    builder.fill_rect("NexusTown", 18, 0, 19, 19, TREE_BORDER)
    
    # Path (Cross shape)
    builder.fill_rect("NexusTown", 9, 2, 10, 17, PATH_DIRT)
    builder.fill_rect("NexusTown", 2, 9, 17, 10, PATH_DIRT)
    
    # Player House
    builder.draw_stamp("NexusTown", 4, 6, PETALBURG_HOUSE_STAMP)
    # Lab (using a bigger house or PC stamp as proxy)
    builder.draw_stamp("NexusTown", 13, 6, PETALBURG_MART_STAMP)

def build_route():
    builder = MapBuilder(".")
    builder.fill_rect("BinaryRoute", 0, 0, 39, 9, GRASS)
    builder.fill_rect("BinaryRoute", 0, 4, 39, 5, PATH_DIRT)
    # Forest edges
    builder.fill_rect("BinaryRoute", 0, 0, 39, 0, TREE_BORDER)
    builder.fill_rect("BinaryRoute", 0, 9, 39, 9, TREE_BORDER)
    # Encounter zones
    builder.fill_rect("BinaryRoute", 10, 1, 20, 3, TALL_GRASS)
    builder.fill_rect("BinaryRoute", 25, 6, 35, 8, TALL_GRASS)

def build_silicon():
    builder = MapBuilder(".")
    # Pavement 0x1E0
    builder.fill_rect("SiliconCity", 0, 0, 29, 29, 0x1E0)
    # Border
    builder.fill_rect("SiliconCity", 0, 0, 29, 0, 0x1F2) # Mauville wall/border proxy
    
    # PC and Mart
    builder.draw_stamp("SiliconCity", 4, 4, MAUVILLE_POKECENTER_STAMP)
    builder.draw_stamp("SiliconCity", 20, 4, MAUVILLE_POKEMART_STAMP)
    # Gym
    builder.draw_stamp("SiliconCity", 13, 20, MAUVILLE_GYM_EXT_STAMP)

if __name__ == "__main__":
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "nexus": build_nexus()
        elif cmd == "route": build_route()
        elif cmd == "silicon": build_silicon()
        elif cmd == "all":
            build_nexus()
            build_route()
            build_silicon()
    else:
        print("Usage: map_builder.py [nexus|route|silicon|all]")