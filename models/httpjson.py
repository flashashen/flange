import requests
# import jmespath



def get_model_instance(data):
    auth = (data['user'], data['password']) if 'user' in data else None
    r = requests.get(data['url'], verify=False, auth=auth).json()
    # if 'jmespath' in config:
    #     r = jmespath.search(config['jmespath'], r)
    return r


FACTORY = get_model_instance

SCHEMA = {
    "type" : "object",
    "properties" : {
        'url':{'type':'string'},
        'user':{'type':'string'},
        'password':{'type':'string'},
        'extract':{'type':'string'},
    },
    "required": ["url"]
}

