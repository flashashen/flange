# Flange 

Application configuration and object instantiation. This is partially inspired by spring app framework

Resources - Define, Discover, Fetch, Interact, Update 

many resources merged 
URL handler plugin scheme
object cache


### What it does
- Automatically load the data of various applications/formats using Anyconfig
- Object registry with caching
- Pluggable, automatic object detection/creation from data sources based on jsonschema
- Convenient object access 

### What it will do
- encrypt data files, read encrypted files 
- Edit data and write back to src files 
- Provide prompts for missing elements given a dict and a model/schema


## How it works

**init**
- searches for any recongnized config/data files on start
- first pass of loaded sources: look for flange specific config
- performs another load round if needed based on flange config
- repeat load and process steps until all flange config is processed
- final pass of loaded sources: performs a final data merge and normalization
- scans for model instances including model plugins

### Usage

```
In [1]: import flange

In [3]: flange.sources()
Out[3]: 
[{'ns': '', 'src': '/Users/a.user/.cmd.yml', 'type': 'yml'},
 {'ns': '', 'src': '/Users/a.user/.ansible.cfg', 'type': 'shellvars'},
 {'ns': 'docker',
  'src': '/Users/a.user/.docker/config.json',
  'type': 'json'},
 {'ns': 'heroku',
  'src': '/Users/a.user/.heroku/config.json',
  'type': 'json'},
 {'ns': 'm2', 'src': '/Users/a.user/.m2/settings.xml', 'type': 'xml'},
 {'ns': 'm2', 'src': '/Users/a.user/.m2/settings.xml.hide', 'type': 'xml'},
 {'ns': 'nyttth', 'src': '/Users/a.user/.nyttth/config.yml', 'type': 'yml'},
 {'ns': 'nyttth',
  'src': '/Users/a.user/.nyttth/config_example.yml',
  'type': 'yml'},
 {'ns': 'nyttth', 'src': '/Users/a.user/.nyttth/config.yml', 'type': 'yml'},
 {'ns': 'nyttth',
  'src': '/Users/a.user/.nyttth/config_example.yml',
  'type': 'yml'},
 {'ns': 'ScreamingFrogSEOSpider',
  'src': '/Users/a.user/.ScreamingFrogSEOSpider/spider.config',
  'type': 'shellvars'},
 {'ns': 'sonic-pi',
  'src': '/Users/a.user/.sonic-pi/settings.json',
  'type': 'json'},
 {'ns': 'env', 'src': 'os', 'type': None}]
```