# flange 

Application configuration and object instantiation. This is partially inspired by spring app framework


### Notes

- Temporarily has a hard dependency on sqlalchemy and requests. Models depending on external libs will later be handled as plugins or conditional imports



### Usage

```
In [1]: import flange
In [2]: flange.sources
Out[2]: <function flange.sources>

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
 {'ns': 'Trash',
  'src': '/Users/a.user/.Trash/docker-compose.override.yml',
  'type': 'yml'},
 {'ns': 'Trash',
  'src': '/Users/a.user/.Trash/docker-compose.yml',
  'type': 'yml'},
 {'ns': 'env', 'src': 'os', 'type': None}]
```