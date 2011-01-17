from itertools import chain

from numpy import array, uint8

try:
    from json import load, dump
except ImportError:
    try:
        from simplejson import load, dump
    except ImportError:
        raise ImportError("Couldn't find a JSON library!")

class InventorySerializer(object):

    def load_from_tag(inventory, l):

        items = [None] * len(inventory)

        for item in l:
            slot = item["Slot"]
            items[slot] = item["id"], item["Damage"], item["Count"]

        inventory.load_from_list(items)

    def save_to_tag(inventory):

        l = []

        for i, item in enumerate(chain(inventory.crafted,
            inventory.crafting, inventory.armor, inventory.storage,
            inventory.holdables)):
            if item is not None:
                id, damage, count = item
                d = {
                    "id": id,
                    "Damage": damage,
                    "Count": count,
                    "Slot": i,
                }
                l.append(d)

        return l

class ChestSerializer(object):

    def load_from_tag(chest, d):

        chest.x = d["x"]
        chest.y = d["y"]
        chest.z = d["z"]

        chest.inventory.load_from_tag(d["Items"])

    def save_to_tag(chest):

        d = {
            "id": "Chest",
            "x": chest.x,
            "y": chest.y,
            "z": chest.z,
            "Items": chest.inventory.save_to_tag(),
        }

        return d

class SignSerializer(object):

    def load_from_tag(sign, d):

        sign.x = d["x"]
        sign.y = d["y"]
        sign.z = d["z"]

        sign.text1 = d["Text1"]
        sign.text2 = d["Text2"]
        sign.text3 = d["Text3"]
        sign.text4 = d["Text4"]

    def save_to_tag(sign):

        d = {
            "id": "Sign",
            "x": sign.x,
            "y": sign.y,
            "z": sign.z,
            "Text1": sign.text1,
            "Text2": sign.text2,
            "Text3": sign.text3,
            "Text4": sign.text4,
        }

        return d

class ChunkSerializer(object):

    def load_from_tag(chunk, d):

        level = d["Level"]

        chunk.blocks = array(level["Blocks"],
            dtype=uint8).reshape(chunk.blocks.shape)
        chunk.heightmap = array(level["HeightMap"],
            dtype=uint8).reshape(chunk.heightmap.shape)
        chunk.blocklight = array(level["BlockLight"],
            dtype=uint8).reshape(chunk.blocklight.shape)
        chunk.metadata = array(level["Data"],
            dtype=uint8).reshape(chunk.metadata.shape)
        chunk.skylight = array(level["SkyLight"],
            dtype=uint8).reshape(chunk.skylight.shape)

        chunk.populated = level["TerrainPopulated"]

        if "TileEntities" in level:
            for t in level["TileEntities"]:
                try:
                    tile = chunk.known_tile_entities[t["id"]]()
                    tile.load_from_tag(t)
                    chunk.tiles[tile.x, tile.y, tile.z] = tile
                except:
                    print "Unknown tile entity %s" % t["id"]

        chunk.dirty = not chunk.populated

    def save_to_tag(chunk):

        d = {
            "Level": {
                "Blocks": chunk.blocks.ravel().tolist(),
                "HeightMap": chunk.heightmap.ravel().tolist(),
                "BlockLight": chunk.blocklight.ravel().tolist(),
                "Data": chunk.metadata.ravel().tolist(),
                "SkyLight": chunk.skylight.ravel().tolist(),
                "TerrainPopulated": chunk.populated,
                "TileEntities": [tile.save_to_tag()
                    for tile in chunk.tiles.itervalues()
                ],
            }
        }

        return d

class LevelSerializer(object):

    def load_from_tag(level, d):

        level.spawn = (d["Data"]["SpawnX"],
            d["Data"]["SpawnY"],
            d["Data"]["SpawnZ"])

        level.seed = d["Data"]["RandomSeed"]

    def save_to_tag(level):

        d = {
            "Data": {
                "RandomSeed": level.seed,
                "SpawnX": level.spawn[0],
                "SpawnY": level.spawn[1],
                "SpawnZ": level.spawn[2],
            }
        }

        return d

class PlayerSerializer(object):

    def load_from_tag(player, d):

        player.location.x, player.location.y, player.location.z = d["Pos"]

        player.location.yaw, player.location.pitch = d["Rotation"]

        if "Inventory" in d:
            player.inventory.load_from_tag(d["Inventory"])

    def save_to_tag(player):

        d = {
            "Pos": (player.location.x, player.location.y, player.location.z),
            "Rotation": (player.location.yaw, player.location.pitch),
            "Inventory": player.inventory.save_to_tag(),
        }

        return d

def read_from_file(f):

    return load(f)

def write_to_file(d, f):

    dump(d, f)

def extension():

    return ".json"
