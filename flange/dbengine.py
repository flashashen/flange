

from . import cfg, model
from sqlalchemy import create_engine

dbengine_schema = {
    "type" : "object",
    "properties" : {
        'driver':{'type':'string'},
        'name':{'type':'string'},
        'user':{'type':'string'},
        'pass':{'type':'string'},
        'port':{'type':'string'},
    },
    "required": ["driver", "name", "user", "pass"]
}


def dbengine_create_func(config):

    url = "{:s}://{:s}:{:s}@{:s}:{:s}/{:s}?".format(
        config.pop('driver'),
        config.pop('user'),
        config.pop('pass'),
        config.pop('host'),
        config.pop('port'),
        config.pop('name'))

    return create_engine(url, **config)


def register():
    cfg.register_default_model(
        'dbengine',
        model.Model('dbengine',
                    model.Model.get_schema_validator(dbengine_schema),
                    dbengine_create_func))

register()