#
# docker_compose_model = {
#     'image':{'type':'string',
#             'required':True}
# }


#
#       requests GET
#
#

import requests
# import jmespath

json_api_model = {
    "type" : "object",
    "properties" : {
        'url':{'type':'string'},
        'user':{'type':'string'},
        'password':{'type':'string'},
        'extract':{'type':'string'},
    },
    "required": ["url", "level", "format"]
}

def fetch_json(config):

    auth = (config['user'],config['password']) if 'user' in config else None
    r = requests.get(config['url'], verify=False, auth=auth).json()
    # if 'jmespath' in config:
    #     r = jmespath.search(config['jmespath'], r)
    return r


#
#       python logger
#


logger_model = {
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


def create_logger(config):
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


#
#       Sqlalchemy engine
#

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


model_specs = {
    'logger': {'config_model':logger_model, 'create_func':create_logger},
    'sqlengine' : {'config_model':sql_engine_model, 'create_func':sql_engine_create_func},
    'api' : {'config_model':json_api_model, 'create_func':fetch_json}
}