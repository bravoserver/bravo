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

*I get lots of RuntimeErrors from Exocet while loading things like*

``bravo.parameters``, ``xml.sax``, and ``twisted.internet``.
 Those are harmless.

 Exocet is very, very strict about imports, and in fact, it is stricter than
 the standard importer. This means that Exocet will warn about modules which
 try to do weird or tricky things during imports. The warnings might be
 annoying, but they aren't indicative of anything going wrong.

*I have an error involving construct!*

 Install Construct.

*I have an error involving JSON!*

 If you update to a newer Bravo, you won't need JSON support.

*I have an error involving IRC/AMP/ListOf!*

 Your Twisted is too old. You really do need Twisted 10.1 or newer.

*I have an error ``TypeError: an integer is required`` when starting Bravo!*

 Is your Twisted 10.1 or older? This error could be caused by your Twisted not
 being 10.2 or newer.

*I am running as root on a Unix system and twistd cannot find
``bravo.service``. What's going on?*

 For security reasons, twistd doesn't look in non-system directories as root.
 If you insist on running as root, try an incantation like the following,
 setting ``PYTHONPATH``::

     # PYTHONPATH=. twistd -n bravo

Help!
=====

If you are having a hard time figuring something out, encountered a bug,
or have ideas, feel free to reach out to the community in one of several
different ways:

* **IRC:** #Bravo on FreeNode
* Post to our `issue tracker`_.
* Speak up over our `mailing list`_.