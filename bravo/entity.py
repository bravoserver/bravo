from random import uniform

from twisted.internet.task import LoopingCall
from twisted.python import log

from bravo.inventory import Inventory
from bravo.inventory.slots import ChestStorage, FurnaceStorage
from bravo.location import Location
from bravo.beta.packets import make_packet
from bravo.utilities.geometry import gen_close_point
from bravo.utilities.maths import clamp
from bravo.utilities.furnace import (furnace_recipes, furnace_on_off,
    update_all_windows_slot, update_all_windows_progress)
from bravo.blocks import furnace_fuel, unstackable

class Entity(object):
    """
    Class representing an entity.

    Entities are simply dynamic in-game objects. Plain entities are not very
    interesting.
    """

    name = "Entity"

    def __init__(self, location=None, eid=0, **kwargs):
        """
        Create an entity.

        This method calls super().
        """

        super(Entity, self).__init__()

        self.eid = eid

        if location is None:
            self.location = Location()
        else:
            self.location = location

    def __repr__(self):
        return "%s(eid=%d, location=%s)" % (self.name, self.eid, self.location)

    __str__ = __repr__

class Player(Entity):
    """
    A player entity.
    """

    name = "Player"

    def __init__(self, username="", **kwargs):
        """
        Create a player.

        This method calls super().
        """

        super(Player, self).__init__(**kwargs)

        self.username = username
        self.inventory = Inventory()

        self.equipped = 0

    def __repr__(self):
        return ("%s(eid=%d, location=%s, username=%s)" %
                (self.name, self.eid, self.location, self.username))

    __str__ = __repr__

    def save_to_packet(self):
        """
        Create a "player" packet representing this entity.
        """

        yaw, pitch = self.location.ori.to_fracs()
        x, y, z = self.location.pos

        item = self.inventory.holdables[self.equipped]
        if item is None:
            item = 0
        else:
            item = item[0]

        packet = make_packet("player", eid=self.eid, username=self.username,
                             x=x, y=y, z=z, yaw=yaw, pitch=pitch, item=item,
                             metadata={})
        return packet

    def save_equipment_to_packet(self):
        """
        Creates packets that include the equipment of the player. Equipment
        is the item the player holds and all 4 armor parts.
        """

        packet = ""
        slots = (self.inventory.holdables[self.equipped],
                 self.inventory.armor[3], self.inventory.armor[2],
                 self.inventory.armor[1], self.inventory.armor[0])

        for slot, item in enumerate(slots):
            if item is None:
                continue

            primary, secondary, count = item
            packet += make_packet("entity-equipment", eid=self.eid, slot=slot,
                                  primary=primary, secondary=secondary,
                                  count=1)
        return packet

class Painting(Entity):
    """
    A painting on a wall.
    """

    name = "Painting"

    def __init__(self, face="+x", motive="", **kwargs):
        """
        Create a painting.

        This method calls super().
        """

        super(Painting, self).__init__(**kwargs)

        self.face = face
        self.motive = motive

    def save_to_packet(self):
        """
        Create a "painting" packet representing this entity.
        """

        x, y, z = self.location.pos

        return make_packet("painting", eid=self.eid, title=self.motive, x=x,
                y=y, z=z, face=self.face)

class Pickup(Entity):
    """
    Class representing a dropped block or item.

    For historical and sanity reasons, this class is called Pickup, even
    though its entity name is "Item."
    """

    name = "Item"

    def __init__(self, item=(0, 0), quantity=1, **kwargs):
        """
        Create a pickup.

        This method calls super().
        """

        super(Pickup, self).__init__(**kwargs)

        self.item = item
        self.quantity = quantity

    def save_to_packet(self):
        """
        Create a "pickup" packet representing this entity.
        """

        x, y, z = self.location.pos

        return ""

        return make_packet("pickup", eid=self.eid, primary=self.item[0],
                secondary=self.item[1], count=self.quantity, x=x, y=y, z=z,
                yaw=0, pitch=0, roll=0)

class Mob(Entity):
    """
    A creature.
    """

    name = "Mob"
    """
    The name of this mob.

    Names are used to identify mobs during serialization, just like for all
    other entities.

    This mob might not be serialized if this name is not overriden.
    """

    metadata = {0: ("byte", 0)}

    def __init__(self, **kwargs):
        """
        Create a mob.

        This method calls super().
        """

        self.loop = None
        super(Mob, self).__init__(**kwargs)
        self.manager = None

    def update_metadata(self):
        """
        Overrideable hook for general metadata updates.

        This method is necessary because metadata generally only needs to be
        updated prior to certain events, not necessarily in response to
        external events.

        This hook will always be called prior to saving this mob's data for
        serialization or wire transfer.
        """

    def run(self):
        """
        Start this mob's update loop.
        """

        # Save the current chunk coordinates of this mob. They will be used to
        # track which chunk this mob belongs to.
        self.chunk_coords = self.location.pos

        self.loop = LoopingCall(self.update)
        self.loop.start(.2)

    def save_to_packet(self):
        """
        Create a "mob" packet representing this entity.
        """

        x, y, z = self.location.pos
        yaw, pitch = self.location.ori.to_fracs()

        # Update metadata from instance variables.
        self.update_metadata()

        return make_packet("mob", eid=self.eid, type=self.name, x=x, y=y, z=z,
                yaw=yaw, pitch=pitch, head_yaw=yaw, vx=0, vy=0, vz=0,
                metadata=self.metadata)

    def save_location_to_packet(self):
        x, y, z = self.location.pos
        yaw, pitch = self.location.ori.to_fracs()

        return make_packet("teleport", eid=self.eid, x=x, y=y, z=z, yaw=yaw,
                pitch=pitch)

    def update(self):
        """
        Update this mob's location with respect to a factory.
        """

        # XXX  Discuss appropriate style with MAD
        # XXX remarkably untested
        player = self.manager.closest_player(self.location.pos, 16)

        if player is None:
            vector = (uniform(-.4,.4),
                      uniform(-.4,.4),
                      uniform(-.4,.4))

            target = self.location.pos + vector
        else:
            target = player.location.pos

            self_pos = self.location.pos
            vector = gen_close_point(self_pos, target)

            vector = (
                clamp(vector[0], -0.4, 0.4),
                clamp(vector[1], -0.4, 0.4),
                clamp(vector[2], -0.4, 0.4),
            )

        new_position = self.location.pos + vector

        new_theta = self.location.pos.heading(new_position)
        self.location.ori = self.location.ori._replace(theta=new_theta)

        # XXX explain these magic numbers please
        can_go = self.manager.check_block_collision(self.location.pos,
                (-10, 0, -10), (16, 32, 16))

        if can_go:
            self.slide = False
            self.location.pos = new_position

            self.manager.correct_origin_chunk(self)
            self.manager.broadcast(self.save_location_to_packet())
        else:
            self.slide = self.manager.slide_vector(vector)
            self.manager.broadcast(self.save_location_to_packet())


class Chuck(Mob):
    """
    A cross between a duck and a chicken.
    """

    name = "Chicken"
    offsetlist = ((.5, 0, .5),
            (-.5, 0, .5),
            (.5, 0, -.5),
            (-.5, 0, -.5))

class Cow(Mob):
    """
    Large, four-legged milk containers.
    """

    name = "Cow"

class Creeper(Mob):
    """
    A creeper.
    """

    name = "Creeper"

    def __init__(self, aura=False, **kwargs):
        """
        Create a creeper.

        This method calls super()
        """

        super(Creeper, self).__init__(**kwargs)

        self.aura = aura

    def update_metadata(self):
        self.metadata = {
            0: ("byte", 0),
            17: ("byte", int(self.aura)),
        }

class Ghast(Mob):
    """
    A very melancholy ghost.
    """

    name = "Ghast"

class GiantZombie(Mob):
    """
    Like a regular zombie, but far larger.
    """

    name = "GiantZombie"

class Pig(Mob):
    """
    A provider of bacon and piggyback rides.
    """

    name = "Pig"

    def __init__(self, saddle=False, **kwargs):
        """
        Create a pig.

        This method calls super().
        """

        super(Pig, self).__init__(**kwargs)

        self.saddle = saddle

    def update_metadata(self):
        self.metadata = {
            0: ("byte", 0),
            16: ("byte", int(self.saddle)),
        }

class ZombiePigman(Mob):
    """
    A zombie pigman.
    """

    name = "PigZombie"

class Sheep(Mob):
    """
    A woolly mob.
    """

    name = "Sheep"

    def __init__(self, sheared=False, color=0, **kwargs):
        """
        Create a sheep.

        This method calls super().
        """

        super(Sheep, self).__init__(**kwargs)

        self.sheared = sheared
        self.color = color

    def update_metadata(self):
        color = self.color
        if self.sheared:
            color |= 0x10

        self.metadata = {
            0: ("byte", 0),
            16: ("byte", color),
        }

class Skeleton(Mob):
    """
    An archer skeleton.
    """

    name = "Skeleton"

class Slime(Mob):
    """
    A gelatinous blob.
    """

    name = "Slime"

    def __init__(self, size=1, **kwargs):
        """
        Create a slime.

        This method calls super().
        """

        super(Slime, self).__init__(**kwargs)

        self.size = size

    def update_metadata(self):
        self.metadata = {
            0: ("byte", 0),
            16: ("byte", self.size),
        }

class Spider(Mob):
    """
    A spider.
    """

    name = "Spider"

class Squid(Mob):
    """
    An aquatic source of ink.
    """

    name = "Squid"

class Wolf(Mob):
    """
    A wolf.
    """

    name = "Wolf"

    def __init__(self, owner=None, angry=False, sitting=False, **kwargs):
        """
        Create a wolf.

        This method calls super().
        """

        super(Wolf, self).__init__(**kwargs)

        self.owner = owner
        self.angry = angry
        self.sitting = sitting

    def update_metadata(self):
        flags = 0
        if self.sitting:
            flags |= 0x1
        if self.angry:
            flags |= 0x2
        if self.owner:
            flags |= 0x4

        self.metadata = {
            0: ("byte", 0),
            16: ("byte", flags),
        }

class Zombie(Mob):
    """
    A zombie.
    """

    name = "Zombie"
    offsetlist = ((-.5,0,-.5), (-.5,0,.5), (.5,0,-.5), (.5,0,.5), (-.5,1,-.5), (-.5,1,.5), (.5,1,-.5), (.5,1,.5),)

entities = dict((entity.name, entity)
    for entity in (
        Chuck,
        Cow,
        Creeper,
        Ghast,
        GiantZombie,
        Painting,
        Pickup,
        Pig,
        Player,
        Sheep,
        Skeleton,
        Slime,
        Spider,
        Squid,
        Wolf,
        Zombie,
        ZombiePigman,
    )
)

class Tile(object):
    """
    An entity that is also a block.

    Or, perhaps more correctly, a block that is also an entity.
    """

    name = "GenericTile"

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def load_from_packet(self, container):

        log.msg("%s doesn't know how to load from a packet!" % self.name)

    def save_to_packet(self):

        log.msg("%s doesn't know how to save to a packet!" % self.name)

        return ""

class Chest(Tile):
    """
    A tile that holds items.
    """

    name = "Chest"

    def __init__(self, *args, **kwargs):
        super(Chest, self).__init__(*args, **kwargs)

        self.inventory = ChestStorage()

class Furnace(Tile):
    """
    A tile that converts items to other items, using specific items as fuel.
    """

    name = "Furnace"

    burntime = 0
    cooktime = 0
    running = False

    def __init__(self, *args, **kwargs):
        super(Furnace, self).__init__(*args, **kwargs)

        self.inventory = FurnaceStorage()
        self.burning = LoopingCall.withCount(self.burn)

    def changed(self, factory, coords):
        '''
        Called from outside by event handler to inform the tile
        that the content was changed. If the furnace meet the requirements
        the method starts ``burn`` process. The ``burn`` stops the
        looping call when it's out of fuel or no need to burn more.

        We get furnace coords from outer side as the tile does not know
        about own chunk. If self.chunk is implemented the parameter
        can be removed and self.coords will be:

        >>> self.coords = self.chunk.x, self.x, self.chunk.z, self.z, self.y

        :param `BravoFactory` factory: The factory
        :param tuple coords: (bigx, smallx, bigz, smallz, y) - coords of this furnace
        '''

        self.coords = coords
        self.factory = factory

        if not self.running:
            if self.burntime != 0:
                # This furnace was already burning, but not started. This
                # usually means that the furnace was serialized while burning.
                self.running = True
                self.burn_max = self.burntime
                self.burning.start(0.5)
            elif self.has_fuel() and self.can_craft():
                # This furnace could be burning, but isn't. Let's start it!
                self.burntime = 0
                self.cooktime = 0
                self.burning.start(0.5)

    def burn(self, ticks):
        '''
        The main furnace loop.

        :param int ticks: number of furnace iterations to perform
        '''

        # Usually it's only one iteration but if something blocks the server
        # for long period we shall process skipped ticks.
        # Note: progress bars will lag anyway.
        if ticks > 1:
            log.msg("Lag detected; skipping %d furnace ticks" % (ticks - 1))

        for iteration in xrange(ticks):
            # Craft items, if we can craft them.
            if self.can_craft():
                self.cooktime += 1

                # Notchian time is ~9.25-9.50 sec.
                if self.cooktime == 20:
                    # Looks like things were successfully crafted.
                    source = self.inventory.crafting[0]
                    product = furnace_recipes[source.primary]
                    self.inventory.crafting[0] = source.decrement()

                    if self.inventory.crafted[0] is None:
                        self.inventory.crafted[0] = product
                    else:
                        item = self.inventory.crafted[0]
                        self.inventory.crafted[0] = item.increment(product.quantity)

                    update_all_windows_slot(self.factory, self.coords, 0, self.inventory.crafting[0])
                    update_all_windows_slot(self.factory, self.coords, 2, self.inventory.crafted[0])
                    self.cooktime = 0
            else:
                self.cooktime = 0

            # Consume fuel, if applicable.
            if self.burntime == 0:
                if self.has_fuel() and self.can_craft():
                    # We have fuel and stuff to craft, so burn a bit of fuel
                    # and craft some stuff.
                    fuel = self.inventory.fuel[0]
                    self.burntime = self.burn_max = furnace_fuel[fuel.primary]
                    self.inventory.fuel[0] = fuel.decrement()

                    if not self.running:
                        self.running = True
                        furnace_on_off(self.factory, self.coords, True)

                    update_all_windows_slot(self.factory, self.coords, 1, self.inventory.fuel[0])
                else:
                    # We're finished burning. Turn ourselves off.
                    self.burning.stop()
                    self.running = False
                    furnace_on_off(self.factory, self.coords, False)

                    # Reset the cooking time, just because.
                    self.cooktime = 0
                    update_all_windows_progress(self.factory, self.coords, 0, 0)
                    return

            self.burntime -= 1

        # Update progress bars for the window.
        # XXX magic numbers
        cook_progress = 185 * self.cooktime / 19
        burn_progress = 250 * self.burntime / self.burn_max
        update_all_windows_progress(self.factory, self.coords, 0, cook_progress)
        update_all_windows_progress(self.factory, self.coords, 1, burn_progress)

    def has_fuel(self):
        '''
        Determine whether this furnace is fueled.

        :returns: bool
        '''

        return (self.inventory.fuel[0] is not None and
                self.inventory.fuel[0].primary in furnace_fuel)

    def can_craft(self):
        '''
        Determine whether this furnace is capable of outputting items.

        Note that this is independent of whether the furnace is fueled.

        :returns: bool
        '''

        crafting = self.inventory.crafting[0]
        crafted = self.inventory.crafted[0]

        # Nothing to craft?
        if crafting is None:
            return False

        # No matching recipe?
        if crafting.primary not in furnace_recipes:
            return False

        # Something to craft and no current output? This is a success
        # condition.
        if crafted is None:
            return True

        # Unstackable output?
        if crafted.primary in unstackable:
            return False

        recipe = furnace_recipes[crafting.primary]

        # Recipe doesn't match current output?
        if recipe[0] != crafted.primary:
            return False

        # Crafting would overflow current output?
        if crafted.quantity + recipe.quantity > 64:
            return False

        # By default, yes, you can craft.
        return True

class MobSpawner(Tile):
    """
    A tile that spawns mobs.
    """

    name = "MobSpawner"

class Music(Tile):
    """
    A tile which produces a pitch when whacked.
    """

    name = "Music"

class Sign(Tile):
    """
    A tile that stores text.
    """

    name = "Sign"

    def __init__(self, *args, **kwargs):
        super(Sign, self).__init__(*args, **kwargs)

        self.text1 = ""
        self.text2 = ""
        self.text3 = ""
        self.text4 = ""

    def load_from_packet(self, container):
        self.x = container.x
        self.y = container.y
        self.z = container.z

        self.text1 = container.line1
        self.text2 = container.line2
        self.text3 = container.line3
        self.text4 = container.line4

    def save_to_packet(self):
        packet = make_packet("sign", x=self.x, y=self.y, z=self.z,
            line1=self.text1, line2=self.text2, line3=self.text3,
            line4=self.text4)
        return packet

tiles = dict((tile.name, tile)
    for tile in (
        Chest,
        Furnace,
        MobSpawner,
        Music,
        Sign,
    )
)
