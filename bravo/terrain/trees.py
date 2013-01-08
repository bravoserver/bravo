from __future__ import division

from itertools import product
from math import cos, pi, sin, sqrt
from random import choice, random, randint

from zope.interface import Interface, implements

from bravo.blocks import blocks

PHI = (sqrt(5) - 1) * 0.5
IPHI = (sqrt(5) + 1) * 0.5
"""
Phi and inverse phi constants.
"""

# add lights in the middle of foliage clusters
# for those huge trees that get so dark underneath
# or for enchanted forests that should glow and stuff
# Only works if SHAPE is "round" or "cone" or "procedural"
# 0 makes just normal trees
# 1 adds one light inside the foliage clusters for a bit of light
# 2 adds two lights around the base of each cluster, for more light
# 4 adds lights all around the base of each cluster for lots of light
LIGHTTREE = 0

def dist_to_mat(cord, vec, matidxlist, world, invert=False, limit=None):
    """
    Find the distance from the given coordinates to any of a set of blocks
    along a certain vector.
    """

    curcord = [i + .5 for i in cord]
    iterations = 0
    on_map = True
    while on_map:
        x = int(curcord[0])
        y = int(curcord[1])
        z = int(curcord[2])
        if not 0 <= y < 128:
            break
        block = world.sync_get_block((x, y, z))

        if block in matidxlist and not invert:
            break
        elif block not in matidxlist and invert:
            break
        else:
            curcord = [curcord[i] + vec[i] for i in range(3)]
            iterations += 1
        if limit and iterations > limit:
            break
    return iterations

class ITree(Interface):
    """
    An ideal Platonic tree.

    Trees usually are made of some sort of wood, and are adorned with leaves.
    These trees also may have lanterns hanging in their branches.
    """

    def prepare(world):
        """
        Do any post-__init__() setup.
        """

    def make_trunk(world):
        """
        Write a trunk to the world.
        """

    def make_foliage(world):
        """
        Write foliage (leaves, lanterns) to the world.
        """

class Tree(object):
    """
    Set up the interface for tree objects.  Designed for subclassing.
    """

    implements(ITree)

    def __init__(self, pos, height=None):
        if height is None:
            self.height = randint(4, 7)
        else:
            self.height = height
        self.species = 0    # default to oak
        self.pos = pos

    def prepare(self, world):
        pass

    def make_trunk(self, world):
        pass

    def make_foliage(self, world):
        pass

class StickTree(Tree):
    """
    A large stick or log.

    Subclass this to build trees which only require a single-log trunk.
    """

    def make_trunk(self, world):
        x, y, z = self.pos
        for i in xrange(self.height):
            world.sync_set_block((x, y, z), blocks["log"].slot)
            world.sync_set_metadata((x, y, z), self.species)
            y += 1

class NormalTree(StickTree):
    """
    A Notchy tree.

    This tree will be a single bulb of foliage above a single width trunk.
    The shape is very similar to the default Minecraft tree.
    """

    def make_foliage(self, world):
        topy = self.pos[1] + self.height - 1
        start = topy - 2
        end = topy + 2
        for y in xrange(start, end):
            if y > start + 1:
                rad = 1
            else:
                rad = 2
            for xoff, zoff in product(xrange(-rad, rad + 1), repeat=2):
                if (random() > PHI and abs(xoff) == abs(zoff) == rad or
                       xoff == zoff == 0):
                    continue

                x = self.pos[0] + xoff
                z = self.pos[2] + zoff

                world.sync_set_block((x, y, z), blocks["leaves"].slot)
                world.sync_set_metadata((x, y, z), self.species)

class BambooTree(StickTree):
    """
    A bamboo-like tree.

    Bamboo foliage is sparse and always adjacent to the trunk.
    """

    def make_foliage(self, world):
        start = self.pos[1]
        end = start + self.height + 1
        for y in xrange(start, end):
            for i in (0, 1):
                xoff = choice([-1, 1])
                zoff = choice([-1, 1])
                x = self.pos[0] + xoff
                z = self.pos[2] + zoff
                world.sync_set_block((x, y, z), blocks["leaves"].slot)

class PalmTree(StickTree):
    """
    A traditional palm tree.

    This tree has four tufts of foliage at the top of the trunk.  No coconuts,
    though.
    """

    def make_foliage(self, world):
        y = self.pos[1] + self.height
        for xoff, zoff in product(xrange(-2, 3), repeat=2):
            if abs(xoff) == abs(zoff):
                x = self.pos[0] + xoff
                z = self.pos[2] + zoff
                world.sync_set_block((x, y, z), blocks["leaves"].slot)

class ProceduralTree(Tree):
    """
    Base class for larger, complex, procedurally generated trees.

    This tree type has roots, a trunk, branches all of varying width, and many
    foliage clusters.

    This class needs to be subclassed to be useful. Specifically,
    foliage_shape must be set.  Subclass 'prepare' and 'shapefunc' to make
    different shaped trees.
    """

    def cross_section(self, center, radius, diraxis, matidx, world):
        """Create a round section of type matidx in world.

        Passed values:
        center = [x,y,z] for the coordinates of the center block
        radius = <number> as the radius of the section.  May be a float or int.
        diraxis: The list index for the axis to make the section
        perpendicular to.  0 indicates the x axis, 1 the y, 2 the z.  The
        section will extend along the other two axies.
        matidx = <int> the integer value to make the section out of.
        world = the array generated by make_mcmap
        matdata = <int> the integer value to make the block data value.
        """

        rad = int(radius + PHI)
        if rad <= 0:
            return None
        secidx1 = (diraxis - 1) % 3
        secidx2 = (1 + diraxis) % 3
        coord = [0] * 3
        for off1, off2 in product(xrange(-rad, rad + 1), repeat=2):
            thisdist = sqrt((abs(off1) + .5)**2 + (abs(off2) + .5)**2)
            if thisdist > radius:
                continue
            pri = center[diraxis]
            sec1 = center[secidx1] + off1
            sec2 = center[secidx2] + off2
            coord[diraxis] = pri
            coord[secidx1] = sec1
            coord[secidx2] = sec2
            world.sync_set_block(coord, matidx)
            world.sync_set_metadata(coord, self.species)

    def shapefunc(self, y):
        """
        Obtain a radius for the given height.

        Subclass this method to customize tree design.

        If None is returned, no foliage cluster will be created.

        :returns: radius, or None
        """

        if random() < 100 / ((self.height)**2) and y < self.trunkheight:
            return self.height * .12
        return None

    def foliage_cluster(self, center, world):
        """
        Generate a round cluster of foliage at the location center.

        The shape of the cluster is defined by the list self.foliage_shape.
        This list must be set in a subclass of ProceduralTree.
        """

        x = center[0]
        y = center[1]
        z = center[2]
        for i in self.foliage_shape:
            self.cross_section([x, y, z], i, 1, blocks["leaves"].slot, world)
            y += 1

    def taperedcylinder(self, start, end, startsize, endsize, world, blockdata):
        """
        Create a tapered cylinder in world.

        start and end are the beginning and ending coordinates of form [x,y,z].
        startsize and endsize are the beginning and ending radius.
        The material of the cylinder is WOODMAT.
        """

        # delta is the coordinate vector for the difference between
        # start and end.
        delta = [int(e - s) for e, s in zip(end, start)]

        # primidx is the index (0,1,or 2 for x,y,z) for the coordinate
        # which has the largest overall delta.
        maxdist = max(delta, key=abs)
        if maxdist == 0:
            return None
        primidx = delta.index(maxdist)

        # secidx1 and secidx2 are the remaining indices out of [0,1,2].
        secidx1 = (primidx - 1) % 3
        secidx2 = (1 + primidx) % 3

        # primsign is the digit 1 or -1 depending on whether the limb is headed
        # along the positive or negative primidx axis.
        primsign = cmp(delta[primidx], 0) or 1

        # secdelta1 and ...2 are the amount the associated values change
        # for every step along the prime axis.
        secdelta1 = delta[secidx1]
        secfac1 = float(secdelta1)/delta[primidx]
        secdelta2 = delta[secidx2]
        secfac2 = float(secdelta2)/delta[primidx]
        # Initialize coord.  These values could be anything, since
        # they are overwritten.
        coord = [0] * 3
        # Loop through each crossection along the primary axis,
        # from start to end.
        endoffset = delta[primidx] + primsign
        for primoffset in xrange(0, endoffset, primsign):
            primloc = start[primidx] + primoffset
            secloc1 = int(start[secidx1] + primoffset*secfac1)
            secloc2 = int(start[secidx2] + primoffset*secfac2)
            coord[primidx] = primloc
            coord[secidx1] = secloc1
            coord[secidx2] = secloc2
            primdist = abs(delta[primidx])
            radius = endsize + (startsize-endsize) * abs(delta[primidx]
                                - primoffset) / primdist
            self.cross_section(coord, radius, primidx, blockdata, world)

    def make_foliage(self, world):
        """
        Generate the foliage for the tree in world.

        Also place lanterns.
        """

        foliage_coords = self.foliage_cords
        for coord in foliage_coords:
            self.foliage_cluster(coord,world)
        for x, y, z in foliage_coords:
            world.sync_set_block((x, y, z), blocks["log"].slot)
            world.sync_set_metadata((x, y, z), self.species)
            if LIGHTTREE == 1:
                world.sync_set_block((x, y + 1, z), blocks["lightstone"].slot)
            elif LIGHTTREE in [2,4]:
                world.sync_set_block((x + 1, y, z), blocks["lightstone"].slot)
                world.sync_set_block((x - 1, y, z), blocks["lightstone"].slot)
                if LIGHTTREE == 4:
                    world.sync_set_block((x, y, z + 1), blocks["lightstone"].slot)
                    world.sync_set_block((x, y, z - 1), blocks["lightstone"].slot)

    def make_branches(self, world):
        """Generate the branches and enter them in world.
        """
        treeposition = self.pos
        height = self.height
        topy = treeposition[1] + int(self.trunkheight + 0.5)
        # endrad is the base radius of the branches at the trunk
        endrad = max(self.trunkradius * (1 - self.trunkheight/height), 1)
        for coord in self.foliage_cords:
            dist = (sqrt(float(coord[0]-treeposition[0])**2 +
                            float(coord[2]-treeposition[2])**2))
            ydist = coord[1]-treeposition[1]
            # value is a magic number that weights the probability
            # of generating branches properly so that
            # you get enough on small trees, but not too many
            # on larger trees.
            # Very difficult to get right... do not touch!
            value = (self.branchdensity * 220 * height)/((ydist + dist) ** 3)
            if value < random():
                continue

            posy = coord[1]
            slope = self.branchslope + (0.5 - random()) * .16
            if coord[1] - dist*slope > topy:
                # Another random rejection, for branches between
                # the top of the trunk and the crown of the tree
                threshhold = 1 / height
                if random() < threshhold:
                    continue
                branchy = topy
                basesize = endrad
            else:
                branchy = posy-dist*slope
                basesize = (endrad + (self.trunkradius-endrad) *
                         (topy - branchy) / self.trunkheight)
            startsize = (basesize * (1 + random()) * PHI *
                         (dist/height)**PHI)
            if startsize < 1.0:
                startsize = 1.0
            rndr = sqrt(random()) * basesize * PHI
            rndang = random() * 2 * pi
            rndx = int(rndr*sin(rndang) + 0.5)
            rndz = int(rndr*cos(rndang) + 0.5)
            startcoord = [treeposition[0]+rndx,
                          int(branchy),
                          treeposition[2]+rndz]
            endsize = 1.0
            self.taperedcylinder(startcoord, coord, startsize, endsize, world,
                blocks["log"].slot)

    def make_trunk(self, world):
        """
        Make the trunk, roots, buttresses, branches, etc.
        """

        # In this method, x and z are the position of the trunk.
        x, starty, z = self.pos
        midy = starty + int(self.trunkheight / (PHI + 1))
        topy = starty + int(self.trunkheight + 0.5)
        end_size_factor = self.trunkheight / self.height
        endrad = max(self.trunkradius * (1 - end_size_factor), 1)
        midrad = max(self.trunkradius * (1 - end_size_factor * .5), endrad)

        # Make the lower and upper sections of the trunk.
        self.taperedcylinder([x,starty,z], [x,midy,z], self.trunkradius,
            midrad, world, blocks["log"].slot)
        self.taperedcylinder([x,midy,z], [x,topy,z], midrad, endrad, world,
            blocks["log"].slot)

        #Make the branches.
        self.make_branches(world)

    def prepare(self, world):
        """
        Initialize the internal values for the Tree object.

        Primarily, sets up the foliage cluster locations.
        """

        treeposition = self.pos
        self.trunkradius = PHI * sqrt(self.height)
        if self.trunkradius < 1:
            self.trunkradius = 1
        self.trunkheight = self.height
        yend = int(treeposition[1] + self.height)
        self.branchdensity = 1.0
        foliage_coords = []
        ystart = treeposition[1]
        num_of_clusters_per_y = int(1.5 + (self.height / 19)**2)
        if num_of_clusters_per_y < 1:
            num_of_clusters_per_y = 1
        # make sure we don't spend too much time off the top of the map
        if yend > 255:
            yend = 255
        if ystart > 255:
            ystart = 255
        for y in xrange(yend, ystart, -1):
            for i in xrange(num_of_clusters_per_y):
                shapefac = self.shapefunc(y - ystart)
                if shapefac is None:
                    continue
                r = (sqrt(random()) + .328)*shapefac

                theta = random()*2*pi
                x = int(r*sin(theta)) + treeposition[0]
                z = int(r*cos(theta)) + treeposition[2]

                foliage_coords += [[x,y,z]]

        self.foliage_cords = foliage_coords


class RoundTree(ProceduralTree):
    """
    A rounded deciduous tree.
    """

    branchslope = 1 / (PHI + 1)
    foliage_shape = [2, 3, 3, 2.5, 1.6]

    def prepare(self, world):
        self.species = 2 # birch wood
        ProceduralTree.prepare(self, world)
        self.trunkradius *= 0.8
        self.trunkheight *= 0.7

    def shapefunc(self, y):
        twigs = ProceduralTree.shapefunc(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.282 + .1 * sqrt(random())) :
            return None
        radius = self.height / 2
        adj = self.height / 2 - y
        if adj == 0 :
            dist = radius
        elif abs(adj) >= radius:
            dist = 0
        else:
            dist = sqrt((radius**2) - (adj**2))
        dist *= PHI
        return dist


class ConeTree(ProceduralTree):
    """
    A conifer.
    """

    branchslope = 0.15
    foliage_shape = [3, 2.6, 2, 1]

    def prepare(self, world):
        self.species = 1 # pine wood
        ProceduralTree.prepare(self, world)
        self.trunkradius *= 0.5

    def shapefunc(self, y):
        twigs = ProceduralTree.shapefunc(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.25 + .05 * sqrt(random())):
            return None

        # Radius.
        return max((self.height - y) / (PHI + 1), 0)

class RainforestTree(ProceduralTree):
    """
    A big rainforest tree.
    """
    branchslope = 1
    foliage_shape = [3.4, 2.6]

    def prepare(self, world):
        self.species = 3 # jungle wood
        # TODO: play with these numbers until jungles look right
        self.height = randint(10, 20)
        self.trunkradius = randint(5, 15)
        ProceduralTree.prepare(self, world)
        self.trunkradius /= PHI + 1
        self.trunkheight *= .9

    def shapefunc(self, y):
        # Bottom 4/5 of the tree is probably branch-free.
        if y < self.height * 0.8:
            twigs = ProceduralTree.shapefunc(self,y)
            if twigs is not None and random() < 0.07:
                return twigs
            return None
        else:
            width = self.height * 1 / (IPHI + 1)
            topdist = (self.height - y) / (self.height * 0.2)
            dist = width * (PHI + topdist) * (PHI + random()) * 1 / (IPHI + 1)
            return dist

class MangroveTree(RoundTree):
    """
    A mangrove tree.

    Like the round deciduous tree, but bigger, taller, and generally more
    awesome.
    """

    branchslope = 1

    def prepare(self, world):
        RoundTree.prepare(self, world)
        self.trunkradius *= PHI

    def shapefunc(self, y):
        val = RoundTree.shapefunc(self, y)
        if val is not None:
            val *= IPHI
        return val

    def make_roots(self, rootbases, world):
        """generate the roots and enter them in world.

        rootbases = [[x,z,base_radius], ...] and is the list of locations
        the roots can originate from, and the size of that location.
        """
        treeposition = self.pos
        height = self.height
        for coord in self.foliage_cords:
            # First, set the threshhold for randomly selecting this
            # coordinate for root creation.
            dist = (sqrt(float(coord[0]-treeposition[0])**2 +
                            float(coord[2]-treeposition[2])**2))
            ydist = coord[1]-treeposition[1]
            value = (self.branchdensity * 220 * height)/((ydist + dist) ** 3)
            # Randomly skip roots, based on the above threshold
            if value < random():
                continue
            # initialize the internal variables from a selection of
            # starting locations.
            rootbase = choice(rootbases)
            rootx = rootbase[0]
            rootz = rootbase[1]
            rootbaseradius = rootbase[2]
            # Offset the root origin location by a random amount
            # (radialy) from the starting location.
            rndr = sqrt(random()) * rootbaseradius * PHI
            rndang = random()*2*pi
            rndx = int(rndr*sin(rndang) + 0.5)
            rndz = int(rndr*cos(rndang) + 0.5)
            rndy = int(random()*rootbaseradius*0.5)
            startcoord = [rootx+rndx,treeposition[1]+rndy,rootz+rndz]
            # offset is the distance from the root base to the root tip.
            offset = [startcoord[i]-coord[i] for i in xrange(3)]
            # If this is a mangrove tree, make the roots longer.
            offset = [int(val * IPHI - 1.5) for val in offset]
            rootstartsize = (rootbaseradius * IPHI * abs(offset[1])/
                             (height * IPHI))
            rootstartsize = max(rootstartsize, 1.0)

    def make_trunk(self, world):
        """
        Make the trunk, roots, buttresses, branches, etc.
        """

        height = self.height
        trunkheight = self.trunkheight
        trunkradius = self.trunkradius
        treeposition = self.pos
        starty = treeposition[1]
        midy = treeposition[1]+int(trunkheight * 1 / (PHI + 1))
        topy = treeposition[1]+int(trunkheight + 0.5)
        # In this method, x and z are the position of the trunk.
        x = treeposition[0]
        z = treeposition[2]
        end_size_factor = trunkheight/height
        endrad = max(trunkradius * (1 - end_size_factor), 1)
        midrad = max(trunkradius * (1 - end_size_factor * .5), endrad)

        # The start radius of the trunk should be a little smaller if we
        # are using root buttresses.
        startrad = trunkradius * .8
        # rootbases is used later in self.makeroots(...) as
        # starting locations for the roots.
        rootbases = [[x,z,startrad]]
        buttress_radius = trunkradius * 0.382
        # posradius is how far the root buttresses should be offset
        # from the trunk.
        posradius = trunkradius
        # In mangroves, the root buttresses are much more extended.
        posradius = posradius * (IPHI + 1)
        num_of_buttresses = int(sqrt(trunkradius) + 3.5)
        for i in xrange(num_of_buttresses):
            rndang = random()*2*pi
            thisposradius = posradius * (0.9 + random()*.2)
            # thisx and thisz are the x and z position for the base of
            # the root buttress.
            thisx = x + int(thisposradius * sin(rndang))
            thisz = z + int(thisposradius * cos(rndang))
            # thisbuttressradius is the radius of the buttress.
            # Currently, root buttresses do not taper.
            thisbuttressradius = max(buttress_radius * (PHI + random()),
                1)
            # Make the root buttress.
            self.taperedcylinder([thisx, starty, thisz], [x, midy, z],
                thisbuttressradius, thisbuttressradius, world,
                blocks["log"].slot)
            # Add this root buttress as a possible location at
            # which roots can spawn.
            rootbases += [[thisx,thisz,thisbuttressradius]]

        # Make the lower and upper sections of the trunk.
        self.taperedcylinder([x,starty,z], [x,midy,z], startrad, midrad,
            world, blocks["log"].slot)
        self.taperedcylinder([x,midy,z], [x,topy,z], midrad, endrad, world,
            blocks["log"].slot)

        #Make the branches
        self.make_branches(world)
