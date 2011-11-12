""" Utilities for ai/pathfinding routines"""
from math import sin, cos, floor, ceil
from bravo.simplex import dot3

def check_collision(vector, offsetlist, factory):
    cont = True
    for offset_x, offset_y, offset_z in offsetlist:
        calculated_x = vector[0] + offset_x
        calculated_y = vector[1] + offset_y
        calculated_z = vector[2] + offset_z

        if calculated_x >= 0:
            calculated_x = floor(calculated_x)
        else:
            calculated_x = ceil(calculated_x)

        if calculated_y >= 0:
            calculated_y = floor(calculated_y)
        else:
            calculated_y = ceil(calculated_y)

        if calculated_z >= 0:
            calculated_z = floor(calculated_z)
        else:
            calculated_z = ceil(calculated_z)

        b = factory.world.sync_get_block((calculated_x,calculated_y,calculated_z))
        if b == 0:
            continue
        else:
            return False
            cont = False
            break
    if cont:
        return True

def rotate_coords_list(coords, theta, offset):
    """ Rotates a list of coordinates counterclockwise by the specified degree
        the add variables are there for convenience to allow one to give an
        offset list as the coords and an actual position as the add variables"""
    rotated_list = list()
    x_offset, chaff, z_offset = offset
    cosine = cos(theta)
    sine = sin(theta)
    for x, y, z in coords:
        calculated_z = z + z_offset
        calculated_x = x + x_offset
        rotated_x = calculated_x * cosine - calculated_z * sine
        rotated_z = calculated_x * sine + calculated_z * cosine
        rotated_list.append((rotated_x, y, rotated_z))

def slide_collision_vector(vector,normal):
    """ Returns a vector that allows an entity to slide along blocks."""
    dot = dot3(vector,(-normal[0], -normal[1], -normal[2]))
    return (vector[0] + (normal[0] * dot),
            vector[1] + (normal[1] * dot),
            vector[2] + (normal[2] * dot))
