
import logging
from .context import src
import flange, url_scheme_python as pyurl

# import flange, logging



#
#  url scheme
#

# from context import url_scheme_python as pyurl


module_name = __name__.replace('.','/')
def test_url():
    module = pyurl.get('python://{}.test_url'.format(module_name))
    module = pyurl.get('python://{}.TestPlugin'.format(module_name))
    module = pyurl.get('python://{}.TestPlugin()'.format(module_name))
    module = pyurl.get('python://{}.TestPlugin().get_schema__instance'.format(module_name))
    module = pyurl.get('python://{}.TestPlugin.get_schema__static'.format(module_name))




data = {
    'a':{'a2':{'a3a':'a3aval', 'a3b':'a3aval'}},
    'testlog': {
        'name': 'testlog',
        'level': 'debug',
        'format': "%(asctime)s:%(levelname)s:%(name)s:%(message)s"}
}

f = flange.Flange(data=data)


def test_search_key_exact():

    assert f.search('a3b', exact=True)
    assert f.search('a3b', exact=False)

    assert f.search('3b', exact=False)
    assert not f.search('3b', exact=True)



def test_model_research():
    assert type(f.mget('testlog')) == logging.Logger




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
        return TestPlugin.get_schema__instance()


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
            'schema': 'python://{}.TestPlugin.get_schema__static'.format(module_name),
            'factory': 'python://{}.TestPlugin().get_instance'.format(module_name)
        }
    }

    f = flange.Flange(data=data, file_patterns=None)
    assert f.mget('test_instance_key').get_value() == 'some value'



#
#   File handling
#


def test_get_file_source():
    fn = 'test/resources/dsh_example.yml'
    s = flange.get_file_source(fn, ns='testns', ns_from_dirname=True)
    assert fn in s['src']
    assert s['dict']
    assert s['ns'] == 'testns'


def test_instantiate_from_explicit_file():
    f = flange.from_file('test/resources/dsh_example.yml', root_ns='contexts__default')
    assert f.search('vars')