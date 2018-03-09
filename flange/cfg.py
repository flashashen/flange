
import anyconfig, os, fnmatch, string, six
from . import iterutils, url_scheme_python as pyurl
from .registry import InstanceRegistry, LOG_REGISTRY


PARSABLES = {
    'pickle':['p','pickle'],
    'xml':['xml'],
    'yaml':['yml','yaml'],
    'json':['json'],
    'ini':['ini'],
    'properties':['props','properties'],
    'shellvars':['env']}

DEFAULT_EXCLUDE_PATTERNS = ['*.tar','*.jar','*.zip','*.gz','*.swp','node_modules','target','.idea','*.hide','*save']
DEFAULT_FILE_PATTERNS = ['*.yml','*cfg','*settings','*config','*properties','*props']
VALID_KEY_CHARS = [c for c in string.printable if c not in ['_'] ]
VALID_KEY_FUNC = lambda k: isinstance(k, six.string_types) and len(k)<50 and all(c in string.printable for c in VALID_KEY_CHARS)


PLUGIN_SCHEMA = {
    'type': 'object',
    'properties': {
        'type': {'constant': 'FLANGE.TYPE.PLUGIN'},
        'schema': {
            'oneOf': [
                {'type':'string', 'pattern': pyurl.URL_PATTERN_STRING},
                {'type': 'object'}]},
        'factory': {'type':'string', 'pattern': pyurl.URL_PATTERN_STRING}
    },
    'required': ['type','schema','factory']}


DEFAULT_PLUGINS = {'logger': LOG_REGISTRY}
def register_default_plugin(name, schema, factory):
    DEFAULT_PLUGINS[name] = InstanceRegistry(schema, factory)
    # print DEFAULT_PLUGINS
    # If the global instance is already constructed, then explicitly register and research now
    if __GLOBAL_CFG:
        register_model(name, schema, factory)





def from_file(filename, root_ns=None, file_ns_from_dirname=False):
    path, basename = os.path.split(os.path.realpath(os.path.expanduser(filename)))
    return Cfg(root_ns=root_ns, file_ns_from_dirname=file_ns_from_dirname, include_os_env=False, base_dir=path, file_patterns=[basename])

def from_dict(d):
    return Cfg(data=d, file_patterns=None)


def from_os_env(root_ns=None):
    return Cfg(root_ns=root_ns, include_os_env=True, file_patterns=[])




#
#   Provide a Global object for convenience. Shadow the main class methods at the module level.
#

__GLOBAL_CFG = None
def __GET_GLOBAL_FLANGE():
    global __GLOBAL_CFG
    if not __GLOBAL_CFG:
        __GLOBAL_CFG = Cfg()
    return __GLOBAL_CFG

def mget(config_key=None, model=None, vfilter=None, raise_absent=False):
   return __GET_GLOBAL_FLANGE().mget(config_key=config_key, model=model, vfilter=vfilter, raise_absent=raise_absent)

def info():
    return __GET_GLOBAL_FLANGE().info()

def search(pattern, exact=True, keys=True, values=False, path=None):
    return __GET_GLOBAL_FLANGE().search(pattern, exact, keys, values, path)

def get(key, model=None, first=False, raise_absent=False, path=None, vfilter=None):
    return __GET_GLOBAL_FLANGE().get(key, model, first, raise_absent, path, vfilter)

def register_model(name, schema, factory, research=True):
    return __GET_GLOBAL_FLANGE().register_model(name, schema, factory, research)





def merge(dicts, unflatten_separator=None, strategy=anyconfig.MS_DICTS_AND_LISTS):
    '''
    Merge a list of dicts into a composite dict

    :param sources: list of dicts
    :param unflatten_separator: if provided will expand compound keys into nested dicts
    :param strategy: merge strategy
    :return: composite dict, list of any dicts that failed to merge
    '''

    merged = {}
    failed = []
    for d in dicts:
        try:
            anyconfig.merge(merged, unflatten(d, unflatten_separator), ac_merge=anyconfig.MS_DICTS_AND_LISTS)
        except:
            print
            failed.append(d)


    return merged, failed



def unflatten(data, separator='.', replace=True):
    '''
    Expand all compound keys (at any depth) into nested dicts
    
        In [13]: d  = {'test.test2': {'k1.k2': 'val'}}
        In [14]: flange.expand(d)
        Out[14]: {'test.test2': {'k1': {'k2': 'val'}}}

    :param data: input dict
    :param separator: separator in compound keys
    :param replace: if true, remove the compound key. Otherwise the value will
    exist under the compound and expanded key
    :return: copy of input dict with expanded keys
    '''
    if not separator:
        return data
    return iterutils.remap({'temp':data}, visit=lambda p, k, v: __expand_keys(k, v, separator, replace))['temp']



def __expand_keys(k, v, separator, replace):
    if isinstance(v, dict):
        newvalue = v.copy()
        for dkey, dvalue in v.items():
            if replace:
                del newvalue[dkey]
            anyconfig.set_(
                newvalue,
                dkey.replace(separator, '.') if dkey else dkey,
                dvalue)

        return k, newvalue
    return k, v



class Source(object):

    def __init__(self, uri, ns=None, contents={}, parser=None, error=None):
        self.uri = uri
        self.ns = ns
        self.contents = contents
        self.parser = parser
        self.error = error

        self.paths = []

    def __str__(self):
        return "<Source uri={} ns='{}' size={}>".format(self.uri, self.ns, len(self.contents))

    def add_path(self, path):
        self.paths.append(path)

    def set_contents(self, contents, parser=None):
        """
        Set the dict like contents adding under the namespace if there is one
        :param contents: contents of resource at uri in dict form
        :param parser: Currently this is just the anyconfig parser name
        :return: None
        """
        self.contents = {self.ns: contents} if self.ns else contents
        self.parser = parser

    def add_path_visited(self, path_no_ns, key):
        """
        Add to paths list from inputs given by iterutils.visit
        :param path_no_ns: path tuple not including key
        :param key: key
        :return: None
        """
        self.add_path((self.ns,) + path_no_ns + (key,) if self.ns else path_no_ns + (key,))


    def parse(self, parser=None):

        def filter_and_index(source, p,k,v):
            if not VALID_KEY_FUNC(k):
                return False
            source.add_path_visited(p, k)
            return k, v

        d = anyconfig.load(self.uri, ac_parser=parser, ac_ordered=True)

        self.set_contents(
            iterutils.remap(d, lambda p, k, v: filter_and_index(self, p, k, v)),
            parser if parser else os.path.splitext(self.uri)[1].strip('.'))
        # print '\n\n\naccepted:\n', d


    @staticmethod
    def from_file(full_file_path, ns):

        s = Source(full_file_path, ns)

        try:
            s.parse()

        except Exception as e:
            # if the file had a known extension but didn't parse, raise an exception. The danger is that
            # it be parsed incorrectly as properties file which seems to match everything
            ext = os.path.splitext(full_file_path)[1][1:]
            if [lext for lext in PARSABLES.values() if ext in lext]:
                s.error = e
                # print 'exception parsing {}\t{}'.format(ext, e)
                return s

            for p in PARSABLES.keys():
                try:
                    s.parse(p)
                    break
                except Exception as e:
                    # print 'exception parsing as ', p, ' ', e
                    pass

        # print 'returning s\n', s
        return s



# {'src': 'os', 'ns': 'os', 'dict': d, 'ac_parser': None, 'paths': []}


class Cfg(object):
    
    def __init__(self, 
                data=None,
                include_os_env=True,
                research_models=True,
                model_specs=None,
                root_ns='',
                base_dir='.',
                file_patterns=DEFAULT_FILE_PATTERNS,
                file_exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
                file_search_depth=1,
                file_ns_from_dirname=True,
                unflatten_separator='__'):


        self.unflatten_separator=unflatten_separator
        self.base_dir=base_dir
        self.file_patterns=file_patterns
        self.file_exclude_patterns=file_exclude_patterns
        self.file_search_depth=file_search_depth
        self.file_ns_from_dirname=file_ns_from_dirname
        self.include_os_env=include_os_env
        self.root_ns=root_ns
        self.init_data = {}
        self.sources = []
        # dicts = []


        self.add_file_set(
            root_ns=root_ns,
            base_dir=base_dir,
            file_patterns=file_patterns,
            file_exclude_patterns=file_exclude_patterns,
            file_search_depth=file_search_depth,
            file_ns_from_dirname=file_ns_from_dirname,
            unflatten_separator=unflatten_separator
        )

        if self.include_os_env:
            d = os.environ.copy()
            # dicts.append(d)
            self.sources.append(Source('os_env', 'os', d))

        if data:
            self.init_data = data
            # dicts.append(data)
            self.sources.append(Source('init_data', '', data))


        self.merge_sources()

        if research_models:
            self.research_models()

        else:
            self.models = InstanceRegistry(PLUGIN_SCHEMA, Cfg.__create_registry_from_config)


    def merge_sources(self):
        self.data, self.failed = merge(
            [s.contents for s in self.sources],
            self.unflatten_separator)


    def add_file_set(
            self,
            data=None,
             root_ns='',
             base_dir='~',
             file_patterns=DEFAULT_FILE_PATTERNS,
             file_exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
             file_search_depth=1,
             file_ns_from_dirname=True,
             unflatten_separator='__'):

        if file_patterns:
            if isinstance(base_dir, six.string_types):
                base_dir = [base_dir]

            for dir in base_dir:
               self.sources.extend(Cfg.__get_file_sources(
                    base_dir=os.path.expanduser(dir),
                    include=file_patterns,
                    exclude=file_exclude_patterns,
                    search_depth=file_search_depth,
                    ns=root_ns,
                    ns_from_dirname=file_ns_from_dirname))


            # for f in matching_files:
            #     s = Flange.__get_file_source(f, ns_from_dirname=file_ns_from_dirname)
            #     self.sources.append(s)

            self.merge_sources()


                # dicts = []
        # for s in new_sources:
        #     self.sources.append(s)
        #     d = {s['ns']: s['dict']} if s['ns'] else s['dict']
        #     if root_ns:
        #         d = {root_ns: d}
        #     dicts.append(d)
        #
        # new_merged, new_failed = merge(dicts, unflatten_separator)
        # # print 'final merge of {} and {} '.format(type(new_merged), type(self.data))
        # self.data, ignore = merge(dicts=[self.data, new_merged], unflatten_separator=None)
        # # print 'self.data now {} '.format(type(self.data))
        # self.failed.extend(new_failed)



    def register_model(self, name, schema, factory, research=True):

        if not self.models:
            self.models = InstanceRegistry(PLUGIN_SCHEMA, Cfg.__create_registry_from_config)

        self.models.registerInstance(name, InstanceRegistry(schema, factory))

        if research:
            self.models.get(name).research(self.data)


    def research_models(self):

        # Keep a special instance registry that registers models. Use it to discover configuration
        # that defines other type of models with a schema and a factory.
        self.models = InstanceRegistry(PLUGIN_SCHEMA, Cfg.__create_registry_from_config)

        for k,v in DEFAULT_PLUGINS.items():
            self.models.registerInstance(k, v)

        self.models.research(self.data)

        for modelname in self.models.list():
            model = self.models.get(modelname)
            model.research(self.data)




    def info(self):

        print('\nmodels:')
        for name, reg in self.models.registrations.items():
            print("{0:20} instances: {1}".format(name.strip(), ','.join(reg['cached_obj'].list())))    # name.strip(), '\tinstances:', ','.join(reg['cached_obj'].list()))

        print('\nbase dir: \t{}\nsearch depth: \t{}\nfile include patterns: \t{}\nfile exclude patterns: \t{}'.format(
            self.base_dir , self.file_search_depth, self.file_patterns, self.file_exclude_patterns))

        print('\nsources:')
        for src in self.sources:
            print("{0:20} {1}".format(src.parser, src.uri))



    def register(self, name, schema, factory=None, replace=False):

        if not replace and self.models.get(name):
            raise ValueError('model {} already registered'.format(name))

        if not factory:
            # if no factory is given, use an identity factory
            factory = lambda x: x;

        reg = InstanceRegistry(schema, factory);
        reg.research(self.data)
        self.models.registerInstance(name, reg)
        return reg


    def source(self, uri, ns=None, model=None, model_key=None, validate=False, overwrite=False):

        new_source = None

        # handle case where uri+ns combo has already been sourced
        same = [x for x in self.sources if x.uri == uri and x.ns == ns]
        if same:
            if not overwrite:
                raise ValueError('{} - {} is already sourced. To replace, pass overwrite=True'.format(ns, uri))
            # Remove existing source
            self.source.remove(same[0])

        # assume src is file for now. In the future determine by uri
        if True:
            new_source = self.__get_file_source(uri, ns)

        if model:
            self.models.get(model, raise_absent=True).registerContents(
                model_key if model_key else uri,
                new_source.contents,
                validate)

        self.sources.append(new_source)
        return new_source


    def list(self, name):
        registry = self.models.get(name)
        if registry:
            return registry.list()


    def locate(self, data_path, separator='.'):

        if isinstance(data_path, six.string_types):
            p = tuple(data_path.split(separator))
        else:
            # assume already in tuple form
            p = data_path

        return [src.uri for src in self.sources if 'paths' in src and p in src.paths]


    def search(self, pattern, exact=False, keys=True, values=False, path=None):
        return iterutils.search(self.data, pattern, exact, keys, values, path)
    
    
    def get(self, key, model=None, first=False, raise_absent=False, path=None, vfilter=None):
        if model:
            if model not in self.models.list():
                raise ValueError("no model named '{}'".format(model))
            return self.models.get(model).get(key)
        else:
            return iterutils.get(self.data, key, first, raise_absent, path, vfilter)

    
    def mget(self, config_key=None, model=None, vfilter=None, raise_absent=False):
        """
            Get a matching instance from the model registries

        :param config_key: optional. The config key for the model instance
        :param model:  optional. Specify the model explicitly
        :param vfilter: optional. list of terms that must appear in the model instance config
        :return: a matching instance from the model registry(ies)
        """
    
        if model:
            # print('getting by model name ', model_name
            if model not in self.models.list():
                raise ValueError("no model named '{}'".format(model))

            models = [model]
        else:
            models = self.models.list()



        # Search all models for the config key
        l = [i for i in [self.models.get(m).get(config_key, vfilter=vfilter) for m in models] if i]


        if len(l) == 0:
            if raise_absent:
                raise ValueError('no match found')
            return
        elif len(l) > 1:
            raise ValueError('multiple matches found')

        return l[0]




    @staticmethod
    def __get_file_source(filename, ns=None, ns_from_dirname=True):

        full_file_path = os.path.realpath(os.path.expanduser(filename))
        if not ns:
            ns = os.path.split(os.path.dirname(full_file_path))[-1].strip('.') if ns_from_dirname else ''
        return Source.from_file(full_file_path, ns)


    @staticmethod
    def __get_file_sources(
            base_dir=os.path.expanduser('~'),
            include=DEFAULT_FILE_PATTERNS,
            exclude=DEFAULT_EXCLUDE_PATTERNS,
            search_depth=1,
            ns=None,
            ns_from_dirname=True):

        sources = []
        for root, dirnames, filenames in os.walk(base_dir, topdown=True):

            # print 'walk: {}. {}. {}'.format(root, dirnames, filenames)

            depth = root.count(os.sep) - base_dir.count(os.sep)
            if depth >= search_depth:
                del dirnames[:]

            # remove excluded directories and files
            for e in exclude:
                for d in [dirname for dirname in fnmatch.filter(dirnames, e)]:
                    dirnames.remove(d)
                for f in [filename for filename in fnmatch.filter(filenames, e)]:
                    filenames.remove(f)

            to_include = set()
            for p in include:
                for filename in fnmatch.filter(filenames, p):
                    to_include.add(os.path.join(root, filename))

            for s in to_include:
                sources.append(Cfg.__get_file_source(s, ns=ns, ns_from_dirname=ns_from_dirname))

        return sources






    @staticmethod
    def __create_registry_from_config(config):

        if isinstance(config['schema'], six.string_types):
            # parse schema as a url of a method that returns the schema
            schema = pyurl.get(config['schema'])()
        else:
            # otherwise assume this is the schema itself as a dict
            schema = config['schema']

        return InstanceRegistry(
            schema,
            pyurl.get(config['factory']))

