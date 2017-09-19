
import anyconfig, os, datetime, copy, fnmatch
import iterutils, six
import string


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

    return [x for x in iterutils.research(data, query=search_func, reraise=False) if path and path in x[0]]



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




def research_models(data, model_specs):
    models = ModelRegistry(data)
    for name, spec in model_specs.iteritems():
        models.register(name, spec, True, True)
    return models




def gather_data(
        include_env=True,
        expand_separator='__',
        base_dir=os.path.expanduser('~'),
        file_patterns=DEFAULT_FILE_PATTERNS):

        sources = []
        if file_patterns:
            sources.extend(get_file_sources(base_dir, file_patterns))
        if include_env:
            sources.append({'src':'os','ns':'_SHELL','dict':os.environ.copy(),'ac_parser':None})

        merged = {}
        for s in sources:
            d = {s['ns']:s['dict']} if s['ns'] else s['dict']
            anyconfig.merge(merged, d, ac_merge=anyconfig.MS_DICTS_AND_LISTS)

        # separate any x__y__z keys into x: {y: {z: val}}}
        if expand_separator:
            merged = expand(merged, expand_separator)

        return merged, sources



def __expand_value_dict(k,v,separator):
    if isinstance(v, dict):
        newvalue = v.copy()
        for dkey, dvalue in v.iteritems():
            anyconfig.set_(newvalue, dkey.replace(separator, '.'), dvalue)
        return k, newvalue
    return k, v



# Expand a flat list of variables into nested dicts
def expand(data, separator='.'):
    return iterutils.remap(data, visit=lambda p,k,v: __expand_value_dict(k,v,separator) )



def get_file_source(f, ns_from_dirname=True):

    ext = os.path.splitext(f)[1][1:]
    if ext in DEFAULT_EXCLUDE_EXTENSIONS:
        return

    s = {'src':f,
        'ns':os.path.split(os.path.dirname(f))[-1].strip('.') if ns_from_dirname else '',
        'dict': {}}

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
        search_depth=1):

    sources = []
    for root, dirnames, filenames in os.walk(base_dir, topdown=True):
        depth = root.count(os.sep) - base_dir.count(os.sep)
        if  depth >= search_depth:
            del dirnames[:]
        for p in patterns:
            for filename in fnmatch.filter(filenames, p):
                # append the file source, using the dir as the namespace only
                s = get_file_source(os.path.join(root, filename),depth>0)
                if s and len(s['dict']):
                    # print '{} adding keys {}'.format(os.path.join(root, filename), s['dict'].keys())
                    sources.append(s)

    return sources



import jsonschema

def validate(d, spec):
    try:
        jsonschema.validate(d, spec)
        return True
    except:
        return False




from flange_models import model_specs



class Registry(object):
    '''
        Base class for model and object registries
    '''
    def get_registration(self, config_key, raise_absent=False):

        if len(self.registrations) == 0 or (config_key and config_key not in self.registrations):
            if raise_absent:
                raise ValueError("no match found for config key {}".format(config_key))
            else:
                return

        if config_key:
            return self.registrations[config_key]
        else:
            if len(self.registrations) == 1:
                return self.registrations.values()[0]
            else:
                raise ValueError("Multiple valid configurations exist. Config id/key must be specified")

    def list(self):
        return self.registrations.keys()


    def get(self, config_key=None, raise_absent=False):
        return self.get_registration(config_key, raise_absent)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<{} contents={}>".format(self.__class__.__name__ , self.registrations.keys())



class ModelRegistry(Registry):

    def __init__(self, data=globals()):
        self.data = data
        self.registrations = {}

    def register(self, name, model_spec, cache, mutable):
        # print 'searching for valid %s configurations ' % name
        object_map = {}
        for result in iterutils.research(self.data, query=lambda p,k,v: validate(v, model_spec['config_model']), reraise=False):

            # print 'found at %s' % str(result[0])
            object_map[result[0][-1]] = {
                'cached_obj': None,
                'cached_since': None,
                'config_source': 'unknown',
                'config_path': 'unknown',
                'config_data': result[1] if mutable else copy.deepcopy(result[1]), # this is the actual config object. intentionally mutable but beware
                'create_func': lambda d: model_spec['create_func'](d)}

        self.registrations[name] = InstanceRegistry(name, object_map, cache, mutable);
        # self.__dict__.update(**{name:self.registrations[name]})




# Construct a registry class that closes overs the creation function map
class InstanceRegistry(Registry):

    def __init__(self, id, object_map, cache, mutable):
        self.id = id
        self.registrations = object_map
        self.cache = cache
        self.mutable = mutable


    def info(self, config_key):

        reg =  self.get_registration(config_key)
        if reg:
            d =  dict(reg)
            del d['create_func']
            d['config_data'] = dict(d['config_data'])
            d['cache'] = self.cache
            return d


    def update(self, config_key, **kargs):

        if not self.mutable:
            raise Exception('Registry configured as immutable')

        reg = self.get_registration(config_key)
        for key, value in kargs.iteritems():
            # Just put in whatever is given. If its a new key it will be added
            reg['config_data'][key] = value

        return self.info(config_key)


    def get(self, config_key=None):

        reg = self.get_registration(config_key)
        if reg:
            if not self.cache:
                return reg['create_func'](reg['config_data'])

            if not reg['cached_obj']:
                reg['cached_obj'] = reg['create_func'](reg['config_data'])
                reg['cached_since']= datetime.datetime.now()

            return reg['cached_obj']





class Flange(object):
    
    def __init__(self, data=None, model_specs=None):

        self.include_env=True,
        self.expand_separator='__'
        self.base_dir=os.path.expanduser('~')
        self.file_patterns=DEFAULT_FILE_PATTERNS
        
        if data:
            self.data = data
            self.sources = [{'src':'python','ns':'','dict':data,'ac_parser':None}]
        else:
            self.data, self.sources = gather_data(
                self.include_env,
                self.expand_separator,
                self.base_dir,
                self.file_patterns)

        if model_specs:
            self.model_specs = model_specs
        else:
            import flange_models
            self.model_specs = flange_models.model_specs

        self.models = research_models(self.data, self.model_specs)


    def search(self, pattern, exact=True, keys=True, values=False, path=None):
        search(self, self.data, pattern, exact, keys, values, path)
    
    
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
    


# __OBJ__ = Flange()

#
# def globalize_models():
#     for m in models():
#         m.


