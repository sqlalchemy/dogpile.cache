""" 
dogpile.cache.proxy

A class that can wrap backend objects in order to provide extra functionality.  Designed to be 
stackable and easy to extend
"""

from .api import CacheBackend

class ProxyBackend(object):
    
    def __init__(self, *args, **kwargs):
        self.proxied = None
        
    def wrap(self, backend):
        assert(isinstance(backend, CacheBackend) or isinstance(backend, ProxyBackend))
        self.proxied = backend
        return self

    def __getattr__(self, name):
        """ Decorate the backend with extended functionality.  Pass through 
        any functions that do not within the class """  
        if self.proxied and getattr(self.proxied, name):
            setattr(self, name, getattr(self.proxied, name))
            return getattr(self.proxied, name)
        else:
            raise AttributeError
        
 
        
    




    
    



    

        