# Copyright (c) 2010-2011 Allen Short. See LICENSE file for details.
from exocet._exocet import (load, loadNamed, loadPackage, loadPackageNamed,
                            proxyModule, emptyMapper, pep302Mapper, IMapper,
                            DictMapper, ExclusiveMapper, CallableMapper,
                            getModule)

__all__= ['load', 'loadNamed', 'loadPackage', 'loadPackageNamed',
          'getModule', 'proxyModule', 'emptyMapper', 'pep302Mapper',
          'IMapper', 'DictMapper', 'CallableMapper']

__version__ = '0.5'

