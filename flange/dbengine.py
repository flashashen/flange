

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
    url_format_string = "{:s}://{:s}:{:s}@{:s}:{:s}/{:s}?"
    engine = create_engine(url_format_string.format(
        config['driver'],
        config['user'],
        config['pass'],
        config['host'],
        config['port'],
        config['name']), convert_unicode=True)

    return engine


def register():
    cfg.register_default_model(
        'dbengine',
        model.Model('dbengine',
                    model.Model.get_schema_validator(dbengine_schema),
                    dbengine_create_func))

register()