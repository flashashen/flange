
import logging
from .context import *
import pytest

from flange import dbengine, iterutils, url_scheme_python as pyurl
# from flange import Flange, url_scheme_python as pyurl

# pyurl = url_scheme_python

#.
#   url scheme
#



def get_module_function_test_value():
    return 'module function'

module_name = __name__.replace('.','/')


def test_url_module_function():
    attr = pyurl.get('python://{}.get_module_function_test_value'.format(module_name))
    assert attr() == 'module function'

    attr = pyurl.get('python://{}.get_module_function_test_value()'.format(module_name))
    assert attr == 'module function'


def test_url_class():
    attr = pyurl.get('python://{}.FlangeTestPlugin'.format(module_name))
    assert attr().get_schema__instance()

    attr = pyurl.get('python://{}.FlangeTestPlugin()'.format(module_name))
    assert attr.get_schema__instance()


def test_url_class_functions():
    attr = pyurl.get('python://{}.FlangeTestPlugin().get_schema__instance'.format(module_name))
    assert attr()['type'] == 'object'
    attr = pyurl.get('python://{}.FlangeTestPlugin().get_schema__instance()'.format(module_name))
    assert attr['type'] == 'object'

    attr = pyurl.get('python://{}.FlangeTestPlugin.get_schema__static'.format(module_name))
    assert attr()['type'] == 'object'
    attr = pyurl.get('python://{}.FlangeTestPlugin.get_schema__static()'.format(module_name))
    assert attr['type'] == 'object'



#
#   InstanceRegistry
#



#
#   flange api
#
data = {
    'a':{'a2':{'a3a':'a3aval', 'a3b':'a3aval'}},
    'testlog': {
        'name': 'testlog',
        'level': 'DEBUG',
        'format': "%(asctime)s:%(levelname)s:%(name)s:%(message)s"},
    'testlog2': {
        'name': 'another name',
        'level': 'WARNING',
        'format': "%(asctime)s:%(levelname)s:%(name)s:%(message)s"}
}

f = flange.cfg.Cfg(data=data)

#
#   registry = f.register(schema)
#
#   src_meta = f.source(url_or_file_path, validation_model)
#
#   f.validate(
#




def test_search_key_exact():
    assert f.search('a/a2/a3b')
    assert f.search('a/a2/a3*')
    assert not f.search('a/a2/a3')
    assert not f.search('a/a2/a3b_')


@pytest.mark.xfail(raises=ValueError)
def test_search_key_exact_raise():
    f.search('3b', raise_absent=True)


def test_search_key_fuzzy():
    assert f.search('**/a3b*')
    assert len(f.search('**/a3*', unique=False)) == 2
    assert not f.search('a/a2/a3bx*')
    assert not f.search('a/a2/*XX*')


@pytest.mark.xfail(raises=ValueError)
def test_multiples_raise_when_unique_specified():
    # even with 'p' given, unique means unique
    f.search('**/a3*', unique=True)


@pytest.mark.xfail(raises=ValueError)
def test_search_key_fuzzy_raise():

    assert not f.search('**/XX', raise_absent=True)





def test_model_research():
    assert type(f.obj('testlog')) == logging.Logger


def test_obj_by_name():
    assert(f.obj('testlog'))
    assert(f.obj('testlog2'))
    assert(f.obj('testlog') != f.obj('testlog2'))


def test_obj_by_model():
    # An instance can be fetched by model name. If there are multiple instances a values can be used
    with pytest.raises(ValueError):
        f.obj(model='logger', raise_absent=True)
    assert(f.obj(model='logger', values='DEBUG'))


def test_obj_values():
    # values can be used with or without the config key to retrieve an instance
    assert(f.obj('testlog', values='DEBUG'))
    assert(f.obj('testlog', values='WARNING') == None)

    assert(f.obj('testlog2', values='WARNING'))
    assert(f.obj('testlog2', values='DEBUG') == None)



def test_iter_search():


    # r = iterutils.__query(p, v, k, accepted_keys=None, required_values=None, path=None, exact=True)

    # key
    assert iterutils.__query(('root',), 'testkey', None,
                             'testkey', None, None, True)
    assert iterutils.__query(('root',), 'testkey', None,
                             ['testkey', 'xxx'], None, None, True)
    assert iterutils.__query(('root',), 'testkey', None,
                             'test', None, None, False)
    assert iterutils.__query(('root',), 'testkey', None,
                             ['test', 'xxx'], None, None, False)
    assert not iterutils.__query(('root',), 'testkey', None,
                                 'test', None, None, True)
    assert not iterutils.__query(('root',), 'testkey', None,
                                 'testkeyextra', None, None, True)
    assert not iterutils.__query(('root',), 'testkey', None,
                                 'testkeyextra', None, None, False)

    # path
    assert iterutils.__query(('root',), 'testkey', None,
                             'testkey', None, ('root',), True)
    assert not iterutils.__query(('root',), 'testkey', None,
                                 'testkey', None, ('root', 'sub',), True)

    # val
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, 'val1', None, False)
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, 'val2', None, False)
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, 'val1', None, True)
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, 'va', None, False)
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, '2', None, False)
    assert iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, ['val1', 'val2'], None, True)
    assert not iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                                 None, 'v3', None, False)
    assert not iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                                 None, ['v3'], None, False)
    assert not iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                                 None, 'val', None, True)
    assert not iterutils.__query(('root',),  'testkey', {'k1':'val1', 'k2':'val2'},
                             None, ['val1', 'val2', 'val3'], None, True)



def test_get():

    po = f.fobj('testlog')
    assert po



class FlangeTestPlugin:

    class Inner:
        def m(self):
            pass

    '''
        A class to test providing schema and factory with instance methods, as well
        a test the created object which is an instance of this class. so both the model
        and the instance are provided by this class
    '''

    def __init__(self, value=None):
        self.value = value

    def get_value(self):
        return self.value

    @staticmethod
    def get_schema__static():
        return {
            'type': 'object',
            'properties':{
                'only_FlangeTestPlugin_would_match_this': {'type': 'string'}
            },
            'required': ['only_FlangeTestPlugin_would_match_this']
        }

    def get_schema__instance(self):
        return FlangeTestPlugin.get_schema__static()


    def get_instance(self, params):
        # return an instance of this object with the value given in params
        return FlangeTestPlugin(params['only_FlangeTestPlugin_would_match_this'])



def test_plugin_model():


    data = {

        'test_instance_key': {
            'only_FlangeTestPlugin_would_match_this': 'some value'
        },

        'test_plugin_config_key': {
            'name': 'test_plugin',
            'type': 'FLANGE.TYPE.PLUGIN',
            'schema': {
                'type': 'object',
                'properties':{
                    'only_FlangeTestPlugin_would_match_this': {'type': 'string'}
                },
                'required': ['only_FlangeTestPlugin_would_match_this']
            },
            'factory': 'python://{}.FlangeTestPlugin().get_instance'.format(module_name)
        }
    }

    f = flange.cfg.Cfg(data=data, file_patterns=None)
    # print f.obj('test_instance_key')
    assert f.obj('test_instance_key').get_value() == 'some value'



def test_sqlalchemy_plugin():

    try:
        dbengine.register()
    except ImportError as e:
        # It's ok if sqlalchemy can't be found. Its not required
        assert('sqlalchemy' in str(e))


#
#   File handling
#


# def test_get_file_source():
#     fn = 'test/resources/dsh_example.yml'
#     s = flange.Flange.(fn, ns='testns', ns_from_dirname=True)
#     assert fn in s['src']
#     assert s['dict']
#     assert s['ns'] == 'testns'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

PATH_EXAMPLE = os.path.join(os.path.dirname(__file__), 'resources', 'dsh_example.yml')

#
def test_instantiate_from_explicit_file():
    f = flange.cfg.from_file(PATH_EXAMPLE, root_path='contexts__default')
    assert f.search('contexts/default/vars')


def test_delayed_merge():
    f = flange.cfg.Cfg(base_dir=os.path.dirname(__file__), file_search_depth=1, merge=False)
    assert not f.search('command_name2')
    f.refresh(False, True, True)
    assert f.search('command_name2')
