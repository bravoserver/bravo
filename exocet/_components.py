# -*- test-case-name: twisted.python.test.test_components -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Component architecture for Twisted, based on Zope3 components.

Using the Zope3 API directly is strongly recommended. Everything
you need is in the top-level of the zope.interface package, e.g.::

   from zope.interface import Interface, implements

   class IFoo(Interface):
       pass

   class Foo:
       implements(IFoo)

   print IFoo.implementedBy(Foo) # True
   print IFoo.providedBy(Foo()) # True

L{twisted.python.components.registerAdapter} from this module may be used to
add to Twisted's global adapter registry. 

L{twisted.python.components.proxyForInterface} is a factory for classes
which allow access to only the parts of another class defined by a specified
interface.
"""

# zope3 imports
from zope.interface import interface, declarations
from zope.interface.adapter import AdapterRegistry


# The global adapter registry of the modules package
globalRegistry = AdapterRegistry()

# Attribute that registerAdapter looks at. Is this supposed to be public?
ALLOW_DUPLICATES = 0

# Define a function to find the registered adapter factory, using either a
# version of Zope Interface which has the `registered' method or an older
# version which does not.
if getattr(AdapterRegistry, 'registered', None) is None:
    def _registered(registry, required, provided):
        """
        Return the adapter factory for the given parameters in the given
        registry, or None if there is not one.
        """
        return registry.get(required).selfImplied.get(provided, {}).get('')
else:
    def _registered(registry, required, provided):
        """
        Return the adapter factory for the given parameters in the given
        registry, or None if there is not one.
        """
        return registry.registered([required], provided)


def registerAdapter(adapterFactory, origInterface, *interfaceClasses):
    """Register an adapter class.

    An adapter class is expected to implement the given interface, by
    adapting instances implementing 'origInterface'. An adapter class's
    __init__ method should accept one parameter, an instance implementing
    'origInterface'.
    """
    self = globalRegistry
    assert interfaceClasses, "You need to pass an Interface"
    global ALLOW_DUPLICATES

    # deal with class->interface adapters:
    if not isinstance(origInterface, interface.InterfaceClass):
        origInterface = declarations.implementedBy(origInterface)

    for interfaceClass in interfaceClasses:
        factory = _registered(self, origInterface, interfaceClass)
        if factory is not None and not ALLOW_DUPLICATES:
            raise ValueError("an adapter (%s) was already registered." % (factory, ))
    for interfaceClass in interfaceClasses:
        self.register([origInterface], interfaceClass, '', adapterFactory)


def getAdapterFactory(fromInterface, toInterface, default):
    """Return registered adapter for a given class and interface.

    Note that is tied to the *Twisted* global registry, and will
    thus not find adapters registered elsewhere.
    """
    self = globalRegistry
    if not isinstance(fromInterface, interface.InterfaceClass):
        fromInterface = declarations.implementedBy(fromInterface)
    factory = self.lookup1(fromInterface, toInterface)
    if factory is None:
        factory = default
    return factory


# add global adapter lookup hook for our newly created registry
def _hook(iface, ob, lookup=globalRegistry.lookup1):
    factory = lookup(declarations.providedBy(ob), iface)
    if factory is None:
        return None
    else:
        return factory(ob)
interface.adapter_hooks.append(_hook)


def getRegistry():
    """Returns the Twisted global
    C{zope.interface.adapter.AdapterRegistry} instance.
    """
    return globalRegistry


__all__ = [
    # Sticking around:
    "registerAdapter", "getAdapterFactory",
    "getRegistry",
]
