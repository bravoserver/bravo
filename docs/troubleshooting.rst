.. include:: globals.txt

===============
Troubleshooting
===============

Configuring
===========

*When I connect to the server, the client gets an "End of Stream" error and the
server log says something about "ConsoleRPCProtocol".*

 You are connecting to the wrong port.

 Bravo always runs an RPC console by default. This console isn't directly
 accessible from clients. In order to connect a client, you must configure a
 world and connect to that world. See the example bravo.ini configuration file
 for an example of how to configure a world.

*My world is snowy. I didn't want this.*

 In bravo.ini, change your ``seasons`` list to exclude winter. A possible
 incantation might be the following::

     seasons = *, -winter

Errors
======

*I get lots of RuntimeErrors from Exocet.*

 Upgrade to a newer Bravo which doesn't use Exocet.

*I have an error involving construct!*

 Install Construct. It is a required package.

*I have an error involving JSON!*

 If you update to a newer Bravo, you won't need JSON support.

*I have an error involving IRC/AMP/ListOf!*

 Your Twisted is too old. You really do need Twisted 11.0 or newer.

*I have an error ``TypeError: an integer is required`` when starting Bravo!*

 Your Twisted is too old. You *really* do need Twisted 11.0 or newer.

*I am running as root on a Unix system and twistd cannot find
``bravo.service``. What's going on?*

 For security reasons, twistd doesn't look in non-system directories as root.
 If you insist on running as root, try an incantation like the following,
 setting ``PYTHONPATH``::

     # PYTHONPATH=. twistd -n bravo

 But seriously, stop running as root.

Help!
=====

If you are having a hard time figuring something out, encountered a bug,
or have ideas, feel free to reach out to the community in one of several
different ways:

* **IRC:** #bravoserver on FreeNode
* Post to our `issue tracker`_.
* Speak up over our `mailing list`_.
