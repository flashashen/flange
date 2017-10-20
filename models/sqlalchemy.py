

from sqlalchemy import create_engine

sql_engine_model = {
    "type" : "object",
    "properties" : {
        'driver':{'type':'string'},
        'name':{'type':'string'},
        'user':{'type':'string'},
        'pass':{'type':'string'},
        'port':{'type':'int'},
    },
    "required": ["driver", "name", "user", "pass"]
}

def sql_engine_create_func(config):
    url_format_string = "{:s}://{:s}:{:s}@{:s}:{:s}/{:s}?charset=utf8"
    engine = create_engine(url_format_string.format(
        config['driver'],
        config['user'],
        config['pass'],
        config['host'],
        str(config['port']),
        config['name']), convert_unicode=True)

    return engine

