
import logging
from .context import *
from nose.tools import *

from flange import dbengine, url_scheme_python as pyurl
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
    attr = pyurl.get('python://{}.TestPlugin'.format(module_name))
    assert attr().get_schema__instance()

    attr = pyurl.get('python://{}.TestPlugin()'.format(module_name))
    assert attr.get_schema__instance()


def test_url_class_functions():
    attr = pyurl.get('python://{}.TestPlugin().get_schema__instance'.format(module_name))
    assert attr()['type'] == 'object'
    attr = pyurl.get('python://{}.TestPlugin().get_schema__instance()'.format(module_name))
    assert attr['type'] == 'object'

    attr = pyurl.get('python://{}.TestPlugin.get_schema__static'.format(module_name))
    assert attr()['type'] == 'object'
    attr = pyurl.get('python://{}.TestPlugin.get_schema__static()'.format(module_name))
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

    assert f.search('a3b', exact=True)
    assert f.search('a3b', exact=False)

    assert f.search('3b', exact=False)
    assert not f.search('3b', exact=True)



def test_model_research():
    assert type(f.mget('testlog')) == logging.Logger


def test_mget_by_name():
    assert(f.mget('testlog'))
    assert(f.mget('testlog2'))
    assert(f.mget('testlog') != f.mget('testlog2'))


def test_mget_by_model():
    # An instance can be fetched by model name. If there are multiple instances a vfilter can be used
    with assert_raises(ValueError):
        f.mget(model='logger', raise_absent=True)
    assert(f.mget(model='logger', vfilter='DEBUG'))


def test_mget_vfilter():
    # vfilter can be used with or without the config key to retrieve an instance
    assert(f.mget('testlog', vfilter='DEBUG'))
    assert(f.mget('testlog', vfilter='WARNING') == None)

    assert(f.mget('testlog2', vfilter='WARNING'))
    assert(f.mget('testlog2', vfilter='DEBUG') == None)



class TestPlugin:

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
                'only_TestPlugin_would_match_this': {'type': 'string'}
            },
            'required': ['only_TestPlugin_would_match_this']
        }

    def get_schema__instance(self):
        return TestPlugin.get_schema__static()


    def get_instance(self, params):
        # return an instance of this object with the value given in params
        return TestPlugin(params['only_TestPlugin_would_match_this'])



def test_plugin_model():


    data = {

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
            'factory': 'python://{}.TestPlugin().get_instance'.format(module_name)
        }
    }

    f = flange.cfg.Cfg(data=data, file_patterns=None)
    assert f.mget('test_instance_key').get_value() == 'some value'



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
    f = flange.cfg.from_file(PATH_EXAMPLE, root_ns='contexts__default')
    assert f.search('vars')

