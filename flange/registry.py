
import copy, datetime
from . import iterutils


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
        self.registrations = {}
        self.schema = schema
        self.factory = factory
        self.cache = cache
        self.mutable = mutable


    def validate(self, data):
        return jsonschema.validate(data, self.schema)


    def matches_filter(self, registration, vfilter):
        if not vfilter:
            return True
        return all([iterutils.search(registration['params'], term, exact=False, keys=False, values=True, path=None) for term in vfilter])


    def research(self, data):
        """
            Traverse the data dict recursively to find anything matching the schema. For every match, create
            a registration

        :param data: input data to research
        :return: None
        """
        for result in iterutils.research(data, query=lambda p,k,v: validate(v,self.schema), reraise=False):
            self.registerContents(result[0][-1], result[1]);


    def registerInstance(self, key, instance):
        self.registrations[key] = {
            'cached_obj': instance,
            'cached_since': datetime.datetime.now(),
            'params_source': 'unknown',
            'params_key_path': 'unknown',
            'params': None}

    def registerContents(self, key, data, validate=False):
        self.registrations[key] = {
            'cached_obj': None,
            'cached_since': None,
            'params_source': 'unknown',
            'params_key_path': 'unknown',
            'params': data if self.mutable else copy.deepcopy(data)}
        if validate:
            self.get(key)



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


    def list(self, vfilter=None):
        return self.registrations.keys()
        # return [k for k,v in self.registrations.items() if self.matches_filter(v, vfilter)]


    def get(self, config_key=None, raise_absent=False, vfilter=None):

        reg = self.get_registration(config_key, raise_absent, vfilter)
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


    def get_registration(self, config_key, raise_absent=False, vfilter=None):

        if isinstance(vfilter, basestring):
            vfilter = [vfilter]


        if config_key:

            if config_key not in self.registrations.keys():
                if raise_absent:
                    raise ValueError("no registration found for '{}'".format(config_key))
            else:
                reg = self.registrations[config_key]

                if not self.matches_filter(reg, vfilter):
                    if raise_absent:
                        raise ValueError("registration found for {} but did not match filters {}".format(config_key,vfilter))
                else:
                    return reg

        else:
            matches = [x for x in self.registrations.values() if self.matches_filter(x, vfilter)]
            if not matches:
                if raise_absent:
                    raise ValueError("no registrations matched filters {}".format(vfilter))
            elif len(matches) == 1:
                return matches[0]
            else:
                raise ValueError("multiple matching configurations exist")




    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<{} contents={}>".format(self.__class__.__name__ , self.registrations.keys())



logger_schema = {
    "type" : "object",
    "properties" : {
        'name':{'type':'string'},
        'level': { "enum": ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']},
        # 'level':{'type':'string'},
        'format':{'type':'string'},
        'handler':{'type':'string'},
        'handler_args':{'type':'string'},
    },
    "required": ["name", "level"]
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
    if 'format' in config:
        hdlr.setFormatter(logging.Formatter(config['format']))
    else:
        hdlr.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s"))

    log.handlers = []
    log.addHandler(hdlr)
    return log


LOG_REGISTRY = InstanceRegistry(logger_schema , logger_factory)
