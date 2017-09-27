import re


URL_PATTERN_STRING = "^(?P<scheme>[^:\/?#]+):\/{2,}(?P<path>[^?#]*)(\?([^#]*))?(#(.*))?$"
URL_PATTERN = re.compile(URL_PATTERN_STRING)
PATTERN_METHOD_EXTRACTOR = re.compile(r"^(?P<module>(?:\w+\/)*\w+)(?:\.(?P<pattr>\w+)|(?::(?P<class>\w+)(?:\.(?P<iattr>\w+)|:(?P<cattr>\w+))?)?)?$")


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
        raise ValueError("path part of url ('{}') could not be parsed as pkg1.pkgN.pmethod, pkg1.pkgN:class:cmethod or pkg1.pkgN:class.imethod".format(d['path']))

    # there must at least be a module
    d = m.groupdict()
    import importlib
    module = importlib.import_module(d['module'])

    if 'pattr' in d and d['pattr']:
        # package attribute
        return getattr(module, d['pattr'])

    elif 'class' in d and d['class']:

        cls = getattr(module, d['class'])
        if 'iattr' in d and d['iattr']:
            # class instance method
            return getattr(cls(), d['iattr'])

        if 'cattr' in d and d['cattr']:
            # class static method
            return cls.__getattribute__(d['cattr'])

    # the only remaining alternative is the module itself.
    else:
        return module