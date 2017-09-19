import flange


def test_model_research():

    d = {'testlog': {
            'name': 'testlog',
            'level': 'debug',
            'format': "%(asctime)s:%(levelname)s:%(name)s:%(message)s"}}
    f = flange.Flange()
    assert f.mget('testlog')