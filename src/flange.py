
import anyconfig, os, fnmatch, string, six
from util import iterutils, registry, url_scheme_python as pyurl
from util.registry import InstanceRegistry, LOG_REGISTRY



PARSABLES = {
    'pickle':['p','pickle'],
    'xml':['xml'],
    'yaml':['yml','yaml'],
    'json':['json'],
    'ini':['ini'],
    'properties':['props','properties'],
    'shellvars':['env']}

DEFAULT_EXCLUDE_PATTERNS = ['*.tar','*.jar','*.zip','*.gz','*.swp','node_modules','target','.idea']
DEFAULT_FILE_PATTERNS = ['*.yml','*.cfg','*settings*','*config*','*properties*']
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






def from_file(filename, root_ns=None, file_ns_from_dirname=False):
    path, basename = os.path.split(os.path.realpath(os.path.expanduser(filename)))
    return Flange(root_ns=root_ns, file_ns_from_dirname=file_ns_from_dirname, include_os_env=False, base_dir=path, file_patterns=[basename])

def from_dict(d):
    return Flange(data=d, file_patterns=None)




def search(data, pattern, exact=True, keys=True, values=False, path=None):
    '''
    
    :param data: 
    :param pattern: 
    :param exact: search term must exactly match the key or value 
    :param keys: match against keys
    :param values: match against values
    :param path: search parameter relating to the nesting of dicts. match against given key hierarchy/sequence/path   
    :return: list of matches in the form ((path nesting sequence), value)
    '''
    if exact:
        search_func = lambda p,k,v: (keys == True and pattern == k) or (values == True and pattern == v)
    else:
        search_func = lambda p,k,v: (keys == True and pattern in k) or (values == True and pattern in v)

    # return [x for x in iterutils.research(data, query=search_func, reraise=False) if path and path in x[0]]
    return iterutils.research(data, query=search_func, reraise=False)



def get(data, key, first=False, raise_absent=False, path=None):
    '''
    
    :param data: 
    :param config_key: 
    :param first: 
    :param raise_absent: 
    :param path: see search method 
   :return: value at given key. None if no match found. 
    '''
    matches = search(data, key, exact=True, values=False, path=path)
    if matches:
        if len(matches)>1 and not first:
            raise ValueError('multiple matches found: ' + str([m[0] for m in matches]))
        return matches[0][1]
    if raise_absent:
        raise ValueError('key not found: {}'.format(key))





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




class Flange(object):
    
    def __init__(self, 
                data=None,
                root_ns='',
                model_specs=None, 
                base_dir='~',
                file_patterns=DEFAULT_FILE_PATTERNS,
                file_exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
                file_search_depth=1,
                file_ns_from_dirname=True,
                include_os_env=True,
                unflatten_separator='__'):

        self.include_os_env=include_os_env,
        self.unflatten_separator=unflatten_separator
        self.base_dir=os.path.expanduser(base_dir)
        self.file_patterns=file_patterns
        self.file_exclude_patterns=file_exclude_patterns
        self.file_search_depth=file_search_depth
        self.file_ns_from_dirname=file_ns_from_dirname
        self.include_os_env=include_os_env
        self.root_ns=root_ns
        self.init_data = {}



        if data:
            self.init_data = data
            self.sources = [{'src':'python','ns':'','dict':data,'ac_parser':None}]
        else:
            self.sources = []

        if self.file_patterns:
            self.sources.extend(Flange.__get_file_sources(
                base_dir=self.base_dir,
                include=self.file_patterns,
                exclude=self.file_exclude_patterns,
                search_depth=self.file_search_depth,
                ns_from_dirname=self.file_ns_from_dirname))
        if self.include_os_env:
            self.sources.append({'src':'os','ns':'_SHELL','dict':os.environ.copy(),'ac_parser':None})


        # merge the init data and the sources. The sources are added under the namespace if provided
        # but the init_data is taken as is
        dicts = [self.init_data]
        for s in self.sources:
            d = {s['ns']: s['dict']} if s['ns'] else s['dict']
            if root_ns:
                d = {root_ns: d}
            dicts.append(d)

        self.data, self.failed = merge(dicts, unflatten_separator)


        # Keep a special instance registry that registers models. Use it to discover configuration
        # that defines other type of models with a schema and a factory. Th
        self.models = InstanceRegistry(PLUGIN_SCHEMA, Flange.__create_registry_from_config)
        self.models.registerInstance('logger', LOG_REGISTRY)
        self.models.research(self.data)

        for modelname in self.models.list():
            model = self.models.get(modelname)
            model.research(self.data)



    def info(self):
        import pprint

        print('\nmodels:')
        for name, reg in self.models.registrations.items():
            print("{}\t\tinstances: {}".format(name.strip(), ','.join(reg['cached_obj'].list())))    # name.strip(), '\tinstances:', ','.join(reg['cached_obj'].list()))

        print('\nbase dir: \t{}\nfile patterns: \t{}\nsearch depth: \t{}'.format(self.base_dir , self.file_patterns, self.file_search_depth))

        print('\nsources:')
        for src in self.sources:
            print("{}\t\t{}".format(src['ac_parser'],src['src']))



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


    def source(self, src, model=None, ns=None):

        # assume src is file for now
        sd = self.__get_file_source(src, ns)
        if model:
            self.models.get(model, raise_absent=True).validate(sd['dict'])
        if sd not in self.sources:
            self.sources.append(sd)
        return sd


    def list(self, name):
        registry = self.models.get(name)
        if registry:
            return registry.list()


    def search(self, pattern, exact=True, keys=True, values=False, path=None):
        return search(self.data, pattern, exact, keys, values, path)
    
    
    def get(self, key, model=None, first=False, raise_absent=False, path=None):
        if model:
            if model not in self.models.list():
                raise ValueError("no model named '{}'".format(model))
            return self.models.get(model).get(key)
        else:
            return get(self.data, key, first, raise_absent, path)

    
    def mget(self, config_key=None, model=None):
    
        if model:
            # print('getting by model name ', model_name
            if model not in self.models.list():
                raise ValueError("no model named '{}'".format(model))
            return self.models.get(model).get(config_key)
    
        else:
            # Search all models for the config key
            l = [i for i in [self.models.get(m).get(config_key) for m in self.models.list()] if i]
            if len(l) == 0:
                raise ValueError('no match found')
            elif len(l) > 1:
                raise ValueError('multiple matches found')
    
            return l[0]



    @staticmethod
    def __get_file_source(filename, ns=None, ns_from_dirname=True):

        full_file_path = os.path.realpath(os.path.expanduser(filename))

        ext = os.path.splitext(full_file_path)[1][1:]
        # if ext in DEFAULT_EXCLUDE_EXTENSIONS:
        #     return

        if not ns:
            ns = os.path.split(os.path.dirname(full_file_path))[-1].strip('.') if ns_from_dirname else ''

        s = {'src':full_file_path, 'ns':ns, 'dict': {}}

        try:
            s['dict'] = anyconfig.load(s['src'])
            s['ac_parser'] = ext

        except Exception as e:
            # if the file had a known extension but didn't parse, raise an exception. The danger is that
            # it be parsed incorrectly as properties file which seems to match everything
            if [lext for lext in PARSABLES.values() if ext in lext]:
                s['dict'] = None
                s['ac_parser'] = None
                s['error'] = e
                return

            for p in PARSABLES.keys():
                try:
                    d = anyconfig.load(s['src'], ac_parser=p)

                    filtered = iterutils.remap(d, lambda p,k,v: VALID_KEY_FUNC(k))
                    if len(filtered):
                        s['dict'] = filtered
                        s['ac_parser'] = p
                    break
                except Exception as e:
                    # print('exception parsing as ', p, ' ', e
                    pass

        return s


    @staticmethod
    def __get_file_sources(
            base_dir=os.path.expanduser('~'),
            include=DEFAULT_FILE_PATTERNS,
            exclude=DEFAULT_EXCLUDE_PATTERNS,
            search_depth=1,
            ns_from_dirname=True):

        sources = []
        for root, dirnames, filenames in os.walk(base_dir, topdown=True):
            depth = root.count(os.sep) - base_dir.count(os.sep)
            if  depth >= search_depth:
                del dirnames[:]

            # remove excluded directories and files
            for e in exclude:
                for d in [dirname for dirname in fnmatch.filter(dirnames, e)]:
                    dirnames.remove(d)
                for f in [filename for filename in fnmatch.filter(filenames, e)]:
                    filenames.remove(f)

            for p in include:
                for filename in fnmatch.filter(filenames, p):
                    # append the file source, using the dir as the namespace only
                    # ns_from_dirname = ns_from_dirname and depth>0
                    s = Flange.__get_file_source(os.path.join(root, filename), ns_from_dirname=ns_from_dirname)
                    if s and len(s['dict']):
                        # print('{} adding keys {}'.format(os.path.join(root, filename), s['dict'].keys())
                        sources.append(s)

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

