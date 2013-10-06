from collections import namedtuple

from construct import Struct, Container, Embed, Enum, MetaField
from construct import MetaArray, If, Switch, Const, Peek, Magic
from construct import OptionalGreedyRange, RepeatUntil
from construct import Flag, PascalString, Adapter
from construct import UBInt8, UBInt16, UBInt32, UBInt64
from construct import SBInt8, SBInt16, SBInt32
from construct import BFloat32, BFloat64
from construct import BitStruct, BitField
from construct import StringAdapter, LengthValueAdapter, Sequence
from construct import ConstructError

def IPacket(object):
    """
    Interface for packets.
    """

    def parse(buf, offset):
        """
        Parse a packet out of the given buffer, starting at the given offset.

        If the parse is successful, returns a tuple of the parsed packet and
        the next packet offset in the buffer.

        If the parse fails due to insufficient data, returns a tuple of None
        and the amount of data required before the parse can be retried.

        Exceptions may be raised if the parser finds invalid data.
        """

def simple(name, fmt, *args):
    """
    Make a customized namedtuple representing a simple, primitive packet.
    """

    from struct import Struct

    s = Struct(fmt)

    @classmethod
    def parse(cls, buf, offset):
        if len(buf) >= s.size + offset:
            unpacked = s.unpack_from(buf, offset)
            return cls(*unpacked), s.size + offset
        else:
            return None, s.size - len(buf)

    def build(self):
        return s.pack(*self)

    methods = {
        "parse": parse,
        "build": build,
    }

    return type(name, (namedtuple(name, *args),), methods)


DUMP_ALL_PACKETS = False

# Strings.
# This one is a UCS2 string, which effectively decodes single writeChar()
# invocations. We need to import the encoding for it first, though.
from bravo.encodings import ucs2
from codecs import register
register(ucs2)

class DoubleAdapter(LengthValueAdapter):

    def _encode(self, obj, context):
        return len(obj) / 2, obj

def AlphaString(name):
    return StringAdapter(
        DoubleAdapter(
            Sequence(name,
                UBInt16("length"),
                MetaField("data", lambda ctx: ctx["length"] * 2),
            )
        ),
        encoding="ucs2",
    )

# Boolean converter.
def Bool(*args, **kwargs):
    return Flag(*args, default=True, **kwargs)

# Flying, position, and orientation, reused in several places.
grounded = Struct("grounded", UBInt8("grounded"))
position = Struct("position",
    BFloat64("x"),
    BFloat64("y"),
    BFloat64("stance"),
    BFloat64("z")
)
orientation = Struct("orientation", BFloat32("rotation"), BFloat32("pitch"))

# TODO: this must be replaced with 'slot' (see below)
# Notchian item packing (slot data)
items = Struct("items",
    SBInt16("primary"),
    If(lambda context: context["primary"] >= 0,
        Embed(Struct("item_information",
            UBInt8("count"),
            UBInt16("secondary"),
            Magic("\xff\xff"),
        )),
    ),
)

Speed = namedtuple('speed', 'x y z')

class Slot(object):
    def __init__(self, item_id=-1, count=1, damage=0, nbt=None):
        self.item_id = item_id
        self.count = count
        self.damage = damage
        # TODO: Implement packing/unpacking of gzipped NBT data
        self.nbt = nbt

    @classmethod
    def fromItem(cls, item, count):
        return cls(item[0], count, item[1])

    @property
    def is_empty(self):
        return self.item_id == -1

    def __len__(self):
        return 0 if self.nbt is None else len(self.nbt)

    def __repr__(self):
        from bravo.blocks import items
        if self.is_empty:
            return 'Slot()'
        elif len(self):
            return 'Slot(%s, count=%d, damage=%d, +nbt:%dB)' % (
                str(items[self.item_id]), self.count, self.damage, len(self)
            )
        else:
            return 'Slot(%s, count=%d, damage=%d)' % (
                str(items[self.item_id]), self.count, self.damage
            )

    def __eq__(self, other):
        return (self.item_id == other.item_id and
                self.count == other.count and
                self.damage == self.damage and
                self.nbt == self.nbt)

class SlotAdapter(Adapter):

    def _decode(self, obj, context):
        if obj.item_id == -1:
            s = Slot(obj.item_id)
        else:
            s = Slot(obj.item_id, obj.count, obj.damage, obj.nbt)
        return s

    def _encode(self, obj, context):
        if not isinstance(obj, Slot):
            raise ConstructError('Slot object expected')
        if obj.is_empty:
            return Container(item_id=-1)
        else:
            return Container(item_id=obj.item_id, count=obj.count, damage=obj.damage,
                             nbt_len=len(obj) if len(obj) else -1, nbt=obj.nbt)

slot = SlotAdapter(
    Struct("slot",
        SBInt16("item_id"),
        If(lambda context: context["item_id"] >= 0,
            Embed(Struct("item_information",
                UBInt8("count"),
                UBInt16("damage"),
                SBInt16("nbt_len"),
                If(lambda context: context["nbt_len"] >= 0,
                    MetaField("nbt", lambda ctx: ctx["nbt_len"])
                )
            )),
        )
    )
)


Metadata = namedtuple("Metadata", "type value")
metadata_types = ["byte", "short", "int", "float", "string", "slot", "coords"]

# Metadata adaptor.
class MetadataAdapter(Adapter):

    def _decode(self, obj, context):
        d = {}
        for m in obj.data:
            d[m.id.key] = Metadata(metadata_types[m.id.type], m.value)
        return d

    def _encode(self, obj, context):
        c = Container(data=[], terminator=None)
        for k, v in obj.iteritems():
            t, value = v
            d = Container(
                id=Container(type=metadata_types.index(t), key=k),
                value=value,
                peeked=None)
            c.data.append(d)
        if c.data:
            c.data[-1].peeked = 127
        else:
            c.data.append(Container(id=Container(first=0, second=0), value=0,
                peeked=127))
        return c

# Metadata inner container.
metadata_switch = {
    0: UBInt8("value"),
    1: UBInt16("value"),
    2: UBInt32("value"),
    3: BFloat32("value"),
    4: AlphaString("value"),
    5: slot,
    6: Struct("coords",
        UBInt32("x"),
        UBInt32("y"),
        UBInt32("z"),
    ),
}

# Metadata subconstruct.
metadata = MetadataAdapter(
    Struct("metadata",
        RepeatUntil(lambda obj, context: obj["peeked"] == 0x7f,
            Struct("data",
                BitStruct("id",
                    BitField("type", 3),
                    BitField("key", 5),
                ),
                Switch("value", lambda context: context["id"]["type"],
                    metadata_switch),
                Peek(UBInt8("peeked")),
            ),
        ),
        Const(UBInt8("terminator"), 0x7f),
    ),
)

# Build faces, used during dig and build.
faces = {
    "noop": -1,
    "-y": 0,
    "+y": 1,
    "-z": 2,
    "+z": 3,
    "-x": 4,
    "+x": 5,
}
face = Enum(SBInt8("face"), **faces)

# World dimension.
dimensions = {
    "earth": 0,
    "sky": 1,
    "nether": 255,
}
dimension = Enum(UBInt8("dimension"), **dimensions)

# Difficulty levels
difficulties = {
    "peaceful": 0,
    "easy": 1,
    "normal": 2,
    "hard": 3,
}
difficulty = Enum(UBInt8("difficulty"), **difficulties)

modes = {
    "survival": 0,
    "creative": 1,
    "adventure": 2,
}
mode = Enum(UBInt8("mode"), **modes)

# Possible effects.
# XXX these names aren't really canonized yet
effect = Enum(UBInt8("effect"),
    move_fast=1,
    move_slow=2,
    dig_fast=3,
    dig_slow=4,
    damage_boost=5,
    heal=6,
    harm=7,
    jump=8,
    confusion=9,
    regenerate=10,
    resistance=11,
    fire_resistance=12,
    water_resistance=13,
    invisibility=14,
    blindness=15,
    night_vision=16,
    hunger=17,
    weakness=18,
    poison=19,
    wither=20,
)

# The actual packet list.
packets = {
    0x00: Struct("ping",
        UBInt32("pid"),
    ),
    0x01: Struct("login",
        # Player Entity ID (random number generated by the server)
        UBInt32("eid"),
        # default, flat, largeBiomes
        AlphaString("leveltype"),
        mode,
        dimension,
        difficulty,
        UBInt8("unused"),
        UBInt8("maxplayers"),
    ),
    0x02: Struct("handshake",
        UBInt8("protocol"),
        AlphaString("username"),
        AlphaString("host"),
        UBInt32("port"),
    ),
    0x03: Struct("chat",
        AlphaString("message"),
    ),
    0x04: Struct("time",
        # Total Ticks
        UBInt64("timestamp"),
        # Time of day
        UBInt64("time"),
    ),
    0x05: Struct("entity-equipment",
        UBInt32("eid"),
        UBInt16("slot"),
        Embed(items),
    ),
    0x06: Struct("spawn",
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    0x07: Struct("use",
        UBInt32("eid"),
        UBInt32("target"),
        UBInt8("button"),
    ),
    0x08: Struct("health",
        BFloat32("hp"),
        UBInt16("fp"),
        BFloat32("saturation"),
    ),
    0x09: Struct("respawn",
        dimension,
        difficulty,
        mode,
        UBInt16("height"),
        AlphaString("leveltype"),
    ),
    0x0a: grounded,
    0x0b: Struct("position",
        position,
        grounded
    ),
    0x0c: Struct("orientation",
        orientation,
        grounded
    ),
    # TODO: Differ between client and server 'position'
    0x0d: Struct("location",
        position,
        orientation,
        grounded
    ),
    0x0e: Struct("digging",
        Enum(UBInt8("state"),
            started=0,
            cancelled=1,
            stopped=2,
            checked=3,
            dropped=4,
            # Also eating
            shooting=5,
        ),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        face,
    ),
    0x0f: Struct("build",
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        face,
        Embed(items),
        UBInt8("cursorx"),
        UBInt8("cursory"),
        UBInt8("cursorz"),
    ),
    # Hold Item Change
    0x10: Struct("equip",
        # Only 0-8
        UBInt16("slot"),
    ),
    0x11: Struct("bed",
        UBInt32("eid"),
        UBInt8("unknown"),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
    ),
    0x12: Struct("animate",
        UBInt32("eid"),
        Enum(UBInt8("animation"),
            noop=0,
            arm=1,
            hit=2,
            leave_bed=3,
            eat=5,
            unknown=102,
            crouch=104,
            uncrouch=105,
        ),
    ),
    0x13: Struct("action",
        UBInt32("eid"),
        Enum(UBInt8("action"),
            crouch=1,
            uncrouch=2,
            leave_bed=3,
            start_sprint=4,
            stop_sprint=5,
        ),
        UBInt32("unknown"),
    ),
    0x14: Struct("player",
        UBInt32("eid"),
        AlphaString("username"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
        # 0 For none, unlike other packets
        # -1 crashes clients
        SBInt16("item"),
        metadata,
    ),
    0x16: Struct("collect",
        UBInt32("eid"),
        UBInt32("destination"),
    ),
    # Object/Vehicle
    0x17: Struct("object",  # XXX: was 'vehicle'!
        UBInt32("eid"),
        Enum(UBInt8("type"),  # See http://wiki.vg/Entities#Objects
            boat=1,
            item_stack=2,
            minecart=10,
            storage_cart=11,
            powered_cart=12,
            tnt=50,
            ender_crystal=51,
            arrow=60,
            snowball=61,
            egg=62,
            thrown_enderpearl=65,
            wither_skull=66,
            falling_block=70,
            frames=71,
            ender_eye=72,
            thrown_potion=73,
            dragon_egg=74,
            thrown_xp_bottle=75,
            fishing_float=90,
        ),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("pitch"),
        UBInt8("yaw"),
        SBInt32("data"),  # See http://www.wiki.vg/Object_Data
        If(lambda context: context["data"] != 0,
            Struct("speed",
                SBInt16("x"),
                SBInt16("y"),
                SBInt16("z"),
            )
        ),
    ),
    0x18: Struct("mob",
        UBInt32("eid"),
        Enum(UBInt8("type"), **{
            "Creeper": 50,
            "Skeleton": 51,
            "Spider": 52,
            "GiantZombie": 53,
            "Zombie": 54,
            "Slime": 55,
            "Ghast": 56,
            "ZombiePig": 57,
            "Enderman": 58,
            "CaveSpider": 59,
            "Silverfish": 60,
            "Blaze": 61,
            "MagmaCube": 62,
            "EnderDragon": 63,
            "Wither": 64,
            "Bat": 65,
            "Witch": 66,
            "Pig": 90,
            "Sheep": 91,
            "Cow": 92,
            "Chicken": 93,
            "Squid": 94,
            "Wolf": 95,
            "Mooshroom": 96,
            "Snowman": 97,
            "Ocelot": 98,
            "IronGolem": 99,
            "Villager": 120
        }),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        SBInt8("yaw"),
        SBInt8("pitch"),
        SBInt8("head_yaw"),
        SBInt16("vx"),
        SBInt16("vy"),
        SBInt16("vz"),
        metadata,
    ),
    0x19: Struct("painting",
        UBInt32("eid"),
        AlphaString("title"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        face,
    ),
    0x1a: Struct("experience",
        UBInt32("eid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt16("quantity"),
    ),
    0x1b: Struct("steer",
        BFloat32("first"),
        BFloat32("second"),
        Bool("third"),
        Bool("fourth"),
    ),
    0x1c: Struct("velocity",
        UBInt32("eid"),
        SBInt16("dx"),
        SBInt16("dy"),
        SBInt16("dz"),
    ),
    0x1d: Struct("destroy",
        UBInt8("count"),
        MetaArray(lambda context: context["count"], UBInt32("eid")),
    ),
    0x1e: Struct("create",
        UBInt32("eid"),
    ),
    0x1f: Struct("entity-position",
        UBInt32("eid"),
        SBInt8("dx"),
        SBInt8("dy"),
        SBInt8("dz")
    ),
    0x20: Struct("entity-orientation",
        UBInt32("eid"),
        UBInt8("yaw"),
        UBInt8("pitch")
    ),
    0x21: Struct("entity-location",
        UBInt32("eid"),
        SBInt8("dx"),
        SBInt8("dy"),
        SBInt8("dz"),
        UBInt8("yaw"),
        UBInt8("pitch")
    ),
    0x22: Struct("teleport",
        UBInt32("eid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
        UBInt8("yaw"),
        UBInt8("pitch"),
    ),
    0x23: Struct("entity-head",
        UBInt32("eid"),
        UBInt8("yaw"),
    ),
    0x26: Struct("status",
        UBInt32("eid"),
        Enum(UBInt8("status"),
            damaged=2,
            killed=3,
            taming=6,
            tamed=7,
            drying=8,
            eating=9,
            sheep_eat=10,
            golem_rose=11,
            heart_particle=12,
            angry_particle=13,
            happy_particle=14,
            magic_particle=15,
            shaking=16,
            firework=17,
        ),
    ),
    0x27: Struct("attach",
        UBInt32("eid"),
        # XXX -1 for detatching
        UBInt32("vid"),
        UBInt8("unknown"),
    ),
    0x28: Struct("metadata",
        UBInt32("eid"),
        metadata,
    ),
    0x29: Struct("effect",
        UBInt32("eid"),
        effect,
        UBInt8("amount"),
        UBInt16("duration"),
    ),
    0x2a: Struct("uneffect",
        UBInt32("eid"),
        effect,
    ),
    0x2b: Struct("levelup",
        BFloat32("current"),
        UBInt16("level"),
        UBInt16("total"),
    ),
    # XXX 0x2c, server to client, needs to be implemented, needs special
    # UUID-packing techniques
    0x33: Struct("chunk",
        SBInt32("x"),
        SBInt32("z"),
        Bool("continuous"),
        UBInt16("primary"),
        UBInt16("add"),
        PascalString("data", length_field=UBInt32("length"), encoding="zlib"),
    ),
    0x34: Struct("batch",
        SBInt32("x"),
        SBInt32("z"),
        UBInt16("count"),
        PascalString("data", length_field=UBInt32("length")),
    ),
    0x35: Struct("block",
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt16("type"),
        UBInt8("meta"),
    ),
    # XXX This covers general tile actions, not just note blocks.
    # TODO: Needs work
    0x36: Struct("block-action",
        SBInt32("x"),
        SBInt16("y"),
        SBInt32("z"),
        UBInt8("byte1"),
        UBInt8("byte2"),
        UBInt16("blockid"),
    ),
    0x37: Struct("block-break-anim",
        UBInt32("eid"),
        UBInt32("x"),
        UBInt32("y"),
        UBInt32("z"),
        UBInt8("stage"),
    ),
    # XXX Server -> Client. Use 0x33 instead.
    0x38: Struct("bulk-chunk",
        UBInt16("count"),
        UBInt32("length"),
        UBInt8("sky_light"),
        MetaField("data", lambda ctx: ctx["length"]),
        MetaArray(lambda context: context["count"],
            Struct("metadata",
                UBInt32("chunk_x"),
                UBInt32("chunk_z"),
                UBInt16("bitmap_primary"),
                UBInt16("bitmap_secondary"),
            )
        )
    ),
    # TODO: Needs work?
    0x3c: Struct("explosion",
        BFloat64("x"),
        BFloat64("y"),
        BFloat64("z"),
        BFloat32("radius"),
        UBInt32("count"),
        MetaField("blocks", lambda context: context["count"] * 3),
        BFloat32("motionx"),
        BFloat32("motiony"),
        BFloat32("motionz"),
    ),
    0x3d: Struct("sound",
        Enum(UBInt32("sid"),
            click2=1000,
            click1=1001,
            bow_fire=1002,
            door_toggle=1003,
            extinguish=1004,
            record_play=1005,
            charge=1007,
            fireball=1008,
            zombie_wood=1010,
            zombie_metal=1011,
            zombie_break=1012,
            wither=1013,
            smoke=2000,
            block_break=2001,
            splash_potion=2002,
            ender_eye=2003,
            blaze=2004,
        ),
        SBInt32("x"),
        UBInt8("y"),
        SBInt32("z"),
        UBInt32("data"),
        Bool("volume-mod"),
    ),
    0x3e: Struct("named-sound",
        AlphaString("name"),
        UBInt32("x"),
        UBInt32("y"),
        UBInt32("z"),
        BFloat32("volume"),
        UBInt8("pitch"),
    ),
    0x3f: Struct("particle",
        AlphaString("name"),
        BFloat32("x"),
        BFloat32("y"),
        BFloat32("z"),
        BFloat32("x_offset"),
        BFloat32("y_offset"),
        BFloat32("z_offset"),
        BFloat32("speed"),
        UBInt32("count"),
    ),
    0x46: Struct("state",
        Enum(UBInt8("state"),
            bad_bed=0,
            start_rain=1,
            stop_rain=2,
            mode_change=3,
            run_credits=4,
        ),
        mode,
    ),
    0x47: Struct("thunderbolt",
        UBInt32("eid"),
        UBInt8("gid"),
        SBInt32("x"),
        SBInt32("y"),
        SBInt32("z"),
    ),
    0x64: Struct("window-open",
        UBInt8("wid"),
        Enum(UBInt8("type"),
            chest=0,
            workbench=1,
            furnace=2,
            dispenser=3,
            enchatment_table=4,
            brewing_stand=5,
            npc_trade=6,
            beacon=7,
            anvil=8,
            hopper=9,
        ),
        AlphaString("title"),
        UBInt8("slots"),
        UBInt8("use_title"),
        # XXX iff type == 0xb (currently unknown) write an extra secret int
        # here. WTF?
    ),
    0x65: Struct("window-close",
        UBInt8("wid"),
    ),
    0x66: Struct("window-action",
        UBInt8("wid"),
        UBInt16("slot"),
        UBInt8("button"),
        UBInt16("token"),
        UBInt8("shift"),  # TODO: rename to 'mode'
        Embed(items),
    ),
    0x67: Struct("window-slot",
        UBInt8("wid"),
        UBInt16("slot"),
        Embed(items),
    ),
    0x68: Struct("inventory",
        UBInt8("wid"),
        UBInt16("length"),
        MetaArray(lambda context: context["length"], items),
    ),
    0x69: Struct("window-progress",
        UBInt8("wid"),
        UBInt16("bar"),
        UBInt16("progress"),
    ),
    0x6a: Struct("window-token",
        UBInt8("wid"),
        UBInt16("token"),
        Bool("acknowledged"),
    ),
    0x6b: Struct("window-creative",
        UBInt16("slot"),
        Embed(items),
    ),
    0x6c: Struct("enchant",
        UBInt8("wid"),
        UBInt8("enchantment"),
    ),
    0x82: Struct("sign",
        SBInt32("x"),
        UBInt16("y"),
        SBInt32("z"),
        AlphaString("line1"),
        AlphaString("line2"),
        AlphaString("line3"),
        AlphaString("line4"),
    ),
    0x83: Struct("map",
        UBInt16("type"),
        UBInt16("itemid"),
        PascalString("data", length_field=UBInt16("length")),
    ),
    0x84: Struct("tile-update",
        SBInt32("x"),
        UBInt16("y"),
        SBInt32("z"),
        UBInt8("action"),
        PascalString("nbt_data", length_field=UBInt16("length")),  # gzipped
    ),
    0x85: Struct("0x85",
        UBInt8("first"),
        UBInt32("second"),
        UBInt32("third"),
        UBInt32("fourth"),
    ),
    0xc8: Struct("statistics",
        UBInt32("sid"), # XXX I should be an Enum!
        UBInt32("count"),
    ),
    0xc9: Struct("players",
        AlphaString("name"),
        Bool("online"),
        UBInt16("ping"),
    ),
    0xca: Struct("abilities",
        UBInt8("flags"),
        BFloat32("fly-speed"),
        BFloat32("walk-speed"),
    ),
    0xcb: Struct("tab",
        AlphaString("autocomplete"),
    ),
    0xcc: Struct("settings",
        AlphaString("locale"),
        UBInt8("distance"),
        UBInt8("chat"),
        difficulty,
        Bool("cape"),
    ),
    0xcd: Struct("statuses",
        UBInt8("payload")
    ),
    0xce: Struct("score_item",
        AlphaString("name"),
        AlphaString("value"),
        Enum(UBInt8("action"),
            create=0,
            remove=1,
            update=2,
        ),
    ),
    0xcf: Struct("score_update",
        AlphaString("item_name"),
        UBInt8("remove"),
        If(lambda context: context["remove"] == 0,
            Embed(Struct("information",
                AlphaString("score_name"),
                UBInt32("value"),
            ))
        ),
    ),
    0xd0: Struct("score_display",
        Enum(UBInt8("position"),
            as_list=0,
            sidebar=1,
            below_name=2,
        ),
        AlphaString("score_name"),
    ),
    0xd1: Struct("teams",
        AlphaString("name"),
        Enum(UBInt8("mode"),
            team_created=0,
            team_removed=1,
            team_updates=2,
            players_added=3,
            players_removed=4,
        ),
        If(lambda context: context["mode"] in ("team_created", "team_updated"),
            Embed(Struct("team_info",
                AlphaString("team_name"),
                AlphaString("team_prefix"),
                AlphaString("team_suffix"),
                Enum(UBInt8("friendly_fire"),
                    off=0,
                    on=1,
                    invisibles=2,
                ),
            ))
        ),
        If(lambda context: context["mode"] in ("team_created", "players_added", "players_removed"),
            Embed(Struct("players_info",
                UBInt16("count"),
                MetaArray(lambda context: context["count"], AlphaString("player_names")),
            ))
        ),
    ),
    0xfa: Struct("plugin-message",
        AlphaString("channel"),
        PascalString("data", length_field=UBInt16("length")),
    ),
    0xfc: Struct("key-response",
        PascalString("key", length_field=UBInt16("key-len")),
        PascalString("token", length_field=UBInt16("token-len")),
    ),
    0xfd: Struct("key-request",
        AlphaString("server"),
        PascalString("key", length_field=UBInt16("key-len")),
        PascalString("token", length_field=UBInt16("token-len")),
    ),
    0xfe: Struct("poll",
        Magic("\x01" # Poll packet constant
              "\xfa" # Followed by a plugin message
              "\x00\x0b" # Length of plugin channel name
              + u"MC|PingHost".encode("ucs2") # Plugin channel name
        ),
        PascalString("data", length_field=UBInt16("length")),
    ),
    # TODO: rename to 'kick'
    0xff: Struct("error", AlphaString("message")),
}

packet_stream = Struct("packet_stream",
    OptionalGreedyRange(
        Struct("full_packet",
            UBInt8("header"),
            Switch("payload", lambda context: context["header"], packets),
        ),
    ),
    OptionalGreedyRange(
        UBInt8("leftovers"),
    ),
)

def parse_packets(bytestream):
    """
    Opportunistically parse out as many packets as possible from a raw
    bytestream.

    Returns a tuple containing a list of unpacked packet containers, and any
    leftover unparseable bytes.
    """

    container = packet_stream.parse(bytestream)

    l = [(i.header, i.payload) for i in container.full_packet]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if DUMP_ALL_PACKETS:
        for header, payload in l:
            print "Parsed packet 0x%.2x" % header
            print payload

    return l, leftovers

incremental_packet_stream = Struct("incremental_packet_stream",
    Struct("full_packet",
        UBInt8("header"),
        Switch("payload", lambda context: context["header"], packets),
    ),
    OptionalGreedyRange(
        UBInt8("leftovers"),
    ),
)

def parse_packets_incrementally(bytestream):
    """
    Parse out packets one-by-one, yielding a tuple of packet header and packet
    payload.

    This function returns a generator.

    This function will yield all valid packets in the bytestream up to the
    first invalid packet.

    :returns: a generator yielding tuples of headers and payloads
    """

    while bytestream:
        parsed = incremental_packet_stream.parse(bytestream)
        header = parsed.full_packet.header
        payload = parsed.full_packet.payload
        bytestream = "".join(chr(i) for i in parsed.leftovers)

        yield header, payload

packets_by_name = dict((v.name, k) for (k, v) in packets.iteritems())

def make_packet(packet, *args, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments. Additional containers
    or dictionaries to be added to the payload may be passed positionally, as
    well.
    """

    if packet not in packets_by_name:
        print "Couldn't find packet name %s!" % packet
        return ""

    header = packets_by_name[packet]

    for arg in args:
        kwargs.update(dict(arg))
    container = Container(**kwargs)

    if DUMP_ALL_PACKETS:
        print "Making packet <%s> (0x%.2x)" % (packet, header)
        print container
    payload = packets[header].build(container)
    return chr(header) + payload

def make_error_packet(message):
    """
    Convenience method to generate an error packet bytestream.
    """

    return make_packet("error", message=message)
