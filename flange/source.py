import os
import anyconfig



PARSABLES = {
    'pickle':['p','pickle'],
    'toml':['toml'],
    'xml':['xml'],
    'yaml':['yml','yaml'],
    'json':['json'],
    'ini':['ini'],
    'properties':['props','properties'],
    'shellvars':['env']}



class Source(object):

    def __init__(self, uri, root_path=None, contents={}, parser=None, error=None):
        self.uri = uri
        self.root_path = root_path
        self.error = error
        self.parser = parser
        self.contents = contents


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Source uri={} root_path={} parser={} error={}>".format(self.uri, self.root_path, self.parser, self.error)


    def load(self):
        pass


    @staticmethod
    def from_file(full_file_path, root_path):
        s = SourceFile(full_file_path, root_path)
        s.load()
        return s



class SourceFile(Source):


    def _parse(self, parser=None):

        contents = anyconfig.load(self.uri, ac_parser=parser, ac_ordered=True)
        parser = parser if parser else os.path.splitext(self.uri)[1].strip('.')
        return (contents, parser)


    def load(self):

        try:
            self.contents, self.parser = self._parse()

        except Exception as e:
            # if the file had a known extension but didn't parse, raise an exception. The danger is that
            # it be parsed incorrectly as properties file which seems to match everything
            ext = os.path.splitext(self.uri)[1][1:]
            if [lext for lext in PARSABLES.values() if ext in lext]:
                self.error = e
                # print type(e) # 'exception parsing {}\t{}'.format(ext, e)

            for p in PARSABLES.keys():
                try:
                    self.contents, self.parser = self._parse(p)
                    break
                except Exception as e:
                    # print type(e) #'exception parsing as ', p, ' ', e
                    pass


