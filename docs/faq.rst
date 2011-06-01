===
FAQ
===

Why are you doing this? What's wrong with the official Alpha server?
 Plenty. The biggest architectural mistake is the choice of dozens of threads
 instead of NIO and an asynchronous event-driven model, but there are other
 problems as well.

Are you implying that the official Alpha server is bad?
 Yes. As previous versions of this FAQ have stated, Notch is a cool guy, but
 the official server is bad.

Are you going to make an open-source client? That would be awesome!
 The server is free, but the client is not. Accordingly, we are not pursuing
 an open-source client at this time. If you want to play Alpha, you should pay
 for it. There's already enough Minecraft piracy going on; we don't feel like
 being part of the problem. That said, Bravo's packet parser and networking
 tools could be used in a client; the license permits it, after all.

Where did the docs go?
 We contribute to the Minecraft Collective's wiki at
 http://mc.kev009.com/wiki/ now, since it allows us to share data faster. All
 general Minecraft data goes to that wiki. Bravo-specific docs are shipped in
 ReST form, and a processed Sphinx version is available online at
 http://www.docs.bravoserver.org/.

Why did you make design decision <X>?
 There's an entire page dedicated to this in the documentation. Look at
 docs/philosophy.rst or http://www.docs.bravoserver.org/philosophy.html.

It doesn't install? Okay, maybe it installed, but I'm having issues!
 On Freenode IRC (irc.freenode.net), #bravo is dedicated to Bravo development
 and assistance, and #mcdevs is a more general channel for all custom
 Minecraft development. You can generally get help from those channels. If you
 think you have found a bug, you can directly report it on the Github issue
 tracker as well.

 Please, please, please read the installation instructions first, as well as
 the comments in bravo.ini.example. I did not type them out so that they could
 be ignored. :3

I have an error involving construct!
 Install Construct.

I have an error involving JSON!
 If you update to a newer Bravo, you won't need JSON support.

I have an error involving IRC/AMP/ListOf/endpoints!
 Your Twisted is too old. You really do need Twisted 10.1 or newer.

Who are you guys, anyway?
 Corbin Simpson (MostAwesomeDude) is the main coder. Derrick Dymock (Ac-town)
 is the visionary and provider of network traffic dumps. Ben Kero and Mark
 Harris are the reluctant testers and bug-reporters. The Minecraft Coalition
 has been an invaluable forum for discussion.
