# vim: set fileencoding=utf8 :

from itertools import product, chain
import json
from time import time
from urlparse import urlunparse

from twisted.internet import reactor
from twisted.internet.defer import (DeferredList, inlineCallbacks,
                                    maybeDeferred, succeed)
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.task import cooperate, deferLater, LoopingCall
from twisted.internet.task import TaskDone, TaskFailed
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log
from twisted.web.client import getPage

from bravo import version
from bravo.beta.structures import BuildData, Settings, Slot
from bravo.blocks import blocks, items
from bravo.chunk import CHUNK_HEIGHT
from bravo.entity import Sign
from bravo.errors import BetaClientError, BuildError
from bravo.ibravo import (IChatCommand, IPreBuildHook, IPostBuildHook,
                          IWindowOpenHook, IWindowClickHook, IWindowCloseHook,
                          IPreDigHook, IDigHook, ISignHook, IUseHook)
from bravo.infini.factory import InfiniClientFactory
from bravo.inventory.windows import InventoryWindow
from bravo.location import Location, Orientation, Position
from bravo.motd import get_motd
from bravo.beta.packets import parse_packets, make_packet
from bravo.plugin import retrieve_plugins
from bravo.policy.dig import dig_policies
from bravo.utilities.coords import adjust_coords_for_face, split_coords
from bravo.utilities.chat import complete, username_alternatives
from bravo.utilities.maths import circling, clamp, sorted_by_distance
from bravo.utilities.temporal import timestamp_from_clock

from uuid import uuid4

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
from varint import VarInt

# States of the protocol.
(STATE_UNAUTHENTICATED, STATE_AUTHENTICATED, STATE_LOCATED) = range(3)

SUPPORTED_PROTOCOL = 4


# Data structures required for the beta protocol.
def AlphaString(name):
    return PascalString(name, length_field=VarInt('length'))


def Bool(*args, **kwargs):
    return Flag(*args, default=True, **kwargs)


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
                           SBInt8("count"),
                           SBInt16("damage"),
                           SBInt16("nbt_len"),
                           If(lambda context: context["nbt_len"] >= 0,
                              MetaField("nbt", lambda ctx: ctx["nbt_len"])
                              )
                           )),
              )
           )
)


Metadata = namedtuple("Metadata", "type value")
# JMT: merge metadata_types with metadata_switch
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
    1: SBInt16("value"),
    2: SBInt32("value"),
    3: BFloat32("value"),
    4: PascalString("value"),
    5: slot,
    6: Struct("coords",
              SBInt32("x"),
              SBInt32("y"),
              SBInt32("z"),
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

# Enums.
mobtypes = {
    50: 'Creeper',
    51: 'Skeleton',
    52: 'Spider',
    53: 'Giant Zombie',
    54: 'Zombie',
    55: 'Slime',
    56: 'Ghast',
    57: 'Zombie Pigman',
    58: 'Enderman',
    59: 'Cave Spider',
    60: 'Silverfish',
    61: 'Blaze',
    62: 'Magma Cube',
    63: 'Ender Dragon',
    64: 'Wither',
    65: 'Bat',
    66: 'Witch',
    90: 'Pig',
    91: 'Sheep',
    92: 'Cow',
    93: 'Chicken',
    94: 'Squid',
    95: 'Wolf',
    96: 'Mooshroom',
    97: 'Snowman',
    98: 'Ocelot',
    99: 'Iron Golem',
    100: 'Horse',
    120: 'Villager',
}

objecttypes = {
    1: 'Boat',
    2: 'Item Stack (Slot)',
    10: 'Minecart',
    11: 'Minecart (storage)',
    12: 'Minecart (powered)',
    50: 'Activated TNT',
    51: 'EnderCrystal',
    60: 'Arrow (projectile)',
    61: 'Snowball (projectile)',
    62: 'Egg (projectile)',
    63: 'FireBall (ghast projectile)',
    64: 'FireCharge (blaze projectile)',
    65: 'Thrown Enderpearl',
    66: 'Wither Skull (projectile)',
    70: 'Falling Objects',
    71: 'Item frames',
    72: 'Eye of Ender',
    73: 'Thrown Potion',
    74: 'Falling Dragon Egg',
    75: 'Thrown Exp Bottle',
    90: 'Fishing Float',
}

clientanimationtypes = {
    0: 'Swing arm',
    1: 'Damage animation',
    2: 'Leave bed',
    3: 'Eat food',
    4: 'Critical effect',
    5: 'Magic critical effect',
    102: '(unknown)',
    104: 'Crouch',
    105: 'Uncrouch',
}

entitystatustypes = {
    2: 'Entity hurt',
    3: 'Entity dead',
    6: 'Wolf taming',
    7: 'Wolf tamed',
    8: 'Wolf shaking water off itself',
    9: '(of self) Eating accepted by server',
    10: 'Sheep eating grass',
    11: 'Iron Golem handing over a rose',
    12: 'Spawn "heart" particles near a villager',
    13: 'Spawn particles indicating that a villager is angry and seeking revenge',
    14: 'Spawn happy particles near a villager',
    15: 'Spawn a "magic" particle near the Witch',
    16: 'Zombie converting into a villager by shaking violently (unused in recent update)',
    17: 'A firework exploding',
}

effecttypes = {
    1000: 'random.click',
    1001: 'random.click',
    1002: 'random.bow',
    1003: 'random.door_open or random.door_close (50/50 chance)',
    1004: 'random.fizz',
    1005: 'Play a music disc.',  # Data: Record ID
    1007: 'mob.ghast.charge',
    1008: 'mob.ghast.fireball',
    1009: 'mob.ghast.fireball, but with a lower volume.',
    1010: 'mob.zombie.wood',
    1011: 'mob.zombie.metal',
    1012: 'mob.zombie.woodbreak',
    1013: 'mob.wither.spawn',
    1014: 'mob.wither.shoot',
    1015: 'mob.bat.takeoff',
    1016: 'mob.zombie.infect',
    1017: 'mob.zombie.unfect',
    1018: 'mob.enderdragon.end',
    1020: 'random.anvil_break',
    1021: 'random.anvil_use',
    1022: 'random.anvil_land',
    2000: 'Spawns 10 smoke particles, e.g. from a fire.',  # Data: smoke direction
    2001: 'Block break.',  # Data: Block ID
    2002: 'Splash potion. Particle effect + glass break sound.',  # Data: Potion ID
    2003: 'Eye of ender entity break animation - particles and sound',
    2004: 'Mob spawn particle effect: smoke + flames',
    2005: 'Spawn "happy villager" effect (hearts).',
}

smokedirectiontypes = {
    0: 'Southeast',
    1: 'South',
    2: 'Southwest',
    3: 'East',
    4: 'Up',
    5: 'West',
    6: 'Northeast',
    7: 'North',
    8: 'Northwest',
}

reasontypes = {
    0: 'Invalid Bed',  # "tile.bed.notValid"
    1: 'End raining',
    2: 'Begin raining',
    3: 'Change game mode',  # "gameMode.changed" 0 - Survival, 1 - Creative, 2 - Adventure
    4: 'Enter credits',
    5: 'Demo messages',  # 0 - Show welcome to demo screen, 101 - Tell movement controls, 102 - Tell jump control, 103 - Tell inventory control
    6: 'Arrow hitting player',  # Appears to be played when an arrow strikes another player in Multiplayer
    7: 'Fade value',  # The current darkness value. 1 = Dark, 0 = Bright, Setting the value higher causes the game to change color and freeze
    8: 'Fade time',  # Time in ticks for the sky to fade
}

# Old enums.
faces = {
    'noop': -1,
    '-y': 0,
    '+y': 1,
    '-z': 2,
    '+z': 3,
    '-x': 4,
    '+x': 5,
}

face_enum = Enum(SBInt8('face'), **faces)

dimensions = {
    'earth': 0,
    'sky': 1,
    'nether': -1,
}

dimension_enum = Enum(SBInt8('dimension'), **dimensions)

difficulties = {
    'peaceful': 0,
    'easy': 1,
    'normal': 2,
    'hard': 3,
}

difficulty_enum = Enum(UBInt8('difficulty'), **difficulties)

modes = {
    'survival': 0,
    'creative': 1,
    'adventure': 2,
}

mode_enum = Enum(UBInt8('mode'), **modes)

# Packet-specific enums.
handshaking_state = {
    'status': 1,
    'login': 2,
}

handshaking_state_enum = Enum(VarInt('next_state'), **handshaking_state)

mouse = {
    'left': 0,
    'right': 1,
}

mouse_enum = Enum(UBInt8('mouse'), **mouse)

player_digging_status = {
    'started': 0,
    'cancelled': 1,
    'stopped': 2,
    'dropped_stack': 3,  # New!
    'dropped': 4,
    'shooting': 5,  # Also eating
}

player_digging_status_enum = Enum(UBInt8('state'), **player_digging_status)

server_animation = {
    'noop': 0,
    'arm': 1,
    'hit': 2,
    'leave_bed': 3,
    # XXX FIX ME
    'eat': 5,
    'critical': 6,  # New!
    'magic_critical': 7,  # New!
    'unknown': 102,
    'crouch': 104,
    'uncrouch': 105,
}

server_animation_enum = Enum(UBInt8('animation'), **server_animation)

entity_action = {
    'crouch': 1,
    'uncrouch': 2,
    'leave_bed': 3,
    'start_sprint': 4,
    'stop_sprint': 5,
}

entity_action_enum = Enum(UBInt8('action'), **entity_action)

client_status = {
    'respawn': 0,
    'stats': 1,
    'open_inventory_achievement': 2,
}

client_status_enum = Enum(UBInt8('status'), **client_status)

game_state = {
    'bad_bed': 0,
    'start_rain': 1,
    'stop_rain': 2,
    'mode_change': 3,
    'run_credits': 4,
    'demo-messages': 5,  # New!
    'arrow_hits_player': 6,  # New!
    'fade_value': 7,  # New!
    'fade_time': 8,  # New!
}

game_state_enum = Enum(UBInt8('reason'), **game_state)

# Commonly-occurring packet elements.
grounded = Struct("grounded",
                  UBInt8("grounded"),  # Bool('on_ground')
                  )
position = Struct("position",
                  BFloat64("x"),
                  BFloat64("y"),
                  BFloat64("stance"),
                  BFloat64("z")
                  )
orientation = Struct("orientation",
                     BFloat32("rotation"),  # BFloat32('yaw')
                     BFloat32("pitch"),
                     )
# JMT: try adding these
block_target = Struct('block_target',
                      SBInt32('x'),
                      UBInt8('y'),
                      SBInt32('z'),
                      )

# Packets.
serverbound = {
    'handshaking': {
        0x00: Struct('handshaking',
                     VarInt('protocol'),
                     AlphaString('name'),
                     UBInt16('port'),
                     # VarInt('next_state'),
                     handshaking_state_enum,
                     ),
        0x01: Struct('encryption_response',
                     SBInt16('key_len'),
                     MetaField('key', lambda ctx: ctx['key_len']),
                     SBInt16('token_len'),
                     MetaField('token', lambda ctx: ctx['token_len']),
                     ),
    },
    'login': {
        0x00: Struct('login_start',
                     AlphaString('username'),
                     ),
    },
    'status': {
        0x00: Struct('status_request',
                     UBInt8('unknown'),
                     ),
        0x01: Struct('status_ping',
                     UBInt64('time'),
                     ),
    },
    'play': {
        0x00: Struct('keepalive',
                     SBInt32('keepalive_id'),
                     ),
        0x01: Struct('chat',
                     AlphaString('json'),
                     ),
        0x02: Struct('use_entity',
                     UBInt32('target'),  # eid is apparently self
                     mouse_enum,
                     ),
        0x03: Struct('player',
                     grounded,
                     ),
        0x04: Struct('player_position',
                     position,
                     grounded,
                     ),
        0x05: Struct('player_look',
                     orientation,
                     grounded,
                     ),
        0x06: Struct('player_position_and_look',
                     position,
                     orientation,
                     grounded,
                     ),
        0x07: Struct('player_digging',
                     player_digging_status_enum,
                     SBInt32('x'),
                     UBInt8('y'),
                     SBInt32('z'),
                     face_enum,
                     ),
        0x08: Struct('player_block_placement',
                     SBInt32('x'),
                     UBInt8('y'),
                     SBInt32('z'),
                     face_enum,  # direction
                     slot,
                     UBInt8('cursorx'),
                     UBInt8('cursory'),
                     UBInt8('cursorz'),
                     ),
        0x09: Struct('held_item_change',
                     UBInt16('slot'),
                     ),
        0x0a: Struct('animate',
                     UBInt32('eid'),
                     server_animation_enum,
                     ),
        0x0b: Struct('entity_action',
                     UBInt32('eid'),
                     entity_action_enum,
                     UBInt32('unknown'),  # jump_boost
                     ),
        0x0c: Struct('steer_vehicle',
                     BFloat32('first'),  # sideways
                     BFloat32('second'),  # forward
                     Bool('third'),  # jump
                     Bool('fourth'),  # mount
                     ),
        0x0d: Struct('close_window',
                     UBInt8('wid'),
                     ),
        0x0e: Struct('click_window',
                     UBInt8('wid'),
                     SBInt16('slot_no'),
                     UBInt8('button'),
                     UBInt16('token'),
                     UBInt8('shift'),  # TODO: rename to 'mode'  <-- old
                     slot,  # Embed(items),  # slot
                     ),
        0x0f: Struct('confirm_transaction',
                     UBInt8('wid'),
                     UBInt16('token'),
                     Bool('acknowledged'),
                     ),
        0x10: Struct('creative_inventory_action',
                     UBInt16('slot_no'),
                     slot,  # Embed(items),  # slot
                     ),
        0x11: Struct('enchant_item',
                     UBInt8('wid'),
                     UBInt8('enchantment'),
                     ),
        0x12: Struct('update_sign',
                     SBInt32('x'),
                     UBInt16('y'),  # JMT: yet another y sigh
                     SBInt32('z'),
                     AlphaString('line1'),
                     AlphaString('line2'),
                     AlphaString('line3'),
                     AlphaString('line4'),
                     ),
        0x13: Struct('player_abilities',
                     UBInt8('flags'),
                     BFloat32('fly_speed'),
                     BFloat32('walk_speed'),
                     ),
        0x14: Struct('tab',
                     AlphaString('autocomplete'),  # text
                     ),
        0x15: Struct('client_settings',
                     AlphaString('locale'),
                     UBInt8('distance'),
                     UBInt8('chat'),
                     Bool('unused'),
                     difficulty_enum,
                     Bool('cape'),
                     ),
        0x16: Struct('client_status',
                     UBInt8('payload'),
                     ),
        0x17: Struct('plugin_message',
                     AlphaString('channel'),
                     PascalString('data', length_field=UBInt16('length')),
                     ),
    }
}

serverbound_by_name = dict((k, dict((iv.name, ik) for (ik, iv) in serverbound[k].iteritems())) for (k, v) in serverbound.iteritems())

clientbound = {
    'handshaking': {
        0x00: Struct('handshaking',
                     AlphaString('json'),
                     ),
        0x01: Struct('encryption_request',
                     AlphaString('server_id'),
                     SBInt16('key_len'),
                     MetaField('key', lambda ctx: ctx['key_len']),
                     SBInt16('token_len'),
                     MetaField('token', lambda ctx: ctx['token_len']),
                     ),
        0x40: Struct('disconnect',
                     AlphaString('reason'),
                     ),
    },
    'status': {
        0x00: Struct('status_response',
                     AlphaString('json'),
                     ),
        0x01: Struct('status_ping',
                     UBInt64('time'),
                     ),
        0x40: Struct('disconnect',
                     AlphaString('reason'),
                     ),
    },
    'login': {
        0x02: Struct('login_success',
                     AlphaString('uuid'),
                     AlphaString('username'),
                     ),
        0x40: Struct('disconnect',
                     AlphaString('reason'),
                     ),
    },
    'play': {
        0x00: Struct('keepalive',
                     SBInt32('keepalive_id'),
                     ),
        0x01: Struct('join',
                     SBInt32('eid'),
                     UBInt8('gamemode'),
                     dimension_enum,
                     difficulty_enum,
                     UBInt8('max_players'),
                     AlphaString('level_type'),
                     ),
        0x02: Struct('chat',
                     AlphaString('json'),
                     ),
        0x03: Struct('time',
                     UBInt64('age_of_world'),
                     UBInt64('time_of_day'),
                     ),
        0x04: Struct('entity_equipment',
                     SBInt32('eid'),
                     SBInt16('slot_no'),
                     slot,
                     ),
        0x05: Struct('spawn_position',
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     ),
        0x06: Struct('update_health',
                     BFloat32('health'),
                     SBInt16('food'),
                     BFloat32('food_saturation'),
                     ),
        0x07: Struct('respawn',
                     dimension_enum,
                     difficulty_enum,
                     UBInt8('gamemode'),
                     AlphaString('level_type'),
                     ),
        0x08: Struct('player_position_and_look',
                     BFloat64("x"),
                     BFloat64("y"),
                     BFloat64("z"),
                     orientation,
                     grounded,
                     ),
        0x09: Struct('held_item',
                     UBInt8('slot'),
                     ),
        0x0a: Struct('use_bed',
                     SBInt32('eid'),
                     SBInt32('x'),
                     UBInt8('y'),
                     SBInt32('z'),
                     ),
        0x0b: Struct('animation',
                     VarInt('eid'),
                     UBInt8('animation'),
                     ),
        0x0c: Struct('spawn_player',
                     VarInt('eid'),
                     AlphaString('uuid'),
                     AlphaString('name'),
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     UBInt8('yaw'),
                     UBInt8('pitch'),
                     SBInt16('current_item'),
                     metadata,
                     ),
        0x0d: Struct('collect_item',
                     SBInt32('collected_eid'),
                     SBInt32('collector_eid'),
                     ),
        0x0e: Struct('spawn_object',
                     VarInt('eid'),
                     UBInt8('type'),  # object types are scary
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     SBInt8('pitch'),
                     SBInt8('yaw'),
                     SBInt32('data'),
                     If(lambda ctx: ctx['data'] != 0,
                        Struct('speed',
                               SBInt16('x'),
                               SBInt16('y'),
                               SBInt16('z'),
                               ),
                        ),
                     ),
        0x0f: Struct('spawn_mob',
                     VarInt('eid'),
                     UBInt8('type'),  # mob types are scary
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     UBInt8('pitch'),
                     UBInt8('head_pitch'),
                     UBInt8('yaw'),
                     SBInt16('vx'),
                     SBInt16('vy'),
                     SBInt16('vz'),
                     metadata,
                     ),
        0x10: Struct('spawn_painting',
                     VarInt('eid'),
                     AlphaString('title'),  # max len 13 ?
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     SBInt32('direction'),
                     ),
        0x11: Struct('spawn_experience_orb',
                     VarInt('eid'),
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     SBInt16('count'),
                     ),
        0x12: Struct('entity_velocity',
                     SBInt32('eid'),
                     SBInt16('vx'),
                     SBInt16('vy'),
                     SBInt16('vz'),
                     ),
        0x13: Struct('destroy_entities',
                     SBInt8('count'),
                     MetaArray(lambda ctx: ctx['count'], SBInt32('eid')),
                     ),
        0x14: Struct('create_entity',
                     SBInt32('eid'),
                     ),
        0x15: Struct('entity_relative_move',
                     SBInt32('eid'),
                     UBInt8('dx'),
                     UBInt8('dy'),
                     UBInt8('dz'),
                     ),
        0x16: Struct('entity_look',
                     SBInt32('eid'),
                     UBInt8('yaw'),
                     UBInt8('pitch'),
                     ),
        0x17: Struct('entity_look_and_relative_move',
                     SBInt32('eid'),
                     UBInt8('dx'),
                     UBInt8('dy'),
                     UBInt8('dz'),
                     UBInt8('yaw'),
                     UBInt8('pitch'),
                     ),
        0x18: Struct('entity_teleport',
                     SBInt32('eid'),
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     UBInt8('yaw'),
                     UBInt8('pitch'),
                     ),
        0x19: Struct('entity_head_look',
                     SBInt32('eid'),
                     UBInt8('head_yaw'),
                     ),
        0x1a: Struct('entity_status',
                     SBInt32('eid'),
                     UBInt8('status'),
                     ),
        0x1b: Struct('attach_entity',
                     SBInt32('eid'),
                     SBInt32('vehicle'),
                     Bool('leash'),
                     ),
        0x1c: Struct('entity_metadata',
                     SBInt32('eid'),
                     metadata,
                     ),
        0x1d: Struct('entity_effect',
                     SBInt32('eid'),
                     UBInt8('effect'),
                     UBInt8('amplifier'),
                     SBInt16('duration'),
                     ),
        0x1e: Struct('entity_remove_effect',
                     SBInt32('eid'),
                     UBInt8('effect'),
                     ),
        0x1f: Struct('set_experience',
                     BFloat32('bar'),
                     SBInt16('level'),
                     SBInt16('total'),
                     ),
        0x20: Struct('entity_properties',
                     SBInt32('eid'),
                     SBInt32('count'),
                     MetaArray(lambda ctx: ctx['count'],
                               Struct('property',
                                      AlphaString('key'),
                                      BFloat64('value'),
                                      SBInt16('list_length'),
                                      MetaArray(lambda ctx: ctx['list_length'],
                                                Struct('modifier',
                                                       UBInt64('uuid_1'),
                                                       UBInt64('uuid_2'),
                                                       BFloat64('amount'),
                                                       UBInt8('operation'),
                                                       ),
                                                ),
                                      ),
                               ),
                     ),
        0x21: Struct('chunk_data',
                     SBInt32('chunk_x'),
                     SBInt32('chunk_z'),
                     Bool('continuous'),
                     UBInt16('primary_bitmap'),
                     UBInt16('add_bitmap'),
                     SBInt32('compressed_size'),
                     MetaField('compressed_data',
                               lambda ctx: ctx['compressed_size']
                               ),
                     ),
        0x22: Struct('multi_block_change',
                     SBInt32('chunk_x'),
                     SBInt32('chunk_z'),
                     SBInt16('count'),
                     SBInt32('data_size'),
                     MetaField('data',
                               lambda ctx: ctx['data_size']
                               ),
                     ),
        0x23: Struct('block_change',
                     SBInt32('x'),
                     UBInt8('y'),
                     SBInt32('z'),
                     VarInt('block_type'),
                     UBInt8('block_data'),
                     ),
        0x24: Struct('block_action',
                     SBInt32('x'),
                     SBInt16('y'),
                     SBInt32('z'),
                     UBInt8('byte_1'),
                     UBInt8('byte_2'),
                     VarInt('block_type'),
                     ),
        0x25: Struct('block_break_animation',
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     UBInt8('destroy_stage'),
                     ),
        0x26: Struct('map_chunk_bulk',
                     SBInt16('count'),
                     SBInt32('length'),
                     Bool('sky_light_sent'),
                     MetaField('data',
                               lambda ctx: ctx['length']),
                     MetaArray(lambda ctx: ctx['count'],
                               Struct('metadata',
                                      SBInt32('chunk_x'),
                                      SBInt32('chunk_z'),
                                      SBInt16('primary_bitmap'),
                                      SBInt16('add_bitmap'),
                                      ),
                               ),
                     ),
        0x27: Struct('explosion',
                     BFloat32('x'),
                     BFloat32('y'),
                     BFloat32('z'),
                     BFloat32('radius'),
                     SBInt32('count'),
                     MetaField('data',
                               lambda ctx: ctx['count']*3
                               ),
                     BFloat32('player_motion_x'),
                     BFloat32('player_motion_y'),
                     BFloat32('player_motion_z'),
                     ),
        0x28: Struct('effect',
                     SBInt32('eid'),
                     SBInt32('x'),
                     UBInt8('y'),
                     SBInt32('z'),
                     SBInt32('data'),
                     Bool('disable_relative_volume'),
                     ),
        0x29: Struct('sound_effect',
                     AlphaString('sound_name'),
                     SBInt32('effect_x'),
                     SBInt32('effect_y'),
                     SBInt32('effect_z'),
                     BFloat32('volume'),
                     UBInt8('pitch'),
                     ),
        0x2a: Struct('particle',
                     AlphaString('sound_name'),
                     BFloat32('x'),
                     BFloat32('y'),
                     BFloat32('z'),
                     BFloat32('offset_x'),
                     BFloat32('offset_y'),
                     BFloat32('offset_z'),
                     BFloat32('data'),
                     SBInt32('number'),
                     ),
        0x2b: Struct('change_game_state',
                     game_state_enum,
                     BFloat32('value'),
                     ),
        0x2c: Struct('spawn_global_entity',
                     VarInt('eid'),
                     UBInt8('type'),
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     ),
        0x2d: Struct('open_window',
                     UBInt8('wid'),
                     UBInt8('type'),
                     AlphaString('title'),
                     UBInt8('slots'),
                     Bool('use_provided_title'),
                     If(lambda ctx: ctx['type'] == 11,
                        SBInt32('eid'),
                        ),
                     ),
        0x2e: Struct('close_window',
                     UBInt8('wid'),
                     ),
        0x2f: Struct('set_slot',
                     UBInt8('wid'),
                     SBInt16('slot_no'),
                     slot,
                     ),
        0x30: Struct('window_items',
                     UBInt8('wid'),
                     UBInt16('count'),
                     MetaArray(lambda ctx: ctx['count'], slot),
                     ),
        0x31: Struct('window_property',
                     UBInt8('wid'),
                     SBInt8('property'),
                     SBInt8('value'),
                     ),
        0x32: Struct('confirm_transaction',
                     UBInt8('wid'),
                     UBInt16('action_number'),
                     Bool('accepted'),
                     ),
        0x33: Struct('update_sign',
                     SBInt32('x'),
                     SBInt16('y'),
                     SBInt32('z'),
                     AlphaString('line_1'),
                     AlphaString('line_2'),
                     AlphaString('line_3'),
                     AlphaString('line_4'),
                     ),
        0x34: Struct('maps',
                     VarInt('damage'),
                     SBInt16('length'),
                     MetaField('data', lambda ctx: ctx['length']),
                     ),
        0x35: Struct('update_block_entity',
                     SBInt32('x'),
                     SBInt16('y'),
                     SBInt32('z'),
                     UBInt8('action'),
                     SBInt16('nbt_len'),
                     If(lambda ctx: ctx['nbt_len'] > 0,
                        MetaField('nbt', lambda ctx: ctx['nbt_len'])
                        ),
                     ),
        0x36: Struct('sign_editor_open',
                     SBInt32('x'),
                     SBInt32('y'),
                     SBInt32('z'),
                     ),
        0x37: Struct('statistics',
                     VarInt('count'),
                     MetaArray(lambda ctx: ctx['count'],
                               Struct('statistic',
                                      AlphaString('key'),
                                      VarInt('value'),
                                      )
                               ),
                     ),
        0x38: Struct('player_list_item',
                     AlphaString('player_name'),
                     UBInt8('online'),
                     UBInt16('ping'),
                     ),
        0x39: Struct('player_abilities',
                     UBInt8('flags'),
                     BFloat32('fly_speed'),
                     BFloat32('walk_speed'),
                     ),
        0x3a: Struct('tab_complete',
                     VarInt('count'),
                     # JMT: doubtful
                     AlphaString('match'),
                     ),
        0x3b: Struct('scoreboard_objective',
                     AlphaString('name'),
                     AlphaString('value'),
                     UBInt8('create'),
                     ),
        0x3c: Struct('update_score',
                     AlphaString('item_name'),
                     UBInt8('update'),
                     AlphaString('score_name'),
                     SBInt32('value'),
                     ),
        0x3d: Struct('display_scoreboard',
                     UBInt8('position'),
                     AlphaString('score_name'),
                     ),
        0x3e: Struct('teams',
                     AlphaString('team_name'),
                     UBInt8('mode'),
                     # JMT: Switch!
                     AlphaString('team_display_name'),
                     AlphaString('team_prefix'),
                     AlphaString('team_suffix'),
                     UBInt8('friendly_fire'),
                     SBInt16('count'),
                     MetaArray(lambda ctx: ctx['count'],
                               AlphaString('player')
                               ),
                     ),
        0x3f: Struct('plugin_message',
                     AlphaString('channel'),
                     PascalString('data', length_field=UBInt16('length')),
                     ),
        0x40: Struct('disconnect',
                     AlphaString('reason'),
                     ),
    }
}

clientbound_by_name = dict((k, dict((iv.name, ik) for (ik, iv) in clientbound[k].iteritems())) for (k, v) in clientbound.iteritems())


class BetaServerProtocol(object, Protocol, TimeoutMixin):
    """
    The Minecraft Alpha/Beta server protocol.

    This class is mostly designed to be a skeleton for featureful clients. It
    tries hard to not step on the toes of potential subclasses.
    """

    excess = ""
    packet = None

    state = STATE_UNAUTHENTICATED
    mode = 'handshaking'  # JMT: replace with state soon!

    buf = ""
    parser = None
    handler = None

    player = None
    username = None
    settings = Settings()
    motd = "Bravo Generic Beta Server"

    _health = 20
    _latency = 0

    def __init__(self):
        self.chunks = dict()
        self.windows = {}
        self.wid = 1

        self.location = Location()

        # JMT: replace this with handle_*
        self.handlers = {
            0x00: self.ping,
            0x02: self.handshake,
            0x03: self.chat,
            0x07: self.use,
            0x09: self.respawn,
            0x0a: self.grounded,
            0x0b: self.position,
            0x0c: self.orientation,
            0x0d: self.location_packet,
            0x0e: self.digging,
            0x0f: self.build,
            0x10: self.equip,
            0x12: self.animate,
            0x13: self.action,
            0x15: self.pickup,
            0x65: self.wclose,
            0x66: self.waction,
            0x6a: self.wacknowledge,
            0x6b: self.wcreative,
            0x82: self.sign,
            0xca: self.client_settings,
            0xcb: self.complete,
            0xcc: self.settings_packet,
            0xfe: self.poll,
            0xff: self.quit,
        }

        self._ping_loop = LoopingCall(self.update_ping)

        self.setTimeout(30)

    # Low-level packet handlers
    # Try not to hook these if possible, since they offer no convenient
    # abstractions or protections.

    def ping(self, container):
        """
        Hook for ping packets.

        By default, this hook will examine the timestamps on incoming pings,
        and use them to estimate the current latency of the connected client.
        """

        now = timestamp_from_clock(reactor)
        then = container.pid

        self.latency = now - then

    def handshake(self, container):
        """
        Hook for handshake packets.

        Override this to customize how logins are handled. By default, this
        method will only confirm that the negotiated wire protocol is the
        correct version, copy data out of the packet and onto the protocol,
        and then run the ``authenticated`` callback.

        This method will call the ``pre_handshake`` method hook prior to
        logging in the client.
        """

        self.username = container.username

        if container.protocol < SUPPORTED_PROTOCOL:
            # Kick old clients.
            self.error("This server doesn't support your ancient client.")
            return
        elif container.protocol > SUPPORTED_PROTOCOL:
            # Kick new clients.
            self.error("This server doesn't support your newfangled client.")
            return

        log.msg("Handshaking with client, protocol version %d" %
                container.protocol)

        if not self.pre_handshake():
            log.msg("Pre-handshake hook failed; kicking client")
            self.error("You failed the pre-handshake hook.")
            return

        players = min(self.factory.limitConnections, 20)

        self.write_packet("login", eid=self.eid, leveltype="default",
                          mode=self.factory.mode,
                          dimension=self.factory.world.dimension,
                          difficulty="peaceful", unused=0, maxplayers=players)

        self.authenticated()

    def pre_handshake(self):
        """
        Whether this client should be logged in.
        """

        return True

    def chat(self, container):
        """
        Hook for chat packets.
        """

    def use(self, container):
        """
        Hook for use packets.
        """

    def respawn(self, container):
        """
        Hook for respawn packets.
        """

    def grounded(self, container):
        """
        Hook for grounded packets.
        """

        self.location.grounded = bool(container.grounded)

    def position(self, container):
        """
        Hook for position packets.
        """

        if self.state != STATE_LOCATED:
            log.msg("Ignoring unlocated position!")
            return

        self.grounded(container.grounded)

        old_position = self.location.pos
        position = Position.from_player(container.position.x,
                                        container.position.y,
                                        container.position.z)
        altered = False

        dx, dy, dz = old_position - position
        if any(abs(d) >= 64 for d in (dx, dy, dz)):
            # Whoa, slow down there, cowboy. You're moving too fast. We're
            # gonna ignore this position change completely, because it's
            # either bogus or ignoring a recent teleport.
            altered = True
        else:
            self.location.pos = position
            self.location.stance = container.position.stance

        # Santitize location. This handles safety boundaries, illegal stance,
        # etc.
        altered = self.location.clamp() or altered

        # If, for any reason, our opinion on where the client should be
        # located is different than theirs, force them to conform to our point
        # of view.
        if altered:
            log.msg("Not updating bogus position!")
            self.update_location()

        # If our position actually changed, fire the position change hook.
        if old_position != position:
            self.position_changed()

    def orientation(self, container):
        """
        Hook for orientation packets.
        """

        self.grounded(container.grounded)

        old_orientation = self.location.ori
        orientation = Orientation.from_degs(container.orientation.rotation,
                                            container.orientation.pitch)
        self.location.ori = orientation

        if old_orientation != orientation:
            self.orientation_changed()

    def location_packet(self, container):
        """
        Hook for location packets.
        """

        self.position(container)
        self.orientation(container)

    def digging(self, container):
        """
        Hook for digging packets.
        """

    def build(self, container):
        """
        Hook for build packets.
        """

    def equip(self, container):
        """
        Hook for equip packets.
        """

    def pickup(self, container):
        """
        Hook for pickup packets.
        """

    def animate(self, container):
        """
        Hook for animate packets.
        """

    def action(self, container):
        """
        Hook for action packets.
        """

    def wclose(self, container):
        """
        Hook for wclose packets.
        """

    def waction(self, container):
        """
        Hook for waction packets.
        """

    def wacknowledge(self, container):
        """
        Hook for wacknowledge packets.
        """

    def wcreative(self, container):
        """
        Hook for creative inventory action packets.
        """

    def sign(self, container):
        """
        Hook for sign packets.
        """

    def client_settings(self, container):
        """
        Hook for interaction setting packets.
        """

        self.settings.update_interaction(container)

    def complete(self, container):
        """
        Hook for tab-completion packets.
        """

    def settings_packet(self, container):
        """
        Hook for presentation setting packets.
        """

        self.settings.update_presentation(container)

    def poll(self, container):
        """
        Hook for poll packets.

        By default, queries the parent factory for some data, and replays it
        in a specific format to the requester. The connection is then closed
        at both ends. This functionality is used by Beta 1.8 clients to poll
        servers for status.
        """

        log.msg("Poll data: %r" % container.data)

        players = unicode(len(self.factory.protocols))
        max_players = unicode(self.factory.limitConnections or 1000000)

        data = [
            u"§1",
            unicode(SUPPORTED_PROTOCOL),
            u"Bravo %s" % version,
            self.motd,
            players,
            max_players,
        ]

        response = u"\u0000".join(data)
        self.error(response)

    def quit(self, container):
        """
        Hook for quit packets.

        By default, merely logs the quit message and drops the connection.

        Even if the connection is not dropped, it will be lost anyway since
        the client will close the connection. It's better to explicitly let it
        go here than to have zombie protocols.
        """

        log.msg("Client is quitting: %s" % container.message)
        self.transport.loseConnection()

    # handle hooks for the existing protocol
    # packet is the payload of the packet in Container form
    def handle_handshaking(self, packet):
        return NotImplementedError

    def handle_encryption_response(self, packet):
        return NotImplementedError

    def handle_login_start(self, packet):
        return NotImplementedError

    def handle_status_request(self, packet):
        return NotImplementedError

    def handle_status_ping(self, packet):
        return NotImplementedError

    def handle_keepalive(self, packet):
        return NotImplementedError

    def handle_chat(self, packet):
        return NotImplementedError

    def handle_use_entity(self, packet):
        return NotImplementedError

    def handle_player(self, packet):
        return NotImplementedError

    def handle_player_position(self, packet):
        return NotImplementedError

    def handle_player_look(self, packet):
        return NotImplementedError

    def handle_player_position_and_look(self, packet):
        return NotImplementedError

    def handle_player_digging(self, packet):
        return NotImplementedError

    def handle_player_block_placement(self, packet):
        return NotImplementedError

    def handle_held_item_change(self, packet):
        return NotImplementedError

    def handle_animate(self, packet):
        return NotImplementedError

    def handle_entity_action(self, packet):
        return NotImplementedError

    def handle_steer_vehicle(self, packet):
        return NotImplementedError

    def handle_close_window(self, packet):
        return NotImplementedError

    def handle_click_window(self, packet):
        return NotImplementedError

    def handle_confirm_transaction(self, packet):
        return NotImplementedError

    def handle_creative_inventory_action(self, packet):
        return NotImplementedError

    def handle_enchant_item(self, packet):
        return NotImplementedError

    def handle_update_sign(self, packet):
        return NotImplementedError

    def handle_player_abilities(self, packet):
        return NotImplementedError

    def handle_tab(self, packet):
        return NotImplementedError

    def handle_client_settings(self, packet):
        return NotImplementedError

    def handle_client_status(self, packet):
        return NotImplementedError

    def handle_plugin_message(self, packet):
        return NotImplementedError

    # Twisted-level data handlers and methods
    # Please don't override these needlessly, as they are pretty solid and
    # shouldn't need to be touched.

    def dataReceived(self, data):
        self.buf += data

        packets, self.buf = parse_packets(self.buf)

        if packets:
            self.resetTimeout()

        for header, payload in packets:
            if header in serverbound[self.mode]:  # replace with try/except ?
                struct = serverbound[self.mode][header]
                method = getattr(self, 'handle_%s' % struct.name)
                if payload == '':
                    packet = ''
                else:
                    try:
                        packet = struct.parse(payload)
                    except Exception as e:
                        log.err(e)
                        log.err(header)
                        log.err(payload)
                d = maybeDeferred(method, packet=packet)

                @d.addErrback
                def eb(failure):
                    log.err("Error while handling packet 0x%.2x" % header)
                    log.err(failure)
                    return None
            else:
                log.err("Didn't handle parseable packet 0x%.2x!" % header)
                log.err(payload)

    def connectionLost(self, reason=connectionDone):
        if self._ping_loop.running:
            self._ping_loop.stop()

    def timeoutConnection(self):
        self.error("Connection timed out")

    # State-change callbacks
    # Feel free to override these, but call them at some point.

    def authenticated(self):
        """
        Called when the client has successfully authenticated with the server.
        """

        self.state = STATE_AUTHENTICATED

        self._ping_loop.start(30)

    # Event callbacks
    # These are meant to be overriden.

    def orientation_changed(self):
        """
        Called when the client moves.

        This callback is only for orientation, not position.
        """

        pass

    def position_changed(self):
        """
        Called when the client moves.

        This callback is only for position, not orientation.
        """

        pass

    # Convenience methods for consolidating code and expressing intent. I
    # hear that these are occasionally useful. If a method in this section can
    # be used, then *PLEASE* use it; not using it is the same as open-coding
    # whatever you're doing, and only hurts in the long run.

    def write_packet(self, packet_name, *args, **kwargs):
        """
        Send a packet to the client.
        """
        print "writing a packet yay -- packet_name %s" % packet_name
        self.transport.write(make_packet(packet_name, mode=self.mode, *args, **kwargs))

    def update_ping(self):
        """
        Send a keepalive to the client.
        """
        if self.mode == 'play':
            timestamp = timestamp_from_clock(reactor)
            self.write_packet("keepalive", keepalive_id=timestamp)

    def update_location(self):
        """
        Send this client's location to the client.

        Also let other clients know where this client is.
        """

        # Don't bother trying to update things if the position's not yet
        # synchronized. We could end up jettisoning them into the void.
        if self.state != STATE_LOCATED:
            return

        x, y, z = self.location.pos
        yaw, pitch = self.location.ori.to_fracs()

        # Inform everybody of our new location.
        packet = make_packet("entity_teleport", eid=self.player.eid, x=x, y=y, z=z,
                             yaw=yaw, pitch=pitch)
        self.factory.broadcast_for_others(packet, self)

        # Inform ourselves of our new location.
        packet = self.location.save_to_packet()
        self.transport.write(packet)

    def ascend(self, count):
        """
        Ascend to the next XZ-plane.

        ``count`` is the number of ascensions to perform, and may be zero in
        order to force this player to not be standing inside a block.

        :returns: bool of whether the ascension was successful

        This client must be located for this method to have any effect.
        """

        if self.state != STATE_LOCATED:
            return False

        x, y, z = self.location.pos.to_block()

        bigx, smallx, bigz, smallz = split_coords(x, z)

        chunk = self.chunks[bigx, bigz]
        column = [chunk.get_block((smallx, i, smallz))
                  for i in range(CHUNK_HEIGHT)]

        # Special case: Ascend at most once, if the current spot isn't good.
        if count == 0:
            if (not column[y]) or column[y + 1] or column[y + 2]:
                # Yeah, we're gonna need to move.
                count += 1
            else:
                # Nope, we're fine where we are.
                return True

        for i in xrange(y, 255):
            # Find the next spot above us which has a platform and two empty
            # blocks of air.
            if column[i] and (not column[i + 1]) and not column[i + 2]:
                count -= 1
                if not count:
                    break
        else:
            return False

        self.location.pos = self.location.pos._replace(y=i * 32)
        return True

    def error(self, message):
        """
        Error out.

        This method sends ``message`` to the client as a descriptive error
        message, then closes the connection.
        """

        log.msg("Error: %r" % message)
        self.write_packet('disconnect', reason=message, )
        self.transport.loseConnection()

    def play_notes(self, notes):
        """
        Play some music.

        Send a sequence of notes to the player. ``notes`` is a finite iterable
        of pairs of instruments and pitches.

        There is no way to time notes; if staggered playback is desired (and
        it usually is!), then ``play_notes()`` should be called repeatedly at
        the appropriate times.

        This method turns the block beneath the player into a note block,
        plays the requested notes through it, then turns it back into the
        original block, all without actually modifying the chunk.
        """

        x, y, z = self.location.pos.to_block()

        if y:
            y -= 1

        bigx, smallx, bigz, smallz = split_coords(x, z)

        if (bigx, bigz) not in self.chunks:
            return

        block = self.chunks[bigx, bigz].get_block((smallx, y, smallz))
        meta = self.chunks[bigx, bigz].get_metadata((smallx, y, smallz))

        self.write_packet("block", x=x, y=y, z=z,
                          type=blocks["note-block"].slot, meta=0)

        for instrument, pitch in notes:
            self.write_packet("note", x=x, y=y, z=z, pitch=pitch,
                              instrument=instrument)

        self.write_packet("block", x=x, y=y, z=z, type=block, meta=meta)

    def send_chat(self, message):
        """
        Send a chat message back to the client.
        """

        data = json.dumps({"text": message})
        self.write_packet("chat", json=data)

    # Automatic properties. Assigning to them causes the client to be notified
    # of changes.

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if not 0 <= value <= 20:
            raise BetaClientError("Invalid health value %d" % value)

        if self._health != value:
            self.write_packet("health", hp=value, fp=0, saturation=0)
            self._health = value

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self, value):
        # Clamp the value to not exceed the boundaries of the packet. This is
        # necessary even though, in theory, a ping this high is bad news.
        value = clamp(value, 0, 65535)

        # Check to see if this is a new value, and if so, alert everybody.
        if self._latency != value:
            packet = make_packet("player_list_item", player_name=self.username, online=True,
                                 ping=value)
            self.factory.broadcast(packet)
            self._latency = value


class KickedProtocol(BetaServerProtocol):
    """
    A very simple Beta protocol that helps enforce IP bans, Max Connections,
    and Max Connections Per IP.

    This protocol disconnects people as soon as they connect, with a helpful
    message.
    """

    def __init__(self, reason=None):
        BetaServerProtocol.__init__(self)
        if reason:
            self.reason = reason
        else:
            self.reason = (
                "This server doesn't like you very much."
                " I don't like you very much either.")

    def connectionMade(self):
        self.error("%s" % self.reason)


class BetaProxyProtocol(BetaServerProtocol):
    """
    A ``BetaServerProtocol`` that proxies for an InfiniCraft client.
    """

    gateway = "server.wiki.vg"

    def handshake(self, container):
        self.write_packet("handshake", username="-")

    def login(self, container):
        self.username = container.username

        self.write_packet("login", protocol=0, username="", seed=0,
                          dimension="earth")

        url = urlunparse(("http", self.gateway, "/node/0/0/", None, None,
                          None))
        d = getPage(url)
        d.addCallback(self.start_proxy)

    def start_proxy(self, response):
        log.msg("Response: %s" % response)
        log.msg("Starting proxy...")
        address, port = response.split(":")
        self.add_node(address, int(port))

    def add_node(self, address, port):
        """
        Add a new node to this client.
        """

        from twisted.internet.endpoints import TCP4ClientEndpoint

        log.msg("Adding node %s:%d" % (address, port))

        endpoint = TCP4ClientEndpoint(reactor, address, port, 5)

        self.node_factory = InfiniClientFactory()
        d = endpoint.connect(self.node_factory)
        d.addCallback(self.node_connected)
        d.addErrback(self.node_connect_error)

    def node_connected(self, protocol):
        log.msg("Connected new node!")

    def node_connect_error(self, reason):
        log.err("Couldn't connect node!")
        log.err(reason)


class BravoProtocol(BetaServerProtocol):
    """
    A ``BetaServerProtocol`` suitable for serving MC worlds to clients.

    This protocol really does need to be hooked up with a ``BravoFactory`` or
    something very much like it.
    """

    chunk_tasks = None

    time_loop = None

    eid = 0

    last_dig = None

    def __init__(self, config, name):
        BetaServerProtocol.__init__(self)

        self.config = config
        self.config_name = "world %s" % name

        # Retrieve the MOTD. Only needs to be done once.
        self.motd = self.config.getdefault(self.config_name, "motd",
                                           "BravoServer")

    def register_hooks(self):
        log.msg("Registering client hooks...")
        plugin_types = {
            "open_hooks": IWindowOpenHook,
            "click_hooks": IWindowClickHook,
            "close_hooks": IWindowCloseHook,
            "pre_build_hooks": IPreBuildHook,
            "post_build_hooks": IPostBuildHook,
            "pre_dig_hooks": IPreDigHook,
            "dig_hooks": IDigHook,
            "sign_hooks": ISignHook,
            "use_hooks": IUseHook,
        }

        for t in plugin_types:
            setattr(self, t, getattr(self.factory, t))

        log.msg("Registering policies...")
        if self.factory.mode == "creative":
            self.dig_policy = dig_policies["speedy"]
        else:
            self.dig_policy = dig_policies["notchy"]

        log.msg("Registered client plugin hooks!")

    def pre_handshake(self):
        """
        Set up username and get going.
        """
        if self.username in self.factory.protocols:
            # This username's already taken; find a new one.
            for name in username_alternatives(self.username):
                if name not in self.factory.protocols:
                    self.username = name
                    break
            else:
                self.error("Your username is already taken.")
                return False

        return True

    @inlineCallbacks
    def authenticated(self):
        BetaServerProtocol.authenticated(self)
        self.mode = 'play'

        # Init player, and copy data into it.
        self.player = yield self.factory.world.load_player(self.username)
        self.player.eid = self.eid
        self.player.uuid = self.uuid
        self.location = self.player.location
        # Init players' inventory window.
        self.inventory = InventoryWindow(self.player.inventory)

        # *Now* we are in our factory's list of protocols. Be aware.
        self.factory.protocols[self.username] = self

        # Actually join the game.
        self.write_packet('join', eid=self.player.eid, gamemode=0, dimension='earth', difficulty='peaceful', max_players=self.factory.limitConnections, level_type="default")

        # Advertise our brand.
        self.write_packet('plugin_message', channel='MC|Brand', data='bravo')

        # Where are we going to spawn anyway?

        # Shower me with player abilities!
        kwargs = self.settings.make_interaction_packet_fodder()
        self.write_packet('player_abilities', **kwargs)

        # What are we holding in our hands?
        self.write_packet('held_item', slot=0)

        # Announce our presence.
        self.factory.chat("%s is joining the game..." % self.username)
        packet = make_packet("player_list_item", player_name=self.username, online=True,
                             ping=0)
        self.factory.broadcast(packet)

        # Craft our avatar and send it to already-connected other players.
        packet = make_packet("create_entity", eid=self.player.eid)
        packet += self.player.save_to_packet()
        self.factory.broadcast_for_others(packet, self)

        # And of course spawn all of those players' avatars in our client as
        # well.
        for protocol in self.factory.protocols.itervalues():
            # Skip over ourselves; otherwise, the client tweaks out and
            # usually either dies or locks up.
            if protocol is self:
                continue

            self.write_packet("create_entity", eid=protocol.player.eid)
            packet = protocol.player.save_to_packet()
            packet += protocol.player.save_equipment_to_packet()
            self.transport.write(packet)

        # Send spawn and inventory.
        spawn = self.factory.world.level.spawn
        packet = make_packet("spawn_position", x=spawn[0], y=spawn[1], z=spawn[2])
        packet += self.inventory.save_to_packet()
        self.transport.write(packet)

        # TODO: Send Abilities (0xca)
        # TODO: Update Health (0x08)
        # TODO: Update Experience (0x2b)

        # Send weather.
        self.transport.write(self.factory.vane.make_packet())

        self.send_initial_chunk_and_location()

        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(10)

    def orientation_changed(self):
        # Bang your head!
        yaw, pitch = self.location.ori.to_fracs()
        packet = make_packet("entity_look", eid=self.player.eid,
                             yaw=yaw, pitch=pitch)
        self.factory.broadcast_for_others(packet, self)

    def position_changed(self):
        # Send chunks.
        self.update_chunks()

        for entity in self.entities_near(2):
            if entity.name != "Item":
                continue

            left = self.player.inventory.add(entity.item, entity.quantity)
            if left != entity.quantity:
                if left != 0:
                    # partial collect
                    entity.quantity = left
                else:
                    packet = make_packet("collect_item", collected_eid=entity.eid, collector_eid=self.player.eid)
                    packet += make_packet("destroy_entities", count=1, eid=[entity.eid])
                    self.factory.broadcast(packet)
                    self.factory.destroy_entity(entity)

                packet = self.inventory.save_to_packet()
                self.transport.write(packet)

    def entities_near(self, radius):
        """
        Obtain the entities within a radius of this player.

        Radius is measured in blocks.
        """

        chunk_radius = int(radius // 16 + 1)
        chunkx, chunkz = self.location.pos.to_chunk()

        minx = chunkx - chunk_radius
        maxx = chunkx + chunk_radius + 1
        minz = chunkz - chunk_radius
        maxz = chunkz + chunk_radius + 1

        for x, z in product(xrange(minx, maxx), xrange(minz, maxz)):
            if (x, z) not in self.chunks:
                continue
            chunk = self.chunks[x, z]

            yieldables = [entity for entity in chunk.entities
                          if self.location.distance(entity.location) <= (radius * 32)]
            for i in yieldables:
                yield i

    def chat(self, container):
        # data = json.loads(container.data)
        log.msg("Chat! %r" % container.data)
        if container.message.startswith("/"):
            commands = retrieve_plugins(IChatCommand, factory=self.factory)
            # Register aliases.
            for plugin in commands.values():
                for alias in plugin.aliases:
                    commands[alias] = plugin

            params = container.message[1:].split(" ")
            command = params.pop(0).lower()

            if command and command in commands:
                def cb(iterable):
                    for line in iterable:
                        self.send_chat(line)

                def eb(error):
                    self.send_chat("Error: %s" % error.getErrorMessage())

                d = maybeDeferred(commands[command].chat_command,
                                  self.username, params)
                d.addCallback(cb)
                d.addErrback(eb)
            else:
                self.send_chat("Unknown command: %s" % command)
        else:
            # Send the message up to the factory to be chatified.
            message = "<%s> %s" % (self.username, container.message)
            self.factory.chat(message)

    def use(self, container):
        """
        For each entity in proximity (4 blocks), check if it is the target
        of this packet and call all hooks that stated interested in this
        type.
        """
        nearby_players = self.factory.players_near(self.player, 4)
        for entity in chain(self.entities_near(4), nearby_players):
            if entity.eid == container.target:
                for hook in self.use_hooks[entity.name]:
                    hook.use_hook(self.factory, self.player, entity,
                                  container.button == 0)
                break

    @inlineCallbacks
    def digging(self, container):
        if container.x == -1 and container.z == -1 and container.y == 255:
            # Lala-land dig packet. Discard it for now.
            return

        # Player drops currently holding item/block.
        if (container.state == "dropped" and container.face == "-y" and container.x == 0 and container.y == 0 and container.z == 0):
            i = self.player.inventory
            holding = i.holdables[self.player.equipped]
            if holding:
                primary, secondary, count = holding
                if i.consume((primary, secondary), self.player.equipped):
                    dest = self.location.in_front_of(2)
                    coords = dest.pos._replace(y=dest.pos.y + 1)
                    self.factory.give(coords, (primary, secondary), 1)

                    # Re-send inventory.
                    packet = self.inventory.save_to_packet()
                    self.transport.write(packet)

                    # If no items in this slot are left, this player isn't
                    # holding an item anymore.
                    if i.holdables[self.player.equipped] is None:
                        packet = make_packet("entity_equipment",
                                             eid=self.player.eid,
                                             slot_no=0,
                                             slot=Slot(),
                                             )
                        self.factory.broadcast_for_others(packet, self)
            return

        if container.state == "shooting":
            self.shoot_arrow()
            return

        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        coords = smallx, container.y, smallz

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't dig in chunk (%d, %d)!" % (bigx, bigz))
            return

        block = chunk.get_block((smallx, container.y, smallz))

        if container.state == "started":
            # Run pre dig hooks
            for hook in self.pre_dig_hooks:
                cancel = yield maybeDeferred(hook.pre_dig_hook, self.player,
                                             (container.x, container.y, container.z), block)
                if cancel:
                    return

            tool = self.player.inventory.holdables[self.player.equipped]
            # Check to see whether we should break this block.
            if self.dig_policy.is_1ko(block, tool):
                self.run_dig_hooks(chunk, coords, blocks[block])
            else:
                # Set up a timer for breaking the block later.
                dtime = time() + self.dig_policy.dig_time(block, tool)
                self.last_dig = coords, block, dtime
        elif container.state == "stopped":
            # The client thinks it has broken a block. We shall see.
            if not self.last_dig:
                return

            oldcoords, oldblock, dtime = self.last_dig
            if oldcoords != coords or oldblock != block:
                # Nope!
                self.last_dig = None
                return

            dtime -= time()

            # When enough time has elapsed, run the dig hooks.
            d = deferLater(reactor, max(dtime, 0), self.run_dig_hooks, chunk,
                           coords, blocks[block])
            d.addCallback(lambda none: setattr(self, "last_dig", None))

    def run_dig_hooks(self, chunk, coords, block):
        """
        Destroy a block and run the post-destroy dig hooks.
        """

        x, y, z = coords

        if block.breakable:
            chunk.destroy(coords)

        l = []
        for hook in self.dig_hooks:
            l.append(maybeDeferred(hook.dig_hook, chunk, x, y, z, block))

        dl = DeferredList(l)
        dl.addCallback(lambda none: self.factory.flush_chunk(chunk))

    @inlineCallbacks
    def build(self, container):
        """
        Handle a build packet.

        Several things must happen. First, the packet's contents need to be
        examined to ensure that the packet is valid. A check is done to see if
        the packet is opening a windowed object. If not, then a build is
        run.
        """

        # Is the target within our purview? We don't do a very strict
        # containment check, but we *do* require that the chunk be loaded.
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)
        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't select in chunk (%d, %d)!" % (bigx, bigz))
            return

        target = blocks[chunk.get_block((smallx, container.y, smallz))]

        # Attempt to open a window.
        from bravo.policy.windows import window_for_block
        window = window_for_block(target)
        if window is not None:
            # We have a window!
            self.windows[self.wid] = window
            identifier, title, slots = window.open()
            self.write_packet("window-open", wid=self.wid, type=identifier,
                              title=title, slots=slots)
            self.wid += 1
            return

        # Try to open it first
        for hook in self.open_hooks:
            window = yield maybeDeferred(hook.open_hook, self, container,
                                         chunk.get_block((smallx, container.y, smallz)))
            if window:
                self.write_packet("window-open", wid=window.wid,
                                  type=window.identifier, title=window.title,
                                  slots=window.slots_num)
                packet = window.save_to_packet()
                self.transport.write(packet)
                # window opened
                return

        # Ignore clients that think -1 is placeable.
        if container.primary == -1:
            return

        # Special case when face is "noop": Update the status of the currently
        # held block rather than placing a new block.
        if container.face == "noop":
            return

        # If the target block is vanishable, then adjust our aim accordingly.
        if target.vanishes:
            container.face = "+y"
            container.y -= 1

        if container.primary in blocks:
            block = blocks[container.primary]
        elif container.primary in items:
            block = items[container.primary]
        else:
            log.err("Ignoring request to place unknown block 0x%x" %
                    container.primary)
            return

        # Run pre-build hooks. These hooks are able to interrupt the build
        # process.
        builddata = BuildData(block, 0x0, container.x, container.y,
                              container.z, container.face)

        for hook in self.pre_build_hooks:
            cont, builddata, cancel = yield maybeDeferred(hook.pre_build_hook,
                                                          self.player, builddata)
            if cancel:
                # Flush damaged chunks.
                for chunk in self.chunks.itervalues():
                    self.factory.flush_chunk(chunk)
                return
            if not cont:
                break

        # Run the build.
        try:
            yield maybeDeferred(self.run_build, builddata)
        except BuildError:
            return

        newblock = builddata.block.slot
        coords = adjust_coords_for_face(
            (builddata.x, builddata.y, builddata.z), builddata.face)

        # Run post-build hooks. These are merely callbacks which cannot
        # interfere with the build process, largely because the build process
        # already happened.
        for hook in self.post_build_hooks:
            yield maybeDeferred(hook.post_build_hook, self.player, coords,
                                builddata.block)

        # Feed automatons.
        for automaton in self.factory.automatons:
            if newblock in automaton.blocks:
                automaton.feed(coords)

        # Re-send inventory.
        # XXX this could be optimized if/when inventories track damage.
        packet = self.inventory.save_to_packet()
        self.transport.write(packet)

        # Flush damaged chunks.
        for chunk in self.chunks.itervalues():
            self.factory.flush_chunk(chunk)

    def run_build(self, builddata):
        block, metadata, x, y, z, face = builddata

        # Don't place items as blocks.
        if block.slot not in blocks:
            raise BuildError("Couldn't build item %r as block" % block)

        # Check for orientable blocks.
        if not metadata and block.orientable():
            metadata = block.orientation(face)
            if metadata is None:
                # Oh, I guess we can't even place the block on this face.
                raise BuildError("Couldn't orient block %r on face %s" %
                                 (block, face))

        # Make sure we can remove it from the inventory first.
        if not self.player.inventory.consume((block.slot, 0),
                                             self.player.equipped):
            # Okay, first one was a bust; maybe we can consume the related
            # block for dropping instead?
            if not self.player.inventory.consume(block.drop,
                                                 self.player.equipped):
                raise BuildError("Couldn't consume %r from inventory" % block)

        # Offset coords according to face.
        x, y, z = adjust_coords_for_face((x, y, z), face)

        # Set the block and data.
        dl = [self.factory.world.set_block((x, y, z), block.slot)]
        if metadata:
            dl.append(self.factory.world.set_metadata((x, y, z), metadata))

        return DeferredList(dl)

    def equip(self, container):
        self.player.equipped = container.slot

        # Inform everyone about the item the player is holding now.
        item = self.player.inventory.holdables[self.player.equipped]
        if item is None:
            # Empty slot. Use signed short -1.
            primary, secondary = -1, 0
        else:
            primary, secondary, count = item

        packet = make_packet("entity_equipment",
                             eid=self.player.eid,
                             slot_no=0,
                             slot=Slot(item_id=primary, count=1, damage=secondary),
                             )
        self.factory.broadcast_for_others(packet, self)

    def pickup(self, container):
        self.factory.give((container.x, container.y, container.z),
                          (container.primary, container.secondary), container.count)

    def animate(self, container):
        # Broadcast the animation of the entity to everyone else. Only swing
        # arm is send by notchian clients.
        packet = make_packet("animate",
                             eid=self.player.eid,
                             animation=container.animation
                             )
        self.factory.broadcast_for_others(packet, self)

    def wclose(self, container):
        wid = container.wid
        if wid == 0:
            # WID 0 is reserved for the client inventory.
            pass
        elif wid in self.windows:
            w = self.windows.pop(wid)
            w.close()
        else:
            self.error("WID %d doesn't exist." % wid)

    def waction(self, container):
        wid = container.wid
        if wid in self.windows:
            w = self.windows[wid]
            result = w.action(container.slot, container.button,
                              container.token, container.shift,
                              container.primary)
            self.write_packet("window-token", wid=wid, token=container.token,
                              acknowledged=result)
        else:
            self.error("WID %d doesn't exist." % wid)

    def wcreative(self, container):
        """
        A slot was altered in creative mode.
        """

        # XXX Sometimes the container doesn't contain all of this information.
        # What then?
        applied = self.inventory.creative(container.slot, container.primary,
                                          container.secondary, container.count)
        if applied:
            # Inform other players about changes to this player's equipment.
            equipped_slot = self.player.equipped + 36
            if container.slot == equipped_slot:
                packet = make_packet("entity_equipment",
                                     eid=self.player.eid,
                                     # XXX why 0? why not the actual slot?
                                     slot_no=0,
                                     slot=Slot(item_id=container.primary,
                                               count=1,
                                               damage=container.secondary),
                                     )
                self.factory.broadcast_for_others(packet, self)

    def shoot_arrow(self):
        # TODO 1. Create arrow entity:          arrow = Arrow(self.factory, self.player)
        #      2. Register within the factory:  self.factory.register_entity(arrow)
        #      3. Run it:                       arrow.run()
        pass

    def sign(self, container):
        bigx, smallx, bigz, smallz = split_coords(container.x, container.z)

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't handle sign in chunk (%d, %d)!" % (bigx, bigz))
            return

        if (smallx, container.y, smallz) in chunk.tiles:
            new = False
            s = chunk.tiles[smallx, container.y, smallz]
        else:
            new = True
            s = Sign(smallx, container.y, smallz)
            chunk.tiles[smallx, container.y, smallz] = s

        s.text1 = container.line1
        s.text2 = container.line2
        s.text3 = container.line3
        s.text4 = container.line4

        chunk.dirty = True

        # The best part of a sign isn't making one, it's showing everybody
        # else on the server that you did.
        packet = make_packet("update_sign", container)
        self.factory.broadcast_for_chunk(packet, bigx, bigz)

        # Run sign hooks.
        for hook in self.sign_hooks:
            hook.sign_hook(self.factory, chunk, container.x, container.y,
                           container.z, [s.text1, s.text2, s.text3, s.text4], new)

    def complete(self, container):
        """
        Attempt to tab-complete user names.
        """

        needle = container.autocomplete
        usernames = self.factory.protocols.keys()

        results = complete(needle, usernames)

        self.write_packet("tab", autocomplete=results)

    def settings_packet(self, container):
        """
        Acknowledge a change of settings and update chunk distance.
        """

        super(BravoProtocol, self).settings_packet(container)
        self.update_chunks()

    def disable_chunk(self, x, z):
        key = x, z

        log.msg("Disabling chunk %d, %d" % key)

        if key not in self.chunks:
            log.msg("...But the chunk wasn't loaded!")
            return

        # Remove the chunk from cache.
        chunk = self.chunks.pop(key)

        eids = [e.eid for e in chunk.entities]

        self.write_packet("destroy", count=len(eids), eid=eids)

        # Clear chunk data on the client.
        self.write_packet("chunk", x=x, z=z, continuous=False, primary=0x0,
                          add=0x0, data="")

    def enable_chunk(self, x, z):
        """
        Request a chunk.

        This function will asynchronously obtain the chunk, and send it on the
        wire.

        :returns: `Deferred` that will be fired when the chunk is obtained,
                  with no arguments
        """

        log.msg("Enabling chunk %d, %d" % (x, z))

        if (x, z) in self.chunks:
            log.msg("...But the chunk was already loaded!")
            return succeed(None)

        d = self.factory.world.request_chunk(x, z)

        @d.addCallback
        def cb(chunk):
            self.chunks[x, z] = chunk
            return chunk
        d.addCallback(self.send_chunk)

        return d

    def send_chunk(self, chunk):
        log.msg("Sending chunk %d, %d" % (chunk.x, chunk.z))

        packet = chunk.save_to_packet()
        self.transport.write(packet)
        log.msg("Chunk sent!")

        for entity in chunk.entities:
            log.msg(entity)
            packet = entity.save_to_packet()
            self.transport.write(packet)

        for entity in chunk.tiles.itervalues():
            if entity.name == "Sign":
                packet = entity.save_to_packet()
                self.transport.write(packet)

    def send_initial_chunk_and_location(self):
        """
        Send the initial chunks and location.

        This method sends more than one chunk; since Beta 1.2, it must send
        nearly fifty chunks before the location can be safely sent.
        """

        # Disable located hooks. We'll re-enable them at the end.
        self.state = STATE_AUTHENTICATED

        log.msg("Initial position %d, %d, %d" % self.location.pos)
        x, y, z = self.location.pos.to_block()
        bigx, smallx, bigz, smallz = split_coords(x, z)

        # Send the chunk that the player will stand on. The other chunks are
        # not so important. There *used* to be a bug, circa Beta 1.2, that
        # required lots of surrounding geometry to be present, but that's been
        # fixed.
        d = self.enable_chunk(bigx, bigz)

        # What to do if we can't load a given chunk? Just kick 'em.
        d.addErrback(lambda fail: self.error("Couldn't load a chunk... :c"))

        # Don't dare send more chunks beyond the initial one until we've
        # spawned. Once we've spawned, set our status to LOCATED and then
        # update_location() will work.
        @d.addCallback
        def located(none):
            self.state = STATE_LOCATED
            # Ensure that we're above-ground.
            self.ascend(0)
        d.addCallback(lambda none: self.update_location())
        d.addCallback(lambda none: self.position_changed())

        # Send the MOTD.
        if self.motd:
            @d.addCallback
            def motd(none):
                self.send_chat(self.motd.replace("<tagline>", get_motd()))

        # Finally, start the secondary chunk loop.
        d.addCallback(lambda none: self.update_chunks())

    def update_chunks(self):
        # Don't send chunks unless we're located.
        if self.state != STATE_LOCATED:
            return

        x, z = self.location.pos.to_chunk()

        # These numbers come from a couple spots, including minecraftwiki, but
        # I verified them experimentally using torches and pillars to mark
        # distances on each setting. ~ C.
        distances = {
            "tiny": 2,
            "short": 4,
            "far": 16,
        }

        radius = distances.get(self.settings.distance, 8)

        new = set(circling(x, z, radius))
        old = set(self.chunks.iterkeys())
        added = new - old
        discarded = old - new

        # Perhaps some explanation is in order.
        # The cooperate() function iterates over the iterable it is fed,
        # without tying up the reactor, by yielding after each iteration. The
        # inner part of the generator expression generates all of the chunks
        # around the currently needed chunk, and it sorts them by distance to
        # the current chunk. The end result is that we load chunks one-by-one,
        # nearest to furthest, without stalling other clients.
        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass

        to_enable = sorted_by_distance(added, x, z)

        self.chunk_tasks = [
            cooperate(self.enable_chunk(i, j) for i, j in to_enable),
            cooperate(self.disable_chunk(i, j) for i, j in discarded),
        ]

    def update_time(self):
        time = int(self.factory.time)
        self.write_packet("time", age_of_world=time, time_of_day=time % 24000)

    def connectionLost(self, reason=connectionDone):
        """
        Cleanup after a lost connection.

        Most of the time, these connections are lost cleanly; we don't have
        any cleanup to do in the unclean case since clients don't have any
        kind of pending state which must be recovered.

        Remember, the connection can be lost before identification and
        authentication, so ``self.username`` and ``self.player`` can be None.
        """

        if self.username and self.player:
            self.factory.world.save_player(self.username, self.player)

        if self.player:
            self.factory.destroy_entity(self.player)
            packet = make_packet("destroy_entities", count=1, eid=[self.player.eid])
            self.factory.broadcast(packet)

        if self.username:
            packet = make_packet("player_list_item", player_name=self.username, online=False,
                                 ping=0)
            self.factory.broadcast(packet)
            self.factory.chat("%s has left the game." % self.username)

        self.factory.teardown_protocol(self)

        # We are now torn down. After this point, there will be no more
        # factory stuff, just our own personal stuff.
        del self.factory

        if self.time_loop:
            self.time_loop.stop()

        if self.chunk_tasks:
            for task in self.chunk_tasks:
                try:
                    task.stop()
                except (TaskDone, TaskFailed):
                    pass

    # 'handshaking' packets first!
    def handle_handshaking(self, packet):
        if packet.protocol != SUPPORTED_PROTOCOL:
            self.error("This server does not support your client's protocol.")
            return ''
        if packet.next_state == 'status':
            self.mode = 'status'
        elif packet.next_state == 'login':
            self.mode = 'login'
        else:
            log.msg('unexpected next state value: %s' % packet.next_state)
        return ''

    def handle_encryption_response(self, packet):
        return NotImplementedError

    def handle_login_start(self, packet):
        self.username = packet.username
        self.uuid = uuid4()
        self.write_packet('login_success', uuid=self.uuid.bytes, username=self.username)
        self.authenticated()

    def handle_status_request(self, packet):
        version = '"version":{"name":"1.7.2","protocol":4}'
        description = '"description":{"text":"OMG Bravo!"}'
        if len(self.factory.protocols) > 0:
            samples = ',"sample":[' + ''.join(['{"id":"%s","name":"%s"}' % ('', name) for name in self.factory.protocols]) + ']'
        else:
            samples = ''
        players = '"players":{"max":%d,"online":%d%s}' % (self.factory.limitConnections, len(self.factory.protocols), samples)
        json_string = '{%s,%s,%s}' % (description, players, version)
        self.write_packet('status_response', json=json_string)

    def handle_status_ping(self, packet):
        self.write_packet('status_ping', time=packet.time)
        self.mode = 'handshaking'

    def handle_keepalive(self, packet):
        # JMT: this assumes the ping value is time related
        # wiki.vg/Protocol says different:
        # basically, server sends random ID, client returns same.
        now = timestamp_from_clock(reactor)
        then = packet.keepalive_id
        latency = now - then

    def handle_chat(self, packet):
        log.msg("Chat! %r" % packet.json)
        data = json.loads(packet.json)
        log.msg("Chat loaded: %s" % data)
        if data.startswith("/"):
            commands = retrieve_plugins(IChatCommand, factory=self.factory)
            # Register aliases.
            for plugin in commands.values():
                for alias in plugin.aliases:
                    commands[alias] = plugin

            params = data[1:].split(" ")
            command = params.pop(0).lower()

            if command and command in commands:
                def cb(iterable):
                    for line in iterable:
                        self.send_chat(line)

                def eb(error):
                    self.send_chat("Error: %s" % error.getErrorMessage())

                d = maybeDeferred(commands[command].chat_command,
                                  self.username, params)
                d.addCallback(cb)
                d.addErrback(eb)
            else:
                self.send_chat("Unknown command: %s" % command)
        else:
            # Send the message up to the factory to be chatified.
            message = "<%s> %s" % (self.username, data)
            self.factory.chat(message)

    def handle_use_entity(self, packet):
        nearby_players = self.factory.players_near(self.player, 4)
        for entity in chain(self.entities_near(4), nearby_players):
            if entity.eid == packet.target:
                for hook in self.use_hooks[entity.name]:
                    hook.use_hook(self.factory, self.player, entity, packet.mouse == 'left')
                break

    def _grounded(self, packet):
        self.location.grounded = bool(packet.grounded)

    def _position(self, packet):
        if self.state != STATE_LOCATED:
            log.msg("Ignoring unlocated position!")
            return

        old_position = self.location.pos
        position = Position.from_player(packet.position.x, packet.position.y, packet.position.z)
        altered = False

        dx, dy, dz = old_position - position
        if any(abs(d) >= 64 for d in (dx, dy, dz)):
            # Whoa, slow down there, cowboy. You're moving too fast. We're
            # gonna ignore this position change completely, because it's
            # either bogus or ignoring a recent teleport.
            altered = True
        else:
            self.location.pos = position
            self.location.stance = packet.position.stance

        # Santitize location. This handles safety boundaries, illegal stance,
        # etc.
        altered = self.location.clamp() or altered

        # If, for any reason, our opinion on where the client should be
        # located is different than theirs, force them to conform to our point
        # of view.
        if altered:
            log.msg("Not updating bogus position!")
            self.update_location()

        # If our position actually changed, fire the position change hook.
        if old_position != position:
            self.position_changed()

    def _orientation(self, packet):

        old_orientation = self.location.ori
        orientation = Orientation.from_degs(packet.orientation.rotation, packet.orientation.pitch)
        self.location.ori = orientation

        if old_orientation != orientation:
            self.orientation_changed()

    def handle_player(self, packet):
        self._grounded(packet)

    def handle_player_position(self, packet):
        self._position(packet)
        self._grounded(packet)

    def handle_player_look(self, packet):
        self._orientation(packet)
        self._grounded(packet)

    def handle_player_position_and_look(self, packet):
        self._position(packet)
        self._orientation(packet)
        self._grounded(packet)

    def handle_player_digging(self, packet):
        if packet.x == -1 and packet.z == -1 and packet.y == 255:
            # Lala-land dig packet. Discard it for now.
            return

        # Player drops currently holding item/block.
        if (packet.state == "dropped" and packet.face == "-y" and packet.x == 0 and packet.y == 0 and packet.z == 0):
            i = self.player.inventory
            holding = i.holdables[self.player.equipped]
            if holding:
                item_id, count, damage = holding
                if i.consume((item_id, damage), self.player.equipped):
                    dest = self.location.in_front_of(2)
                    coords = dest.pos._replace(y=dest.pos.y + 1)
                    self.factory.give(coords, (item_id, damage), 1)

                    # Re-send inventory.
                    packet = self.inventory.save_to_packet()
                    self.transport.write(packet)

                    # If no items in this slot are left, this player isn't
                    # holding an item anymore.
                    if i.holdables[self.player.equipped] is None:
                        packet = make_packet("entity_equipment",
                                             eid=self.player.eid,
                                             slot_no=0,
                                             slot=Slot()
                                             )
                        self.factory.broadcast_for_others(packet, self)
            return

        if packet.state == "shooting":
            self.shoot_arrow()
            return

        bigx, smallx, bigz, smallz = split_coords(packet.x, packet.z)
        coords = smallx, packet.y, smallz

        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't dig in chunk (%d, %d)!" % (bigx, bigz))
            return

        block = chunk.get_block((smallx, packet.y, smallz))

        if packet.state == "started":
            # Run pre dig hooks
            for hook in self.pre_dig_hooks:
                cancel = yield maybeDeferred(hook.pre_dig_hook, self.player,
                                             (packet.x, packet.y, packet.z), block)
                if cancel:
                    return

            tool = self.player.inventory.holdables[self.player.equipped]
            # Check to see whether we should break this block.
            if self.dig_policy.is_1ko(block, tool):
                self.run_dig_hooks(chunk, coords, blocks[block])
            else:
                # Set up a timer for breaking the block later.
                dtime = time() + self.dig_policy.dig_time(block, tool)
                self.last_dig = coords, block, dtime
        elif packet.state == "stopped":
            # The client thinks it has broken a block. We shall see.
            if not self.last_dig:
                return

            oldcoords, oldblock, dtime = self.last_dig
            if oldcoords != coords or oldblock != block:
                # Nope!
                self.last_dig = None
                return

            dtime -= time()

            # When enough time has elapsed, run the dig hooks.
            d = deferLater(reactor, max(dtime, 0), self.run_dig_hooks, chunk,
                           coords, blocks[block])
            d.addCallback(lambda none: setattr(self, "last_dig", None))

    def handle_player_block_placement(self, packet):
        # Is the target within our purview? We don't do a very strict
        # containment check, but we *do* require that the chunk be loaded.
        bigx, smallx, bigz, smallz = split_coords(packet.x, packet.z)
        try:
            chunk = self.chunks[bigx, bigz]
        except KeyError:
            self.error("Couldn't select in chunk (%d, %d)!" % (bigx, bigz))
            return

        target = blocks[chunk.get_block((smallx, packet.y, smallz))]

        # Attempt to open a window.
        from bravo.policy.windows import window_for_block
        window = window_for_block(target)
        if window is not None:
            # We have a window!
            self.windows[self.wid] = window
            identifier, title, slots = window.open()
            # JMT: no horse support
            self.write_packet('open_window', wid=self.wid, type=identifier, title=title, slots=slots, use_provided_title=True)
            self.wid += 1
            return

        # Try to open it first
        for hook in self.open_hooks:
            window = yield maybeDeferred(hook.open_hook, self, packet,
                                         chunk.get_block((smallx, packet.y, smallz)))
            if window:
                self.write_packet('open_window', wid=window.wid,
                                  type=window.identifier, title=window.title, slots=windows.slots_num, use_provided_title=True)
                packet = window.save_to_packet()
                self.transport.write(packet)
                # window opened
                return

        # Ignore clients that think -1 is placeable.
        if packet.item_id == -1:
            return

        # Special case when face is "noop": Update the status of the currently
        # held block rather than placing a new block.
        if packet.face == "noop":
            return

        # If the target block is vanishable, then adjust our aim accordingly.
        if target.vanishes:
            packet.face = "+y"
            packet.y -= 1

        if packet.item_id in blocks:
            block = blocks[packet.item_id]
        elif packet.item_id in items:
            block = items[packet.item_id]
        else:
            log.err("Ignoring request to place unknown block 0x%x" %
                    packet.item_id)
            return

        # Run pre-build hooks. These hooks are able to interrupt the build
        # process.
        builddata = BuildData(block, 0x0, packet.x, packet.y,
                              packet.z, packet.face)

        for hook in self.pre_build_hooks:
            cont, builddata, cancel = yield maybeDeferred(hook.pre_build_hook,
                                                          self.player, builddata)
            if cancel:
                # Flush damaged chunks.
                for chunk in self.chunks.itervalues():
                    self.factory.flush_chunk(chunk)
                return
            if not cont:
                break

        # Run the build.
        try:
            yield maybeDeferred(self.run_build, builddata)
        except BuildError:
            return

        newblock = builddata.block.slot
        coords = adjust_coords_for_face(
            (builddata.x, builddata.y, builddata.z), builddata.face)

        # Run post-build hooks. These are merely callbacks which cannot
        # interfere with the build process, largely because the build process
        # already happened.
        for hook in self.post_build_hooks:
            yield maybeDeferred(hook.post_build_hook, self.player, coords,
                                builddata.block)

        # Feed automatons.
        for automaton in self.factory.automatons:
            if newblock in automaton.blocks:
                automaton.feed(coords)

        # Re-send inventory.
        # XXX this could be optimized if/when inventories track damage.
        packet = self.inventory.save_to_packet()
        self.transport.write(packet)

        # Flush damaged chunks.
        for chunk in self.chunks.itervalues():
            self.factory.flush_chunk(chunk)

    def handle_held_item_change(self, packet):
        return NotImplementedError

    def handle_animate(self, packet):
        return NotImplementedError

    def handle_entity_action(self, packet):
        return NotImplementedError

    def handle_steer_vehicle(self, packet):
        return NotImplementedError

    def handle_close_window(self, packet):
        return NotImplementedError

    def handle_click_window(self, packet):
        return NotImplementedError

    def handle_confirm_transaction(self, packet):
        return NotImplementedError

    def handle_creative_inventory_action(self, packet):
        return NotImplementedError

    def handle_enchant_item(self, packet):
        return NotImplementedError

    def handle_update_sign(self, packet):
        return NotImplementedError

    def handle_player_abilities(self, packet):
        return NotImplementedError

    def handle_tab(self, packet):
        return NotImplementedError

    def handle_client_settings(self, packet):
        # JMT: The packet has more than the object
        self.settings.update_presentation(packet)

    def handle_client_status(self, packet):
        return NotImplementedError

    def handle_plugin_message(self, packet):
        print "Plugin!"
        print packet
