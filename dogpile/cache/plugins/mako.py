from mako.cache import CacheImpl

class MakoPlugin(CacheImpl):
    def __init__(self, cache):
        super(MakoPlugin, self).__init__(cache)
        try:
            self.regions = self.cache.template.cache_args['regions']
        except KeyError:
            raise KeyError(
                "'cache_regions' argument is required on the "
                "Mako Lookup or Template object for usage "
                "with the dogpile.cache plugin.")

    def _get_region(self, **kw):
        try:
            region = kw['region']
        except KeyError:
            raise KeyError(
                "'cache_region' argument must be specified with 'cache=True'"
                "within templates for usage with the dogpile.cache plugin.")
        try:
            return self.regions[region]
        except KeyError:
            raise KeyError("No such region '%s'" % region)

    def get_and_replace(self, key, creation_function, **kw):
        return self._get_region(**kw).get_or_create(key, creation_function)

    def put(self, key, value, **kw):
        self._get_region(**kw).put(key, value)
 
    def get(self, key, **kw):
        return self._get_region(**kw).get(key)
 
    def invalidate(self, key, **kw):
        self._get_region(**kw).delete(key)
