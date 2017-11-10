
import copy, datetime
from . import iterutils




import jsonschema

def validate(d, spec):
    try:
        jsonschema.validate(d, spec)
        return True
    except:
        return False



class Registry(object):
    '''
        Base class for model and object registries
    '''
    def get_registration(self, config_key, raise_absent=False):

        if len(self.registrations) == 0 or (config_key and config_key not in self.registrations):
            if raise_absent:
                raise ValueError("nothing registered under '{}'".format(config_key))
            else:
                return

        if config_key:
            return self.registrations[config_key]
        else:
            if len(self.registrations) == 1:
                return self.registrations.values()[0]
            else:
                raise ValueError("Multiple valid configurations exist. Config id/key must be specified")

    def list(self):
        return self.registrations.keys()


    def get(self, config_key=None, raise_absent=False):
        return self.get_registration(config_key, raise_absent)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<{} contents={}>".format(self.__class__.__name__ , self.registrations.keys())



# Construct a registry class that closes overs the creation function map
class InstanceRegistry(Registry):

    def __init__(self, schema, factory, cache=True, mutable=False):
        self.registrations = {}
        self.schema = schema
        self.factory = factory
        self.cache = cache
        self.mutable = mutable


    def validate(self, data):
        return jsonschema.validate(data, self.schema)


    def research(self, data):
        """
            Traverse the data dict recursively to find anything matching the schema. For every match, create
            a registration

        :param data: input data to research
        :return: None
        """
        for result in iterutils.research(data, query=lambda p,k,v: validate(v,self.schema), reraise=False):
            self.registerParams(result[0][-1], result[1]);


    def registerInstance(self, key, instance):
        self.registrations[key] = {
            'cached_obj': instance,
            'cached_since': datetime.datetime.now(),
            'params_source': 'unknown',
            'params_key_path': 'unknown',
            'params': None}

    def registerParams(self, key, data):
        self.registrations[key] = {
            'cached_obj': None,
            'cached_since': None,
            'params_source': 'unknown',
            'params_key_path': 'unknown',
            'params': data if self.mutable else copy.deepcopy(data)}



    def info(self):
        import pprint
        return pprint.pformat({'registry': [name for name in self.registrations.keys()]})



    def update(self, config_key, **kargs):

        if not self.mutable:
            raise Exception('Registry configured as immutable')

        reg = self.get_registration(config_key)
        for key, value in kargs.items():
            # Just put in whatever is given. If its a new key it will be added
            reg['params'][key] = value

        return self.info(config_key)


    def list(self):
        return self.registrations.keys()


    def get(self, config_key=None, raise_absent=False):

        reg = self.get_registration(config_key, raise_absent)
        if reg:

            if reg['cached_obj']:
                return reg['cached_obj']

            if not 'params':
                raise ValueError('either a pre-created object or factory parameters must be given')

            obj = self.factory(reg['params'])
            if self.cache:
                reg['cached_obj'] = obj
                reg['cached_since']= datetime.datetime.now()

            return obj




logger_schema = {
    "type" : "object",
    "properties" : {
        'name':{'type':'string'},
        'level':{'type':'string'},
        'format':{'type':'string'},
        'handler':{'type':'string'},
        'handler_args':{'type':'string'},
    },
    "required": ["name", "level", "format"]
}


def logger_factory(config):
    import logging
    from logging import handlers
    log = logging.getLogger(config['name'])
    log.setLevel(getattr(logging, config['level'].upper()))
    if 'handler' in config:
        hargs = config['handler_args'] if 'handler_args' in config else {}
        try:
            # Create a handler assuming the class is defined in the logging.handlers class
            hdlr =  getattr(handlers, config['handler'])(**hargs)
        except:
            # Retry from the logging module directly
            hdlr =  getattr(logging, config['handler'])(**hargs)
    else:
        hdlr = logging.StreamHandler()
    hdlr.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s"))
    log.handlers = []
    log.addHandler(hdlr)
    return log


LOG_REGISTRY = InstanceRegistry(logger_schema , logger_factory)
