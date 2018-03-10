# Flange 

Convenient configuration search and load with a model based object registry. 

*With bits of config you may already have lying around..*
``` yaml

  # somewhere in a config file ..
  my_logger:
    name: myapp
    level: DEBUG
    format: "%(asctime)s:%(levelname)s:%(name)s  %(message)s"
    

  # somewhere in a different config file ..
  my_mssql_db:
    driver: mssql+pymssql
    name: dbname
    user: devuser
    pass: devpass
    host: dbhost.dev.corp
    port: '1111'
    desc: dev db
    args: {'login_timeout':6}
    
  
  # from env vars
   export my_mssql_db__pass=devpass
```

*you can do this..*

```
sh> python -c "from flange import cfg, dbengine; result = cfg.mget('my_mssql_db').execute('USE master SELECT @@version').first()[0]; cfg.mget('my_logger').debug(result)"
2018-03-09 15:49:55,726:DEBUG:myapp  Microsoft SQL Server 2008 (SP4) - 10.0.6000.29 (X64) 
	Sep  3 2014 04:11:34 
	Copyright (c) 1988-2008 Microsoft Corporation
	Enterprise Edition (64-bit) on Windows NT 6.1 <X64> (Build 7601: Service Pack 1) (VM)
```

**You want this if**:

- You're tired of boilerplate configuration code in your python projects
- You're tired of boilerplate logger setup in your python projects
- You're tired of boilerplate data access setup in your python projects
- You're tired of boilerplate *{{fill in the blank}}* setup in your python projects
- you want to hack in the python console and don't remember where you put all your bits 
of config and credentials
- You want to keep passwords separate from main config

 
## What it does

- Automatically searches for and loads (configuration) data in various formats using Anyconfig
- Merges configuration from various sources using Anyconfig
- Pluggable, automatic object detection/creation from config data
- Object registry with lazy init and cache
- Convenient object access 

This is partially inspired by the Spring framework. On init, the main configuration object 
will search for a given set of file pattern at a given directory to a given depth for config 
data and will merge this data into a single configuration object.

Additionally, an object registry is provided that can recognize patterns in the config data
and return cached instances on demand of any type of object. Object initialization is automatic and lazy.
Recognition of instances currently employs json schema 
to identify patterns and a python function is provided that serves as the factory function. 
The factory method can be given explicity in python or specified as url that resolves to a 
python function. The combination of a schema and a factory function along with a name are 
called a 'model'.  


## Usage

##### Model - Logger

This shows access to a logger object which is a built-in model of flange. The built-in logger schema looks like this:

```
{
    "type" : "object",
    "properties" : {
        'name':{'type':'string'},
        'level': { "enum": ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']},
        'format':{'type':'string'},
    },
    "required": ["name", "level"]
}
```

the config looks like this (can appear anywhere in your config files):

```
{
..
  my_logger:
    name: myapp
    level: DEBUG
    format: "%(asctime)s:%(levelname)s %(message)s"
}
```

the object is accessed with the mget(..) method *(model get)*  like this:

```
In [1]: from flange import cfg

In [2]: log = cfg.mget('my_logger')

In [3]: log.debug('hello')
2018-03-09 14:08:17,261:DEBUG:myapp hello
```

if the key in the configuration is not known, then the instance can be fetched
with just the model name *(provided there is only one instance)*:

```
In [4]: cfg.mget(model='logger').debug('hello')
2018-03-09 14:43:07,514:DEBUG:myapp  hello
``` 

.. or just by specifying a value in the instance config with vfilter:

```
In [5]: cfg.mget(vfilter='myapp').debug('hello')
2018-03-09 14:42:50,785:DEBUG:myapp  hello
```

.. or by specifying multiple values in the instance config with vfilter:

```
In [6]: cfg.mget(vfilter=['myapp','DEBUG']).debug('hello')
2018-03-09 14:51:36,742:DEBUG:myapp  hello
```

Any combination of key, model, and vfilter terms can be given to select a 
unique instance with the mget(..) method.


the raw config can also be accessed with the get(..) method:

```
In [7]: cfg.get('my_logger')
Out[7]: 
OrderedDict([('name', 'dshlog'),
             ('level', 'DEBUG'),
             ('format', '%(asctime)s:%(levelname)s %(message)s')])
```


##### Model - dbengine / sqlalchemy 

This is another example with the default settings. The loaded data is described
with the info() method. The the dbengine module is imported which automatically registers 
an sqlalchemy based model and searches for any configuration that is a valid/sufficient for a 
sqlalchemy engine. Note: sqlalchemy is an example built-in model. Any sort of model can be 
registered. **Note that after the import of dbengine module, the 'dbengine' model and it's instances
appear in the output.**

```
In [2]: from flange import cfg

In [3]: cfg.info()

models:
logger               instances: logger

base dir: 	.
search depth: 	1
file include patterns: 	['*.yml', '*cfg', '*settings', '*config', '*properties', '*props']
file exclude patterns: 	['*.tar', '*.jar', '*.zip', '*.gz', '*.swp', 'node_modules', 'target', '.idea', '*.hide', '*save']

sources:
None                 os_env
shellvars            /Users/myuser/.gitconfig
yml                  /Users/myuser/config_example.yml
yml                  /Users/myuser/.cmd.yml
shellvars            /Users/myuser/.ansible.cfg
yml                  /Users/myuser/.flangetest.yml
shellvars            /Users/myuser/.bundle/config
shellvars            /Users/myuser/.git/config
yml                  /Users/myuser/.nyttth/config.yml
shellvars            /Users/myuser/.plotly/.config
shellvars            /Users/myuser/.ScreamingFrogSEOSpider/spider.config
shellvars            /Users/myuser/.ssh/config
shellvars            /Users/myuser/.subversion/config
shellvars            /Users/myuser/airflow/airflow.cfg
shellvars            /Users/myuser/airflow/unittests.cfg
yml                  /Users/myuser/Downloads/config_example.yml
yml                  /Users/myuser/workspace/docker-compose-swarm.yml

In [4]: from flange import dbengine

In [5]: cfg.info()

models:
dbengine             instances: testdb,db1
logger               instances: logger

base dir: 	.
search depth: 	1
file include patterns: 	['*.yml', '*cfg', '*settings', '*config', '*properties', '*props']
file exclude patterns: 	['*.tar', '*.jar', '*.zip', '*.gz', '*.swp', 'node_modules', 'target', '.idea', '*.hide', '*save']

sources:
None                 os_env
yml                  /Users/myuser/config_example.yml
yml                  /Users/myuser/.cmd.yml
shellvars            /Users/myuser/.ansible.cfg
yml                  /Users/myuser/.flangetest.yml
shellvars            /Users/myuser/.bundle/config
yml                  /Users/myuser/.nyttth/config.yml
shellvars            /Users/myuser/.plotly/.config
shellvars            /Users/myuser/.ScreamingFrogSEOSpider/spider.config
shellvars            /Users/myuser/.ssh/config
shellvars            /Users/myuser/.subversion/config
shellvars            /Users/myuser/airflow/airflow.cfg
shellvars            /Users/myuser/airflow/unittests.cfg
yml                  /Users/myuser/Downloads/config_example.yml
yml                  /Users/myuser/workspace/docker-compose-swarm.yml


In [6]: cfg.mget('db1')
Out[6]: Engine(mssql+pymssql://corpdomain\corpuser:***@dbhost:1111/dbname?charset=utf8)
```

## Plugins

Here is how the dbengine (sqlalchemy) model is defined:

``` Python
from . import cfg
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
    url_format_string = "{:s}://{:s}:{:s}@{:s}:{:s}/{:s}?charset=utf8"
    engine = create_engine(url_format_string.format(
        config['driver'],
        config['user'],
        config['pass'],
        config['host'],
        config['port'],
        config['name']), convert_unicode=True)

    return engine


def register():
    cfg.register_default_plugin('dbengine', dbengine_schema, dbengine_create_func)

register()
```
    
The example above showed explicit registration from python. Plugin registration can also be accomplished 
with just configuration. Here is an example from the 
tests in this project. For this to work, a python factory function must exist in the python 
path, resolved via a local url *(see example for url format)*. This config must also appear somewhere in the loaded
config data loaded by flange. With those caveats, The following is all 
that is required to register a custom model and start accessing instances: 

```
config_with_plugin = {

    'test_instance_key': {
        'only_TestPlugin_would_match_this': 'some value'
    },

    'test_plugin_config_key': {
        'type': 'FLANGE.TYPE.PLUGIN',
        'schema': {
            'type': 'object',
            'properties':{
                'only_TestPlugin_would_match_this': {'type': 'string'}
            },
            'required': ['only_TestPlugin_would_match_this']
        },
        'factory': 'python://flange.test.TestPlugin().get_instance'
    }
}
```


## Installation

```
pip install flange
```

### TODO

- encrypt data files, read encrypted files 
- Edit data and write back to src files 
- Provide prompts for missing elements given a dict and a model/schema
