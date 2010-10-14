Minecraft Alpha Wire Protocol
=============================

This document is a brief but hopefully comprehensive guide to the basic wire
protocol used by Minecraft Alpha's server and client. This guide was
originally conceived as part of a project to reimplement the Alpha server, so
there is a definite bias towards the server's point of view.

It is the author's belief that, in the name of interoperability, this
document's distribution should be unlimited.

Overview
--------

Alpha uses a simple packet-based format. Packets are small, discrete chunks of
data meant to have strongly specified size and to be far smaller than the MTU
of the data connection. Packets are composed of a small identifying header and
a payload comprised of a number of simple primitives. No marshalling is
required, so packets may be parsed with no wire trust involved.

The packet's header is a single byte identifying the type of the packet. This
byte is called the **identifier**.

Ports
-----

Alpha listens on TCP port 25565.

Types
-----

String
^^^^^^

Alpha uses Java's UTF-8 string-packing system for strings, as detailed in the
official Java documentation at
http://download.oracle.com/javase/6/docs/api/java/io/DataInput.html. This
format is a length-prefixed string, using a single short to specify the value.
Strings have a length limit of 65335 characters.

Note: Strings may have embedded NULL bytes, as explained by the Java
documentation. It is recommended that implementations correctly handle these
NULL bytes in incoming strings, but not generate them in outgoing strings.

A lazy implementor could certainly get by with a simple length-prefixed string
parser, provided that they not forget to handle the characters as UTF-8.

Byte
^^^^

A 8-bit signed integer in network byte order. At least the official server
treats these as both signed and unsigned depending on the particular packet.

Short
^^^^^

A 16-bit signed integer in network byte order.

Int
^^^

A 32-bit signed integer in network byte order.

Long
^^^^

A 64-bit signed integer in network byte order.

Packets
-------

PingPacket (0x00)
^^^^^^^^^^^^^^^^^

No fields.

A simple keepalive mechanism that must be sent and received within certain
time intervals in order to keep the server from timing out the client or vice
versa.

LoginPacket (0x01)
^^^^^^^^^^^^^^^^^^

Fields:

 * version: integer
 * username: string
 * unknown: string

Identifies clients to the server. The server should reply with an empty
LoginPacket if successful (version 0, no username or unknown.)

The version of the client should be 2 for Alpha servers.

ChatPacket (0x03)
^^^^^^^^^^^^^^^^^

Fields:

 * message: string

Used to relay messages from the chat subsystem of the client.

SpawnPacket (0x06)
^^^^^^^^^^^^^^^^^^

Fields:

 * x: int
 * y: int
 * z: int

Specifies the spawn location of the currently loaded world.

ErrorPacket (0xff)
^^^^^^^^^^^^^^^^^^

Fields:

 * message: string

Used to deliver error messages to clients.
