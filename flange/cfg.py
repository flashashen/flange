
import os, fnmatch, string, six
from . import iterutils, model as flmd
from .source import Source
import anyconfig



DEFAULT_EXCLUDE_PATTERNS = ['*.tar','*.jar','*.zip','*.gz','*.swp','node_modules','target','.idea','*.hide','*save']
DEFAULT_FILE_PATTERNS = ['*.yml','*cfg','*settings','*config','*properties','*props']
VALID_KEY_CHARS = [c for c in string.printable if c not in ['_'] ]
DEFAULT_KEY_FILTER = lambda p, k, v: k == None or isinstance(k, int) or (isinstance(k, six.string_types) and len(k)<50 and all(c in string.printable for c in VALID_KEY_CHARS))
DEFAULT_UNFLATTEN_SEPARATOR = '__'



def from_home_dir(root_path=None, include_os_env=False):
    return Cfg(base_dir='~', root_path=root_path, include_os_env=include_os_env)

def from_file(filename, root_path=None, include_os_env=False):
    path, basename = os.path.split(os.path.realpath(os.path.expanduser(filename)))
    return Cfg(root_path=root_path, include_os_env=include_os_env, base_dir=path, file_patterns=[basename])

def from_dict(d, root_path=None, include_os_env=False):
    return Cfg(data=d, root_path=root_path, file_patterns=None, include_os_env=include_os_env)

def from_os_env(root_path=None):
    return Cfg(root_path=root_path, include_os_env=True, file_patterns=[])




#
#   Provide a Global object for convenience. Shadow the main class methods at the module level.
#

__GLOBAL_CFG = None
def __GET_GLOBAL_FLANGE():
    global __GLOBAL_CFG
    if not __GLOBAL_CFG:
        __GLOBAL_CFG = Cfg()
    return __GLOBAL_CFG

def obj(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().obj(*args, **kwargs)
def objs(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().objs(*args, **kwargs)
def path(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().path(*args, **kwargs)
def paths(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().paths(*args, **kwargs)
def src(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().src(*args, **kwargs)
def srcs(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().srcs(*args, **kwargs)
def uri(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().uri(*args, **kwargs)
def uris(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().uris(*args, **kwargs)
def value(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().value(*args, **kwargs)
def values(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().values(*args, **kwargs)
def get(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().get(*args, **kwargs)
def search(*args, **kwargs):
    return __GET_GLOBAL_FLANGE().search(*args, **kwargs)


def info():
    return __GET_GLOBAL_FLANGE().info()


def get(path, exact=True, unique=True, values=False, raise_absent=False):
    return __GET_GLOBAL_FLANGE().get(path, exact, unique, values, raise_absent=raise_absent)

def register_model(name, model, research=True):
    return __GET_GLOBAL_FLANGE().register_model(name, model, research)



def register_default_model(name, model):

    flmd.DEFAULT_MODELS[name] = model

    # If the global instance is already constructed, then explicitly register and research now
    if __GLOBAL_CFG:
        register_model(name, model)





class Flobject(object):

    def __init__(self, val=None, mregs=None, srcs=None, path=None, wrap=False):

        if wrap:
            # basic wrapper. untested. keep this around for experimentation. This could be used to
            # keep the metadata this class holds in-place in the original data via substitution of the
            # wrapped object. Then an index of paths wouldn't be necessary.
            #
            # copied from:
            #   https://stackoverflow.com/questions/1443129/completely-wrap-an-object-in-python/1445289#1445289
            self.__class__ = type(val.__class__.__name__,
                                  (self.__class__, val.__class__),
                                  {})
            self.__dict__ = val.__dict__


        self.val = val
        self.mregs = mregs if mregs else {}
        self.srcs = srcs if srcs else set()
        self.path = path




    @staticmethod
    def from_path_and_value(pv):
        return Flobject(path=pv[0], val=pv[1])

    def __repr__(self):
        return "<Flobject {}, #srcs={}, #instances={}>".format(self.path, len(self.srcs), len(self.mregs))


    def add_src(self, src):
        self.srcs.add(src)

    def register_model(self, model, v):
        # print 'reg model called on ',  model
        if model.name not in self.mregs:
            self.mregs[model.name] = model.registration(v)


    def val_equals(self, val):
        # print 'assert_val_equals: ', self.val, val
        return self.val == val


    def instance(self, model=None):

        if model:
            if model in self.mregs:
                # try:
                return self.mregs[model].instance()
                # except Exception as e:
                #     print e


        elif len(self.mregs) == 1:
            return list(self.mregs.values())[0].instance()

        if len(self.mregs) > 1:
            raise ValueError('multiple registrations. Must specify model name from :{}'.format(self.mregs))





class Cfg(object):
    
    def __init__(self, 
                data=None,
                include_os_env=True,
                root_path=None,
                base_dir='.',
                file_patterns=DEFAULT_FILE_PATTERNS,
                file_exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
                file_search_depth=0,
                unflatten_separator=DEFAULT_UNFLATTEN_SEPARATOR,
                key_filter=DEFAULT_KEY_FILTER,
                src_post_proc=None,
                gather=True,
                merge=True,
                research=True,):
        """

        :param data: initial data. This is merged as is without regard to root_path
        :param include_os_env:
        :param research_models:
        :param root_path: the namespace/key under which to add all loaded config/data. If model instances are defined at top level this will be needed
        :param base_dir: directory or list of directories to search for config/data. ** order matters! later entries override earlier.
        :param file_patterns:
        :param file_exclude_patterns:
        :param file_search_depth:
        :param unflatten_separator:
        """

        # save params
        self.unflatten_separator = unflatten_separator
        self.file_patterns = [file_patterns] if isinstance(file_patterns, six.string_types) else file_patterns
        self.file_exclude_patterns = file_exclude_patterns
        self.file_search_depth = file_search_depth
        self.include_os_env = include_os_env
        self.root_path = root_path
        self.init_data = data
        self.gather = gather
        self.merge = merge
        self.research = research

        self.key_filter = key_filter
        self.src_post_proc = src_post_proc

        self.base_dir = base_dir
        if isinstance(self.base_dir, six.string_types):
            self.base_dir = [self.base_dir]

        # init data
        self.data = {}
        self.sources = []
        self.path_index = {}
        self.models = flmd.DEFAULT_MODELS.copy()

        # function to give to Source objects so register themselves with the path_index
        # self.source_indexer = lambda src, p, k, v: self.__visit_index_path(self.path_index, src, p, k, v)


    # conditionally do initial gather, merge and research
        self.refresh(self.gather, self.merge, self.research)



    #
    #
    #   Flange Cfg() init methods
    #
    #

    def refresh(self, gather=False, merge=True, research=True):

        if gather:
            self.gather_sources()
        if merge:
            self.merge_sources()
        if research:
            self.research_models()


    def gather_sources(self):

        if self.sources:
            del self.sources
        if self.path_index:
            del self.path_index
        self.sources = []
        self.path_index = {}
        self.visited_uris = set()


        if self.file_patterns:
            for dir in self.base_dir:
                self.sources.extend(self.__get_file_sources(dir))

        if self.include_os_env:
            # Dont use root path
            self.sources.append(Source('os_env', '', os.environ.copy()))

        if self.init_data:
            # Dont use root path
            self.sources.append(Source('init_data', '', self.init_data))




    def merge_sources(self):

        # process sources with called provided function. This gives the caller a chance to
        # shape things up or set the src path prior to the filter, index and merge
        dlist = []
        for s in self.sources:
            if self.src_post_proc:
                self.src_post_proc(s)

            d = {s.root_path: s.contents} if s.root_path else s.contents
            # print d.keys()
            e = iterutils.unflatten(d, self.unflatten_separator)
            # print 'after unflatten', e
            dlist.append(iterutils.remap(e, reraise_visit=True, enter=lambda p, k, v: self.__filter_and_index(s, p, k, v)))
            # e =  {'test': {'exclude': [['192.168.0.0/16'], ['172.16.0.0/12', '10.0.0.0/8'], '10.1.3.0/24']}}
            # dlist.append(iterutils.remap(e, enter=lambda p, k, v: self.__filter_and_index(s, p, k, v)))


        # then merge, putting the content under the root path for each source
        self.data = {}
        failed = []
        for d in dlist:
            try:
                # print 'merging ', d
                anyconfig.merge(self.data, d)
            except:
                failed.append(d)




    def research_models(self):

        plugins = iterutils.research(
            self.data,
            query=lambda p, k, v: flmd.PLUGIN_MODEL.validator(v))

        for p in plugins:
            self.register_model(p[1]['name'], flmd.PLUGIN_MODEL.factory(p[1]), False)

        iterutils.research(
            self.data,
            query=lambda p, k, v: self.__visit_index_model_instance(self.models.values(), p, k, v))





    #
    #
    #   Primary access methods
    #
    #



    def search(self, path, values=None, unique=False, exact=False, raise_absent=False, vfunc=lambda x: x):
        """
        find matches for the given path expression in the data

        :param path: path tuple or string
        :return:
        """
        path_and_value_list = iterutils.search(
                self.data,
                path=path,
                required_values=values,
                exact=exact)

        # print 'search found ', [x[0] for x in path_and_value_list]

        return self.__return_value(path_and_value_list, unique, raise_absent, vfunc)



    def __return_value(self, l, unique=True, raise_absent=False, vfunc=lambda x: x):

        if l:
            if vfunc:
                l = [y for y in [vfunc(x) for x in l] if y]

            if len(l) > 1 and unique:
                raise ValueError('multiple matches found')

        if not l:
            if raise_absent:
                raise ValueError('no match found')

        else:
            return l[0] if unique else l



    def path(self, path=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, unique=True, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: x[0])
    def paths(self, path=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, unique=False, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: x[0])


    def src(self, path=None, values=None, unique=True, exact=True, raise_absent=False):
        sources = self.search(path=path, unique=unique, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: self.path_index[x[0]].srcs)
        return next(iter(sources))
    def srcs(self, path=None, values=None, unique=True, exact=True, raise_absent=False):
        sources = self.search(path=path, unique=False, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: self.path_index[x[0]].srcs)
        return list(set([src for l in sources for s in l])) if sources else sources


    def uri(self, path=None, values=None, exact=True, raise_absent=False):
        sources = self.search(path=path, unique=True, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: self.path_index[x[0]].srcs)
        return next(iter(sources)).uri
    def uris(self, path=None, values=None, exact=True, raise_absent=False):
        sources = self.search(path=path, unique=False, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: self.path_index[x[0]].srcs)
        return [src.uri for l in sources for src in l] if sources else sources


    # def query_obj(self, model, path_value):
    #     if path_value[0] not in self.path_index:
    #         return None
    #     obj = self.path_index[path_value[0]].instance(model=model)
    #     if
    #     x: self.path_index[path_value[0]].instance(model=model) if path_value[0] in self.path_index else None

    def obj(self, path=None, model=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, exact=exact, unique=True, raise_absent=raise_absent, values=values,
                            vfunc=lambda x: self.path_index[x[0]].instance(model=model) if x[0] in self.path_index else None)
    def objs(self, path=None, model=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, exact=exact, unique=False, raise_absent=raise_absent, values=values,
                       vfunc=lambda x: self.path_index[x[0]].instance(model=model) if x[0] in self.path_index else None)


    def value(self, path=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, unique=True, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: x[1])
    def values(self, path=None, values=None, exact=True, raise_absent=False):
        return self.search(path=path, unique=False, exact=exact, values=values, raise_absent=raise_absent, vfunc=lambda x: x[1])

    def get(self, path=None, values=None, unique=True, exact=True, raise_absent=False):
        return self.path_index[self.search(path=path, unique=unique, exact=exact, values=values, raise_absent=raise_absent)[0]]






    #
    #
    #   Init helper methods and remap callbacks
    #
    #


    def register_model_schema(self, name, schema, factory, research=True):
        self.register_model(
            name,
            flmd.Model(name, flmd.Model.get_schema_validator(schema), factory),
            research)

    def register_model(self, name, model, research=True):
        self.models[name] = model
        if research:
            iterutils.research(
                self.data,
                query=lambda p, k, v: self.__visit_index_model_instance([model], p, k, v))


    def __filter_and_index(self, src, p, k, v):

        # now the root_path/ns has already been accounted for in the data.
        # no prefixing loginc
        # np = (src.root_path,) + p if src.root_path else p
        np = p


        # print '__filter_and_index', p, k
        # filter. func may be provided or be class default
        if self.key_filter and not self.key_filter(np, k, v):
            # print 'filtered out ', np, k
            return v, False

        # index. internal to Cfg class
        full_path = np + (k,)
        if full_path in self.path_index:
            # print 'preexisting index at ', full_path
            if not self.path_index[full_path].val_equals(v):
                # print 'updating index at ', full_path
                # raise ValueError('unexpected value change at path_index[{}]'.format(full_path))
                self.path_index[full_path].add_src(src)
        else:
            # print 'adding index at ', full_path
            self.path_index[full_path] = Flobject(val=v, path=full_path, srcs=set([src]))


        return iterutils.default_enter(p, k, v)


    def __visit_index_model_instance(self, models, p, k, v):
        """
            Called during model research on merged data
        """
            # print 'model visit {} on {}'.format(model, v)
        cp = p + (k,)
        for model in models:
            try:
                if model.validator(v):
                    if cp in self.path_index:
                        # if self.path_index[cp].val != v:
                        #     raise ValueError('unexpected value change at path_index[{}]'.format(cp))
                        self.path_index[cp].register_model(model, v)
                    else:
                        # The object should already be in the index but don't complain for now.
                        self.path_index[cp] = Flobject(val=v, path=cp, regs=[model])
            except:
                pass



    def __get_file_sources(self, topdir):

        sources = []
        topdir = os.path.realpath(os.path.expanduser(topdir))
        start_depth = topdir.count(os.sep)

        # print '__get_file_sources on ', dir
        for root, dirnames, filenames in os.walk(os.path.realpath(os.path.expanduser(topdir)), topdown=True):

            # print 'walk: {}. {}. {}'.format(root, dirnames, filenames)

            depth = root.count(os.sep) - self.base_dir.count(os.sep) - start_depth
            if depth >= self.file_search_depth:
                # print 'depth {} exceeded {} on {}'.format(depth, self.file_search_depth, root)
                del dirnames[:]


            # remove excluded directories and files
            for e in self.file_exclude_patterns:
                for d in [dirname for dirname in fnmatch.filter(dirnames, e)]:
                    dirnames.remove(d)
                for f in [filename for filename in fnmatch.filter(filenames, e)]:
                    # print 'removing ', f
                    filenames.remove(f)

            to_include = set()
            for p in self.file_patterns:
                for filename in fnmatch.filter(filenames, p):
                    to_include.add(os.path.join(root, filename))

            for filename in to_include:
                # print filename
                # Don't add a uri twice
                # print '{} is in {}: {}'.format(filename,  self.visited_uris, filename in self.visited_uris)
                if filename not in self.visited_uris:

                    src = Source.from_file(filename, self.root_path)
                    if src:
                        sources.append(src)
                        self.visited_uris.add(src.uri)

        return sources




    #
    #
    #
    #
    #


    def info(self):


        print('\nconfig:\nbase dir: \t{}\nsearch depth: \t{}\nfile include patterns: \t{}\nfile exclude patterns: \t{}'.format(
            self.base_dir , self.file_search_depth, self.file_patterns, self.file_exclude_patterns))

        print('\n\nmodels:')
        for model in self.models:
            print('\n{}'.format(model))
            for x in self.path_index.values():
                if x.mregs.get(model):
                    print("{0:50} {1}".format('/'.join(x.path), x.mregs.get(model)))

        print('\n\nsources:')
        for src in self.sources:
            print("{0:15.10} {1:60.65} {2}".format(str(src.parser), str(src.uri), 'error: ' + str(src.error) if src.error else ''))










