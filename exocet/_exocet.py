# -*- test-case-name: exocet.test.test_exocet -*-
# Copyright (c) 2010-2011 Allen Short. See LICENSE file for details.


import sys, __builtin__, itertools, traceback
from exocet._modules import getModule
from types import ModuleType
from zope.interface import Interface, implements

DEBUG = False
_sysModulesSpecialCases = {
    "os": ['path'],
    "twisted.internet": ["reactor"],
}

def trace(*args):
    if DEBUG:
        print ' '.join(str(x) for x in args)


class IMapper(Interface):
    """
    An object that maps names used in C{import} statements to objects (such as
    modules).
    """

    def lookup(name):
        """
        Return a boolean indicating whether this name can be resolved
        sucessfully by this mapper.
        """


    def contains(name):
        """
        Return a boolean indicating whether this name can be resolved
        sucessfully by this mapper.
        """


    def withOverrides(overrides):
        """
        Create a new mapper based on this one, with the mappings provided
        overriding existing names.
        """


class CallableMapper(object):
    """
    A mapper based on a callable that returns a module or raises C{ImportError}.
    """
    implements(IMapper)
    def __init__(self, baseLookup):
        self._baseLookup = baseLookup


    def lookup(self, name):
        """
        Call our callable to do lookup.
        @see L{IMapper.lookup}
        """
        try:
            return self._baseLookup(name)
        except ImportError:
            raise ImportError("No module named %r in mapper %r" % (name, self))


    def contains(self, name):
        """
        @see L{IMapper.contains}
        """
        try:
            self.lookup(name)
            return True
        except ImportError:
            return False


    def withOverrides(self, overrides):
        """
        @see L{IMapper.withOverrides}
        """
        return _StackedMapper([DictMapper(overrides), self])


class DictMapper(object):
    """
    A mapper that looks up names in a dictionary or other mapping.
    """
    implements(IMapper)
    def __init__(self, _dict):
        self._dict = _dict


    def lookup(self, name):
        """
        @see L{IMapper.lookup}
        """
        if name in self._dict:
            return self._dict[name]
        else:
            raise ImportError("No module named %r in mapper %r" % (name, self))


    def contains(self, name):
        """
        @see L{IMapper.contains}
        """
        return name in self._dict


    def withOverrides(self, overrides):
        """
        @see L{IMapper.withOverrides}
        """
        return _StackedMapper([DictMapper(overrides), self])



class _StackedMapper(object):
    """
    A mapper that consults multiple other mappers, in turn.
    """

    def __init__(self, submappers):
        self._submappers = submappers


    def lookup(self, name):
        """
        @see L{IMapper.lookup}
        """
        for m in self._submappers:
            try:
                val = m.lookup(name)
                break
            except ImportError, e:
                continue
        else:
            raise e
        return val

    def contains(self, name):
        """
        @see L{IMapper.contains}
        """
        try:
            self.lookup(name)
            return True
        except ImportError:
            return False


    def withOverrides(self, overrides):
        """
        @see L{IMapper.withOverrides}
        """
        return _StackedMapper([DictMapper(overrides), self])



class ExclusiveMapper(object):
    """
    A mapper that wraps another mapper, but excludes certain names.

    This mapper can be used to implement a blacklist.
    """

    implements(IMapper)

    def __init__(self, submapper, excluded):
        self._submapper = submapper
        self._excluded = excluded


    def lookup(self, name):
        """
        @see l{Imapper.lookup}
        """

        if name in self._excluded:
            raise ImportError("Module %s blacklisted in mapper %s"
                % (name, self))
        return self._submapper.lookup(name)


    def contains(self, name):
        """
        @see l{Imapper.contains}
        """

        if name in self._excluded:
            return False
        return self._submapper.contains(name)


    def withOverrides(self, overrides):
        """
        @see L{IMapper.withOverrides}
        """
        return _StackedMapper([DictMapper(overrides), self])



class _PackageMapper(CallableMapper):
    """
    A mapper that allows direct mutation as a result of intrapackage
    imports. For internal use only. Void where prohibited. If symptoms
    persist, see a professional.
    """
    implements(IMapper)
    def __init__(self, name, baseMapper):
        self._name = name
        self._baseMapper = baseMapper
        self._intrapackageImports = {}


    def _baseLookup(self, name):
        if name in self._intrapackageImports:
            return self._intrapackageImports[name]
        else:
            return self._baseMapper.lookup(name)


    def add(self, name, module):
        """
        Add an intrapackage import.
        """
        #if not name.startswith(self._name):
        #    raise ValueError("%r is not a member of the %r package" %
        #                     (name, self._name))
        self._intrapackageImports[name] = module



def _noLookup(name):
    raise ImportError(name)

class _PEP302Mapper(CallableMapper):
    """
    Mapper that uses Python's default import mechanism to load modules.

    @cvar _oldSysModules: Set by L{_isolateImports} when clearing
    L{sys.modules} to its former contents.
    """

    _oldSysModules = {}

    def __init__(self):
        self._metaPath = list(sys.meta_path)


    def _baseLookup(self, name):
        try:
            prevImport = __import__
            prevMetaPath = list(sys.meta_path)
            prevSysModules = sys.modules.copy()
            __builtin__.__import__ = prevImport
            sys.meta_path[:] = self._metaPath
            sys.modules.clear()
            sys.modules.update(self._oldSysModules)
            topLevel = _originalImport(name)
            trace("pep302Mapper imported %r as %r@%d" % (name, topLevel, id(topLevel)))
            packages = name.split(".")[1:]
            m = topLevel
            trace("subelements:", packages)
            for p in packages:
                trace("getattr", m, p)
                m = getattr(m, p)
            trace("done:", m, id(m))
            return m
        finally:
            self._oldSysModules.update(sys.modules)
            sys.meta_path[:] = prevMetaPath
            sys.modules.clear()
            sys.modules.update(prevSysModules)
            __builtin__.__import__ = prevImport


emptyMapper = CallableMapper(_noLookup)
pep302Mapper = _PEP302Mapper()

def lookupWithMapper(mapper, fqn):
    """
    Look up a FQN in a mapper, logging all non-ImportError exceptions and
    converting them to ImportErrors.
    """
    try:
        return mapper.lookup(fqn)
    except ImportError, e:
        raise e
    except:
        print "Error raised by Exocet mapper while loading %r" % (fqn)
        traceback.print_exc()
        raise ImportError(fqn)

class MakerFinder(object):
    """
    The object used as Exocet's PEP 302 meta-import hook. 'import' statements
    result in calls to find_module/load_module. A replacement for the
    C{__import__} function is provided as a method, as well.

    @ivar mapper: A L{Mapper}.

    @ivar oldImport: the implementation of C{__import__} being wrapped by this
                     object's C{xocImport} method.
    """
    def __init__(self, oldImport, mapper):
        self.mapper = mapper
        self.oldImport = oldImport


    def find_module(self, fullname, path=None):
        """
        Module finder nethod required by PEP 302 for meta-import hooks.

        @param fullname: The name of the module/package being imported.
        @param path: The __path__ attribute of the package, if applicable.
        """
        trace("find_module", fullname, path)
        return self


    def load_module(self, fqn):
        """
        Module loader method required by PEP 302 for meta-import hooks.

        @param fqn: The fully-qualified name of the module requested.
        """
        trace("load_module", fqn)
        trace("sys.modules", sys.modules)
        p = lookupWithMapper(self.mapper, fqn)
        trace("load_module", fqn , "done", id(p))

        if fqn in _sysModulesSpecialCases:
        # This module didn't have access to our isolated sys.modules when it
        # did its sys.modules modification. Replicate it here.
            for submoduleName in _sysModulesSpecialCases[fqn]:
                subfqn = '.'.join([fqn, submoduleName])
                sys.modules[subfqn] = getattr(p, submoduleName, None)
        return p


    def xocImport(self, name, *args, **kwargs):
        """
        Wrapper around C{__import__}. Needed to ensure builtin modules aren't
        loaded from the global context.
        """
        trace("Import invoked:", name, kwargs.keys())
        if name in sys.builtin_module_names:
            trace("Loading builtin module", name)
            return self.load_module(name)
        else:
            return self.oldImport(name, *args, **kwargs)




def loadNamed(fqn, mapper, m=None):
    """
    Load a Python module, eliminating as much of its access to global state as
    possible. If a package name is given, its __init__.py is loaded.

    @param fqn: The fully qualified name of a Python module, e.g
    C{twisted.python.filepath}.

    @param mapper: A L{Mapper}.

    @param m: An optional empty module object to load code into. (For
    resolving circular module imports.)

    @returns: An instance of the module name requested.
    """

    maker = getModule(fqn)
    return load(maker, mapper, m=m)


def load(maker, mapper, m=None):
    """
    Load a Python module, eliminating as much of its access to global state as
    possible. If a package name is given, its __init__.py is loaded.

    @param maker: A module maker object (i.e., a L{modules.PythonModule} instance)

    @param mapper: A L{Mapper}.

    @param m: An optional empty module object to load code into. (For
    resolving circular module imports.)

    @returns: An instance of the module name requested.
    """

    if maker.isPackage() and m is None:
        pkgContext = PackageContext(maker, mapper, getModule)
        return pkgContext.loadNamed(maker.name)
    else:
        mf = MakerFinder(__builtin__.__import__, mapper)
        if maker.filePath.splitext()[1] in [".so", ".pyd"]:
            #it's native code, gotta suck it up and load it globally (really at a
            ## loss on how to unit test this without significant inconvenience)
            return maker.load()
        return _isolateImports(mf, _loadSingle, maker, mf, m)

def _loadSingle(mk, mf, m=None):
    trace("execfile", mk.name, m)
    if m is None:
        m = ModuleType(mk.name)
    contents = {}
    code = execfile(mk.filePath.path, contents)
    contents['__exocet_context__'] = mf
    m.__dict__.update(contents)
    m.__file__ = mk.filePath.path
    return m

def _isolateImports(mf, f, *a, **kw):
    """
    Internal guts for actual code loading. Displaces the global environment
    and executes the code, then restores the previous global settings.

    @param mk: A L{modules._modules.PythonModule} object; i.e., a module
    maker.
    @param mf: A L{MakerFinder} instance.
    @param m: An optional empty module object to load code into. (For resolving
    circular module imports.)
    """


    oldMetaPath = sys.meta_path
    oldPathHooks = sys.path_hooks
    _PEP302Mapper._oldSysModules = sys.modules.copy()
    oldImport = __builtin__.__import__
    #where is your god now?
    sys.path_hooks = []
    sys.modules.clear()
    sys.meta_path = [mf]
    __builtin__.__import__ = mf.xocImport



    #stupid special case for the stdlib
    if mf.mapper.contains('warnings'):
        sys.modules['warnings'] = mf.mapper.lookup('warnings')

    try:
       return f(*a, **kw)
    finally:
        sys.meta_path = oldMetaPath
        sys.path_hooks = oldPathHooks
        sys.modules.clear()
        sys.modules.update(_PEP302Mapper._oldSysModules)
        __builtin__.__import__ = oldImport

def loadPackageNamed(fqn, mapper):
    """
    Analyze a Python package to determine its internal and external
    dependencies and produce an object capable of creating modules
    that refer to each other.

    @param fqn: The fully qualified name of a Python module, e.g
    C{twisted.python.filepath}.

    @param mapper: A L{Mapper}.

    @returns: A package loader object.
    """
    pkg = getModule(fqn)
    return loadPackage(pkg, mapper)


def loadPackage(pkg, mapper):
    """
    Analyze a Python package to determine its internal and external
    dependencies and produce an object capable of creating modules
    that refer to each other.

    @param pkg: a module maker object (i.e., a L{modules.PythonModule} instance)

    @param mapper: A L{Mapper}.

    @returns: A package loader object.
    """
    if not pkg.isPackage():
        raise ValueError("%r is not a package" % (pkg.name,))
    return PackageContext(pkg, mapper, getModule)


def _buildAndStoreEmptyModule(maker, mapper):
    m = ModuleType(maker.name)
    m.__path__ = maker.filePath.path
    mapper.add(maker.name,  m)
    return m


class PackageContext(object):
    """
    A context for loading interdependent modules from a package. This object
    allows modules in a package to refer to one another consistently without
    requiring them to be in sys.modules. Calling this object's C{loadNamed}
    method will retrieve an already loaded instance if one exists, or else
    loads it (and all its previously unloaded dependencies within the package)
    and remembers them for later use.
    """
    def __init__(self, packageMaker, mapper, getModule):
        """
        @param packageMaker: A L{modules._modules.PythonModule} object
        representing a package.
        @param mapper: A L{Mapper}.
        @param getModule: A function to fetch module maker objects, given an
        FQN. (For example, {twisted.python.}modules.getModule.)
        """
        self.packageMaker = packageMaker
        self.mapper = _PackageMapper(packageMaker.name, mapper)
        initModule = _buildAndStoreEmptyModule(packageMaker, self.mapper)
        if '.' in packageMaker.name:
            modulePath = packageMaker.name.split(".")
            if not self.mapper.contains(modulePath[0]):
                parentMaker = getModule(modulePath[0])
                parent = _buildAndStoreEmptyModule(parentMaker, self.mapper)
                self.mapper.add(modulePath[0], parent)
                for seg in modulePath[1:-1]:
                    new = _buildAndStoreEmptyModule(parentMaker[seg],
                                                    self.mapper)
                    setattr(parent, seg, new)
                    parent = new
                setattr(parent, modulePath[-1], initModule)
        self.allModules  = analyzePackage(self.packageMaker)
        sortedModules = robust_topological_sort(self.allModules)
        self.loadOrder = list(itertools.chain(*sortedModules))
        self.loadOrder.reverse()
        trace("load __init__", vars(initModule), id(initModule))
        self._reallyLoadModule(packageMaker.name, initModule)

    def _searchDeps(self, fqn, depsFoundSoFar=None):
        """
        Searches recursively for modules not yet loaded in this package.

        @param fqn: A module name.
        @param depsFoundSoFar: A set of dependencies found in previous
        invocations of this function, or None.
        """
        trace("searchDeps", fqn, depsFoundSoFar)
        if depsFoundSoFar is not None:
            deps = depsFoundSoFar
        else:
            deps = set()
        deps.add(fqn)
        maker, internalDeps, externalDeps = self.allModules[fqn]
        for dep in internalDeps:
            if dep not in deps and not self.mapper.contains(dep):
                    self._searchDeps(dep, deps)
        return deps

    def _unloadedDeps(self, fqn):
        """
        Returns an iterable of names of unloaded modules in this package that
        must be loaded to satisfy the dependencies of the named package, in
        the order they should be loaded.

        @param fqn: A module name in this package.
        """
        unloadedDeps = self._searchDeps(fqn)
        trace("raw unloaded deps", unloadedDeps)
        trace("load order", self.loadOrder)
        for dep in self.loadOrder:
            if dep in unloadedDeps:
                yield dep

    def loadNamed(self, fqn):
        """
        Load the named module in this package, and any dependencies it may
        have, if not already loaded. Returns the named module.

        @param fqn: The fully-qualified name of a module in this package.
        """
        trace("package loadModule", fqn)
        if self.mapper.contains(fqn):
            trace("package module load satisfied from cache")
            return lookupWithMapper(self.mapper, fqn)
        m = self._reallyLoadModule(fqn)
        trace("package module load triggered code loading", m)
        return m

    def _reallyLoadModule(self, fqn, m=None):
        """
        Do the actual work of loading modules (and their dependencies) into
        this package context.

        @param fqn: The fully-qualified name of a module in this package.
        @param m: An optional empty module object to load code into. (For
        resolving circular module imports.)
        """
        unloadedDeps = list(self._unloadedDeps(fqn))
        if self.packageMaker.name in unloadedDeps:
            unloadedDeps.remove(self.packageMaker.name)
        trace("unloaded deps", unloadedDeps)
        for name in unloadedDeps:
            self.mapper.add(name, ModuleType(name))
        for name in unloadedDeps:
            submod = lookupWithMapper(self.mapper, name)
            loadNamed(name, self.mapper, submod)
            trace("loaded", name, submod)
            setattr(lookupWithMapper(self.mapper, self.packageMaker.name),
                    name, submod)
        self.mapper.add(fqn, loadNamed(fqn, self.mapper, m))
        return lookupWithMapper(self.mapper, fqn)


def analyzePackage(pkg):
    """
    Build a graph of internal and external dependencies of all modules in a
    package.

    @param pkg: A L{modules._modules.PythonModule} object representing a
    package.

    @return: A mapping of fully qualified module names in a package to (module
    object, internal dependencies, external dependencies) triples.
    """
    allModules = {}
    def collect(module):
        if module.isPackage():
            for mod in module.walkModules():
                if mod is not module:
                    collect(mod)

        allModules[module.name] = (module, set(), set())


    collect(pkg)
    for name, (m, imports, externalDeps) in allModules.items():
        if m.filePath.splitext()[1] in [".so", ".pyd"]:
            continue
        for im in m.iterImportNames():
            prefix, dot, item = im.rpartition(".")
            if im in allModules:
                imports.add(im)
            elif prefix in allModules:
                imports.add(prefix)
            else:
                externalDeps.add(im)

    return allModules



## Topological sort based on Paul Harrison's public domain toposort.py

def strongly_connected_components(graph):
    """
    Find the strongly connected components in a graph using Tarjan's
    algorithm.

    @param graph: a mapping of node names to lists of successor nodes.
    """

    result = []
    stack = []
    low = {}

    def visit(node):
        if node in low: return

	num = len(low)
        low[node] = num
        stack_pos = len(stack)
        stack.append(node)

        for successor in graph[node][1]:
            visit(successor)
            low[node] = min(low[node], low[successor])

        if num == low[node]:
	    component = tuple(stack[stack_pos:])
            del stack[stack_pos:]
            result.append(component)
	    for item in component:
	        low[item] = len(graph)

    for node in graph:
        visit(node)

    return result


def topological_sort(graph):
    """
    Topological sort of a directed graph.

    @param graph: Mapping of nodes to lists of other nodes.

    @return: List of nodes, topologically sorted.
    """
    count = {}
    for node in graph:
        count[node] = 0
    for node in graph:
        for successor in graph[node]:
            count[successor] += 1

    ready = [node for node in graph if count[node] == 0]

    result = []
    while ready:
        node = ready.pop(-1)
        result.append(node)

        for successor in graph[node]:
            count[successor] -= 1
            if count[successor] == 0:
                ready.append(successor)

    return result


def robust_topological_sort(graph):
    """
    First identify strongly connected components,
    then perform a topological sort on these components.

    @param graph: Mapping of nodes to lists of other nodes.

    @return: List of tuples of strongly connected groups of nodes,
    topologically sorted.
    """
    components = strongly_connected_components(graph)

    node_component = {}
    for component in components:
        for node in component:
            node_component[node] = component

    component_graph = {}
    for component in components:
        component_graph[component] = []

    for node in graph:
        node_c = node_component[node]
        for successor in graph[node][1]:
            successor_c = node_component[successor]
            if node_c != successor_c:
                component_graph[node_c].append(successor_c)

    return topological_sort(component_graph)



def proxyModule(original, **replacements):
    """
    Create a proxy for a module object, overriding some of its attributes with
    replacement objects.

    @param original: A module.
    @param replacements: Attribute names and objects to associate with them.

    @returns: A module proxy with attributes containing the replacement
    objects; other attribute accesses are delegated to the original module.
    """
    class _ModuleProxy(object):
       def __getattribute__(self, name):
           if name in replacements:
               return replacements[name]
           else:
               return getattr(original, name)

       def __repr__(self):
           return "<Proxy for %r: %s replaced>" % (
               original, ', '.join(replacements.keys()))
    return _ModuleProxy()


def redirectLocalImports(name, globals=None, *a, **kw):
    """
    Catch function-level imports in modules loaded via Exocet. This ensures
    that any imports done after module load time look up imported names in the
    same context the module was originally loaded in.
    """

    if globals is not None:
        mf = globals.get('__exocet_context__', None)
        if mf is not None:
            trace("isolated __import__ of", name,  "called in exocet module", mf, mf.mapper)
            return _isolateImports(mf, _originalImport, name, globals, *a, **kw)
        else:
            return _originalImport(name, globals, *a, **kw)
    else:
        return _originalImport(name, globals, *a, **kw)


_originalImport = None

def installExocetGlobalHook():
    """
    Install the global Exocet import hook.
    """
    global _originalImport
    _originalImport = __builtin__.__import__
    __builtin__.__import__ = redirectLocalImports



def uninstallExocetGlobalHook():
    __builtin__.__import__ = _originalImport


installExocetGlobalHook()

