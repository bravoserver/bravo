from twisted.plugin import IPlugin
from zope.interface import implements

from beta.ibeta import ICommand
from beta.plugin import retrieve_plugins

class Help(object):

    implements(IPlugin, ICommand)

    def dispatch(self, parameters):
        plugins = retrieve_plugins(ICommand)
        for name, plugin in plugins.iteritems():
            print "%s" % plugin.name

    name = "help"

help = Help()
