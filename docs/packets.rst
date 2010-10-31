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

Array
^^^^^

A metatype consisting of a short followed by a number of items corresponding
to the value of that short. A length-prefixed list of data with no delimiters.

Packets
-------

Ping (0x00)
^^^^^^^^^^^

No fields.

A simple keep-alive mechanism that must be sent and received within certain
time intervals in order to keep the server from timing out the client or vice
versa.

Login (0x01)
^^^^^^^^^^^^

Fields:

 * version: integer
 * username: string
 * unknown: string
 * unknown: long
 * unknown: byte

Identifies clients to the server. The server should reply with an empty
Login if successful (version 0, no username or unknown.)

The version of the client should be 2 for Alpha servers.

Handshake (0x02)
^^^^^^^^^^^^^^^^

Fields:

 * username: string

Chat (0x03)
^^^^^^^^^^^

Fields:

 * message: string

Used to relay messages from the chat subsystem of the client.

Time (0x04)
^^^^^^^^^^^

Fields:

 * timestamp: long

A number from 0 to 24000 signifying the virtual time of day. This can be used
to synchronize the client's day/night mechanism.

Inventory (0x05)
^^^^^^^^^^^^^^^^

Fields:

 * unknown: int
 * items: array of...

   * id: short
   * count: byte (optional)
   * damage: short (optional)

A list of items in an inventory. The first unknown field corresponds to one of
the sub-inventory slottings; -1 is the main inventory of 36 items, -2 is the
crafting inventory of 4 items, and -3 is the armor inventory of 4 items. If an
inventory slot is empty, then the id should be negative and the count and
damage must be omitted from the bytestream. As this implies, the size of the
item struct is not constant.

Alpha servers always use -1 (0xffff) as the negative value; different clients
and servers may check for negative values, or for equality to -1, so using -1
is encouraged.

Spawn (0x06)
^^^^^^^^^^^^

Fields:

 * x: int
 * y: int
 * z: int

Specifies the spawn location of the currently loaded world. Clients require
this packet even if they intend to spawn at a previously saved location.

Flying (0x0a)
^^^^^^^^^^^^^

Fields:

 * flying: byte

The general-purpose acknowledgement packet, used by the client to alert the
server of its existence and intent to do things. Alpha clients dispatch five
to ten of these per second for no reason.

Position (0x0b)
^^^^^^^^^^^^^^^

Fields:

 * position: struct of...

   * x: double
   * y: double
   * stance: double
   * z: double
 * flying: byte

The client's location and stance. Stance is the center of gravity of the
player and may be between 0.1 and 1.65 greater than y depending on whether the
client is currently jumping. Stance must be between 0.1 and 1.65 on Alpha
servers, or the server will kick the client.

Look (0x0c)
^^^^^^^^^^^

Fields:

 * look: struct of...

   * rotation: float
   * pitch: float
 * flying: byte

Hopefully self-explanatory. I'll look at it more when I know more.

Location (0x0d)
^^^^^^^^^^^^^^^

Fields:

 * position
 * look
 * flying: byte

A position, look, and flying update, all at once. The client will only send
this once, at the beginning of the initial chunk exchange. The server needs to
send this to the client to start the client's rendering loop.

Error (0xff)
^^^^^^^^^^^^

Fields:

 * message: string

Used to deliver error messages to clients. The official client assumes that a
disconnection is impending when it receives this packet, and preemptively
closes the connection, so it should not be used for warnings or informational
messages.
