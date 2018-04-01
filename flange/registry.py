
import copy, datetime
from . import iterutils
from six import iteritems

try:
    basestring
except NameError:
    basestring = str



import jsonschema

def validate(d, spec):
    try:
        jsonschema.validate(d, spec)
        return True
    except:
        return False















# Construct a registry class that closes overs the creation function map
class InstanceRegistry(object):

    def __init__(self, schema, factory, cache=True, mutable=False):
        self._registrations = {}
        self._schema = schema
        self._factory = factory
        self._cache = cache
        self._mutable = mutable



    #
    #  # methods for dict like access
    #
    # def __getattr__(self, item):
    #     obj = self.get(item)
    #     if obj:
    #         return obj
    #     raise AttributeError
    #
    # def __getitem__(self, item):
    #     return self.__getattr__(item)
    #
    # def keys(self):
    #     return self._registrations.keys()
    #
    # def values(self):
    #     return [x['cached_obj'] for x in self._registrations.values()]
    #
    # def items(self):
    #     return { k: v['cached_obj'] for k, v in iteritems(self._registrations)}




    def validate(self, data):
        return jsonschema.validate(data, self._schema)


    def matches_filter(self, registration, vfilter):
        if not vfilter:
            return True
        return all([iterutils.search(registration['params'], term, exact=False, accepted_keys=False, require=True, path=None) for term in vfilter])


    def research(self, data):
        """
            Traverse the data dict recursively to find anything matching the schema. For every match, create
            a registration

        :param data: input data to research
        :return: None
        """
        for result in iterutils.research(data, query=lambda p, k, v: validate(v, self._schema), reraise=False):
            self.registerContents(result[0][-1], result[1]);


    # def registerInstance(self, key, instance):
    #     self._registrations[key] = {
    #         'key': key,
    #         'cached_obj': instance,
    #         'cached_since': datetime.datetime.now(),
    #         'params_source': 'unknown',
    #         'params_key_path': 'unknown',
    #         'params': None,
    #         'exception': None}
    #
    # def registerContents(self, key, data, validate=False):
    #     if not key:
    #         raise ValueError("invalid registration key: {}. This could result from a valid model instance at top level of data. Try providing a value for 'root_ns'".format(key))
    #     self._registrations[key] = {
    #         'key': key,
    #         'cached_obj': None,
    #         'cached_since': None,
    #         'params_source': 'unknown',
    #         'params_key_path': 'unknown',
    #         'params': data if self._mutable else copy.deepcopy(data),
    #         'exception': None}
    #     if validate:
    #         self.get(key)



    def info(self):
        import pprint
        return pprint.pformat({'registry': [name for name in self._registrations.keys()]})



    def update(self, config_key, **kargs):

        if not self._mutable:
            raise Exception('Registry configured as immutable')

        reg = self.get_registration(config_key)
        for key, value in kargs.items():
            # Just put in whatever is given. If its a new key it will be added
            reg['params'][key] = value

        return self.info(config_key)


    # def list(self, vfilter=None):
    #     return self._registrations.keys()
    #     # return [k for k,v in self._registrations.items() if self.matches_filter(v, vfilter)]


    def get(self, config_key=None, raise_absent=False, vfilter=None):

        reg = self.get_registration(config_key, raise_absent, vfilter)
        if reg:

            if reg['cached_obj']:
                return reg['cached_obj']

            if not 'params':
                raise ValueError('either a pre-created object or factory parameters must be given')

            try:
                obj = self._factory(reg['params'])
                if self._cache:
                    reg['cached_obj'] = obj
                reg['cached_since']= datetime.datetime.now()
                return obj

            except Exception as e:
                reg['exception'] = e



    def get_registration(self, config_key=None, raise_absent=False, vfilter=None, instance=None):

        if isinstance(vfilter, basestring):
            vfilter = [vfilter]


        if config_key:

            if config_key not in self._registrations.keys():
                if raise_absent:
                    raise ValueError("no registration found for '{}'".format(config_key))
            else:
                reg = self._registrations[config_key]

                if instance and instance != reg['cached_obj']:
                    raise ValueError("registration found for {} but did not match instance {}".format(config_key, instance))
                elif not self.matches_filter(reg, vfilter):
                    raise ValueError("registration found for {} but did not match filters {}".format(config_key, vfilter))
                else:
                    return reg

        elif instance:
            matches = [x for x in self._registrations.values() if instance == x['cached_obj']]
            if matches:
                if len(matches) > 1:
                    raise ValueError("multiple matching configurations exist")
                elif vfilter and not self.matches_filter(matches[0], vfilter):
                    raise ValueError("registration found for instance {} but did not match filters {}".format(instance, vfilter))
                else:
                    return matches[0]
            elif raise_absent:
                raise ValueError("no registrations matched instance {}".format(vfilter))

        elif vfilter:
            matches = [x for x in self._registrations.values() if self.matches_filter(x, vfilter)]
            if not matches:
                if raise_absent:
                    raise ValueError("no registrations matched filters {}".format(vfilter))
            elif len(matches) == 1:
                return matches[0]
            else:
                raise ValueError("multiple matching configurations exist")

        else:
            raise ValueError('no search criteria provided')



    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<{} contents={}>".format(self.__class__.__name__ , self._registrations.keys())


