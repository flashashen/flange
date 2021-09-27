from . import url_scheme_python as pyurl
import jsonschema
import datetime
import copy


class ModelRegistration(object):

    def __init__(self, model, data, fobj=None):

        self.factory = lambda: model.factory(copy.deepcopy(data))
        self.cached_object = None
        self.cached_since = None
        self.exception = None
        self.fobj = fobj

    def __repr__(self):
        return '<ModelRegistration {} {} {}>'.format(self.cached_object, self.cached_since, self.exception)

    def instance(self, reraise=False):

        if not self.cached_object:

            try:
                self.cached_object = self.factory()
                if self.fobj:
                    setattr(self.cached_object, '__flange', self.fobj)
                self.cached_since = datetime.datetime.now()
                self.exception = None
                return self.cached_object

            except Exception as e:
                self.exception = e
                if reraise:
                    raise e

        return self.cached_object


class Model(object):

    def __init__(self, name, validator, factory, inject=None):
        self.name = name
        self.factory = factory
        self.validator = validator
        self.inject = inject
        self.fobj = None

    def __repr__(self):
        return '<Model {}>'.format(self.name)


    def registration(self, data):
        return ModelRegistration(self, data, self.fobj)


    @staticmethod
    def get_schema_validator(schema):
        return lambda v: jsonschema.validate(v, schema) == None

    @staticmethod
    def from_plugin_config(config):

        if isinstance(config['schema'], str):
            # parse schema as a url of a method that returns the schema
            schema = pyurl.get(config['schema'])()
        else:
            # otherwise assume this is the schema itself as a dict
            schema = config['schema']

        return Model(
            config.get('name'),
            lambda v: jsonschema.validate(v, schema) == None,
            pyurl.get(config['factory']),
            config.get('inject'))



PLUGIN_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': {'type':'string'},
        'type': {'constant': 'FLANGE.TYPE.PLUGIN'},
        'schema': {
            'oneOf': [
                {'type':'string', 'pattern': pyurl.URL_PATTERN_STRING},
                {'type': 'object'}]},
        'factory': {'type':'string', 'pattern': pyurl.URL_PATTERN_STRING},
        'inject': {"enum": ['flange']}  # if 'flange' then cause instances to have the '__flange' var set to the flange object
    },
    'required': ['name','type','schema','factory']}




logger_schema = {
    "type" : "object",
    "properties" : {
        'name': {'type':'string'},
        'level': { "enum": ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']},
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




# A model to recognize other flange models in config
PLUGIN_MODEL = Model(
    'flange_plugin',
    Model.get_schema_validator(PLUGIN_SCHEMA),
    Model.from_plugin_config)


DEFAULT_MODELS = {

    # simple log model
    'logger': Model(
        'logger',
        Model.get_schema_validator(logger_schema),
        logger_factory)
}

