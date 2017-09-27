import re


URL_PATTERN_STRING = "^(?P<scheme>[^:\/?#]+):\/{2,}(?P<path>[^?#]*)(\?([^#]*))?(#(.*))?$"
URL_PATTERN = re.compile(URL_PATTERN_STRING)
# PATTERN_METHOD_EXTRACTOR = re.compile(r"^(?P<module>(?:\w+\/)*\w+)(?:\.(?P<pattr>\w+)|(?::(?P<class>\w+)(?:\.(?P<iattr>\w+)|:(?P<cattr>\w+))?)?)?$")

PATTERN_METHOD_EXTRACTOR = re.compile(r"^(?P<module>(?:\w+\/)*\w+)(?P<attr>(?:\.\w+(?:\(\))?)*)?$")


def get_from_attr_segment(attr, seg):
    params_idx = seg.find('(')
    if params_idx > 0:
        # there is a () to indicate this attr should be called/instantiated
        attr = getattr(attr, seg[0:params_idx])()
    else:
        attr = getattr(attr, seg)
    return attr


import importlib
def get_from_attr_chain(module, attr_chain):

    attr = module
    for seg in attr_chain.strip('.').split('.'):
        attr = get_from_attr_segment(attr, seg)

    return attr


def get(url):
    '''

    urls like the following are understood.

    :param url:
    :return: The type of returned object depends on the url. here are the possibilities

        python://module                             # module
        python://pkg/module.attr                    # module attribute
        python://pkg/module:class                   # class
        python://pkg/module:class?arg1=x,argn=y     # class instance
        python://pkg/module:class.iattr             # class instance attribute
        python://pkg/module:class:cattr             # class static attribute


        someday support python versions and install package w version: 'python.2.7://requests[1.2,]|requests.get'
    '''
    m = URL_PATTERN.match(url)
    if not m:
        raise ValueError('url {} did not match pattern {}'.format(url,URL_PATTERN_STRING))

    d = m.groupdict()
    if not d['path']:
        raise ValueError('path in {} could not be extracted from {}'.format(URL_PATTERN_STRING, url))

    # The basic url has been parsed. now try to parse the path and args sections
    # to create a python thing
    m = PATTERN_METHOD_EXTRACTOR.match(d['path'])
    if not m:
        raise ValueError("path part of url ('{}') could not be parsed as python attribute chain".format(d['path']))

    # there must at least be a module
    d = m.groupdict()
    import importlib
    module = importlib.import_module(d['module'].replace('/','.'))

    if 'attr' in d and d['attr']:
        return get_from_attr_chain(module, d['attr'])

    #     # package attribute
    #     return getattr(module, d['pattr'])
    # if 'pattr' in d and d['pattr']:
    #     # package attribute
    #     return getattr(module, d['pattr'])
    #
    # elif 'class' in d and d['class']:
    #
    #     cls = getattr(module, d['class'])
    #     if 'iattr' in d and d['iattr']:
    #         # class instance method
    #         return getattr(cls(), d['iattr'])
    #
    #     if 'cattr' in d and d['cattr']:
    #         # class static method
    #         return cls.__getattribute__(d['cattr'])

    # the only remaining alternative is the module itself.
    else:
        return module