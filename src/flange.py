
import anyconfig, os, fnmatch, re, string, six

import iterutils
from registry import InstanceRegistry, LOG_REGISTRY


PARSABLES = {
    'pickle':['p','pickle'],
    'xml':['xml'],
    'yaml':['yml','yaml'],
    'json':['json'],
    'ini':['ini'],
    'properties':['props','properties'],
    'shellvars':['env']}

DEFAULT_EXCLUDE_EXTENSIONS = ['tar','jar','zip','gz','swp']
DEFAULT_FILE_PATTERNS = ['*.yml','*.cfg','*settings*','*config*','*properties*']
VALID_KEY_CHARS = [c for c in string.printable if c not in ['_'] ]
VALID_KEY_FUNC = lambda k: isinstance(k, six.string_types) and len(k)<50 and all(c in string.printable for c in VALID_KEY_CHARS)




def search(data, match_string, exact=True, keys=True, values=False, path=None):
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
        search_func = lambda p,k,v: (keys == True and match_string == k) or (values == True and match_string == v)
    else:
        search_func = lambda p,k,v: (keys == True and match_string in k) or (values == True and match_string in v)

    # return [x for x in iterutils.research(data, query=search_func, reraise=False) if path and path in x[0]]
    return iterutils.research(data, query=search_func, reraise=False)



def get(data, match_key, first=False, raise_absent=False, path=None):
    '''
    
    :param data: 
    :param config_key: 
    :param first: 
    :param raise_absent: 
    :param path: see search method 
   :return: value at given key. None if no match found. 
    '''
    matches = search(data, match_key, exact=True, values=False, path=path)
    if matches:
        if len(matches)>1 and not first:
            raise ValueError('multiple matches found: ' + str([m[0] for m in matches]))
        return matches[0][1]
    if raise_absent:
        raise ValueError('key not found: {}'.format(match_key))




def gather_data(
        include_os_env=True,
        expand_separator='__',
        base_dir=os.path.expanduser('~'),
        file_patterns=DEFAULT_FILE_PATTERNS):

        sources = []
        if file_patterns:
            sources.extend(get_file_sources(base_dir, file_patterns))
        if include_os_env:
            sources.append({'src':'os','ns':'_SHELL','dict':os.environ.copy(),'ac_parser':None})

        merged = {}
        for s in sources:
            d = {s['ns']:s['dict']} if s['ns'] else s['dict']
            anyconfig.merge(merged, d, ac_merge=anyconfig.MS_DICTS_AND_LISTS)

        # separate any x__y__z keys into x: {y: {z: val}}}
        if expand_separator:
            merged = expand(merged, expand_separator)

        return merged, sources




def get_os_env_source():
    return {'src':'os','ns':'_SHELL','dict':os.environ.copy(),'ac_parser':None}


def get_merged_source_data(init_data, sources, expand_separator):

    # first merge to get a copy of initial data
    merged = {}
    anyconfig.merge(
        merged,
        init_data,
        ac_merge=anyconfig.MS_DICTS_AND_LISTS)

    # then merge in every source dict
    for s in sources:
        d = {s['ns']:s['dict']} if s['ns'] else s['dict']
        anyconfig.merge(merged, d, ac_merge=anyconfig.MS_DICTS_AND_LISTS)

    # finally separate any x__y__z keys into x: {y: {z: val}}}
    # wrap the input dict to get the top level key expanded. Otherwise it's skipped by iterutils
    if expand_separator:
        merged = expand({'temp':merged}, expand_separator)['temp']
        # merged = expand(merged, expand_separator)

    return merged




def __expand_value_dict(k,v,separator):
    if isinstance(v, dict):
        newvalue = v.copy()
        for dkey, dvalue in v.iteritems():
            anyconfig.set_(
                newvalue,
                dkey.replace(separator, '.') if dkey else dkey,
                dvalue)
        return k, newvalue
    return k, v



# Expand a flat list of variables into nested dicts
def expand(data, separator='.'):
    return iterutils.remap(data, visit=lambda p,k,v: __expand_value_dict(k,v,separator) )



def get_file_source(filename, ns=None, ns_from_dirname=True):

    full_file_path = os.path.realpath(os.path.expanduser(filename))

    ext = os.path.splitext(full_file_path)[1][1:]
    if ext in DEFAULT_EXCLUDE_EXTENSIONS:
        return

    if not ns:
        ns = os.path.split(os.path.dirname(full_file_path))[-1].strip('.') if ns_from_dirname else ''

    s = {'src':full_file_path, 'ns':ns, 'dict': {}}

    try:
        s['dict'] = anyconfig.load(s['src'])
        s['ac_parser'] = ext

    except:
        # if the file had a known extension but didn't parse, raise an exception. The danger is that
        # it be parsed incorrectly as properties file which seems to match everything
        if [lext for lext in PARSABLES.values() if ext in lext]:
            raise

        for p in PARSABLES.keys():
            try:
                d = anyconfig.load(s['src'], ac_parser=p)

                filtered = iterutils.remap(d, lambda p,k,v: VALID_KEY_FUNC(k))
                if len(filtered):
                    s['dict'] = filtered
                    s['ac_parser'] = p
                break
            except Exception as e:
                # print 'exception parsing as ', p, ' ', e
                pass

    return s


def get_file_sources(
        base_dir=os.path.expanduser('~'),
        patterns=DEFAULT_FILE_PATTERNS,
        search_depth=1,
        ns_from_dirname=True):

    sources = []
    for root, dirnames, filenames in os.walk(base_dir, topdown=True):
        depth = root.count(os.sep) - base_dir.count(os.sep)
        if  depth >= search_depth:
            del dirnames[:]
        for p in patterns:
            for filename in fnmatch.filter(filenames, p):
                # append the file source, using the dir as the namespace only
                # ns_from_dirname = ns_from_dirname and depth>0
                s = get_file_source(os.path.join(root, filename), ns_from_dirname=ns_from_dirname)
                if s and len(s['dict']):
                    # print '{} adding keys {}'.format(os.path.join(root, filename), s['dict'].keys())
                    sources.append(s)

    return sources




import url_scheme_python as pyurl


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


def create_registry_from_config(config):

    if isinstance(config['schema'], six.string_types):
        # parse schema as a url of a method that returns the schema
        schema = pyurl.get(config['schema'])()
    else:
        # otherwise assume this is the schema itself as a dict
        schema = config['schema']

    return InstanceRegistry(
        schema,
        pyurl.get(config['factory']))



def from_file(filename, root_ns=None, file_ns_from_dirname=False):
    path, basename = os.path.split(os.path.realpath(os.path.expanduser(filename)))
    return Flange(root_ns=root_ns, file_ns_from_dirname=file_ns_from_dirname, include_os_env=False, base_dir=path, file_patterns=[basename])



class Flange(object):
    
    def __init__(self, 
                data=None,
                root_ns='',
                model_specs=None, 
                base_dir=os.path.expanduser('~'), 
                file_patterns=DEFAULT_FILE_PATTERNS,
                file_search_depth=1,
                file_ns_from_dirname=True,
                include_os_env=True,
                expand_separator='__'):

        self.include_os_env=include_os_env,
        self.expand_separator=expand_separator
        self.base_dir=base_dir
        self.file_patterns=file_patterns
        self.file_search_depth=file_search_depth
        self.file_ns_from_dirname=file_ns_from_dirname
        self.include_os_env=include_os_env
        self.root_ns=root_ns
        self.init_data = {}
        self.registries = {}



        if data:
            self.init_data = data
            self.sources = [{'src':'python','ns':'','dict':data,'ac_parser':None}]
        else:
            # self.data, self.sources = gather_data(
            #     self.include_os_env,
            #     self.expand_separator,
            #     self.base_dir,
            #     self.file_patterns)

            self.sources = []
            if self.file_patterns:
                self.sources.extend(get_file_sources(self.base_dir,self.file_patterns,self.file_search_depth,self.file_ns_from_dirname))
            if self.include_os_env:
                self.sources.append(get_os_env_source())


        # make the root key equal to root_ns if set
        # if self.root_ns and not self.root_ns in self.init_data or len(self.init_data.keys()) != 1:
        #     d = {self.root_ns: self.init_data}
        # else:
        #     d = self.init_data

        self.data = get_merged_source_data(self.init_data, self.sources, self.expand_separator)
        if self.root_ns and (not self.root_ns in self.init_data or len(self.init_data.keys()) != 1):
            temp = {}
            # use anyonfig set to expand the root_ns key
            anyconfig.set_(
                temp,
                self.root_ns.replace(self.expand_separator, '.'),
                self.data)
            self.data = temp


        # Keep a special instance registry that registers models. Use it to discover configuration
        # that defines other type of models with a schema and a factory. Th
        self.models = InstanceRegistry(PLUGIN_SCHEMA, create_registry_from_config)
        self.models.registerInstance('logger', LOG_REGISTRY)
        self.models.research(self.data)

        for modelname in self.models.list():
            model = self.models.get(modelname)
            model.research(self.data)


        # For any model plugins found, research the data looking for instances
        # for plugin_key in self.get_registration('model_plugins').list():
        #     plugin = self.registrations.get(plugin_key)
        #     self.register(plugin_key, plugin.schema, plugin.factory)






    def search(self, pattern, exact=True, keys=True, values=False, path=None):
        return search(self.data, pattern, exact, keys, values, path)
    
    
    def get(self, config_key, first=False, raise_absent=False, path=None):
        return get(self.data, config_key, first, raise_absent, path)

    
    def mget(self, config_key=None, model_name=None):
    
        if model_name:
            # print 'getting by model name ', model_name
            if model_name not in self.models.list():
                raise ValueError("no model named '{}'".format(model_name))
            return self.models.get(model_name, raise_absent=True).get(config_key)
    
        else:
            # Search all models for the config key
            l = [i for i in [self.models.get(m).get(config_key) for m in self.models.list()] if i]
            if len(l) == 0:
                raise ValueError('no match found')
            elif len(l) > 1:
                raise ValueError('multiple matches found')
    
            return l[0]
    

