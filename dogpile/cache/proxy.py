"""
Proxy Backends
------------------

Provides a utilities and a decorator class that allow for modifying the behavior 
of different backends without altering the class itself or having to extend the 
base backend.  

"""

from .api import CacheBackend

class ProxyBackend(object):
    """A decorator class for altering the functionality of backends 

    Basic usage::

        from dogpile.cache import make_region
        from dogpile.cache.proxy import ProxyBackend
        
        class MyFirstProxy(ProxyBackend):
            def get(self, key):
                ... custom code goes here ...
                return self.proxied.get(key)
                
            def set(self, key, value):
                ... custom code goes here ...
                self.proxied.set(key)
            
        class MySecondProxy(ProxyBackend):
            def get(self, key):
                ... custom code goes here ...
                return self.proxied.get(key)
                

        region = make_region().configure(
            'dogpile.cache.dbm',
            expiration_time = 3600,
            arguments = {
                "filename":"/path/to/cachefile.dbm"
            },
            wrap = [ MyFirstProxy, MySecondProxy ]
        )

    Classes that extend ProxyBackend can be stacked 
    together.  The `.proxied` property will always 
    point to either the concrete backend instance or 
    the next proxy in the chain that a method can be 
    delegated to.
    """ 
        
    def __init__(self, *args, **kwargs):
        self.proxied = None
        
    def wrap(self, backend):
        ''' Take a backend as an argument and setup the self.proxied property.  
        Return an object that be used as a backend by a `CacheRegion` object.
        '''
        assert(isinstance(backend, CacheBackend) or isinstance(backend, ProxyBackend))
        self.proxied = backend
        return self

    def __getattr__(self, name):
        ''' If a method is not already defined or overridden within this class 
        then delegate this call to the next proxy or backend '''   
        if self.proxied and getattr(self.proxied, name):
            setattr(self, name, getattr(self.proxied, name))
            return getattr(self.proxied, name)
        else:
            raise AttributeError
        
 
        
    




    
    



    

        