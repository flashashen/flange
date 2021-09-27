import anyconfig
import iterutils


class Data(object):

    def __init__(
            self,
            unflatten_separator="__",
            indexed_obj_factory=None):
        """

        :param unflatten_separator:
        :param indexed_obj_factory: func(p, k, v, existing_obj) - the factory function to
        create an object to be stored at the each path in the index. If there is an existing
        object it is passed to this function so that the caller/func can decide how to
        hanlde multiple values at a given path
        """

        self.data = {}
        self.path_index = {}
        self.unflatten_separator = unflatten_separator
        self.indexed_obj_factory = indexed_obj_factory


    def add(self, d, root_path):

        # try:
        d = {root_path: d} if root_path else d
        e = iterutils.unflatten(d, self.unflatten_separator)
        anyconfig.merge(self.data, iterutils.remap(e, lambda p, k, v: self.__filter_and_index(p, k, v)))
        # except:
        #     self.failed.append(d)



    def search(self, path_expression, mode=UXP, values=None, ifunc=lambda x: x):
        """
        find matches for the given path expression in the data

        :param path_expression: path tuple or string
        :return:
        """
        # keys = path_expression if isinstance(path_expression, str) else path_expression[-1]

        path_and_value_list = iterutils.search(
            self.data,
            path_expression=path_expression,
            required_values=values,
            exact=(mode[1] == "x"))

        return self.__return_value(path_and_value_list, mode, ifunc)



    def __return_value(self, l, mode, ifunc=lambda x: x):

        if l:
            if len(l) > 1 and mode[0] == 'u':
                raise ValueError('multiple matches found')

        elif mode[2] == 'r':
            raise ValueError('no match found')


        if mode[0] == 'u':
            return ifunc(l[0]) if l else None
        else:
            return l if not ifunc else [ifunc(x) for x in l]


    def __visit_index_path(self, src, p, k, v):
        """
            Called during processing of source data
        """
        cp = p + (k,)
        self.path_index[cp] = self.indexed_obj_factory(p, k, v, self.path_index.get(cp))
        if cp in self.path_index:
            # if self.path_index[cp].assert_val_equals(v):
            #     raise ValueError('unexpected value change at path_index[{}]'.format(cp))
            self.path_index[cp].add_src(src)
        else:
            self.path_index[cp] = Flobject(val=v, path=cp, srcs=set([src]))


    def __filter_and_index(self, p, k, v):

        # now the root_path/ns has already been accounted for in the data.
        # no prefixing loginc
        # np = (src.ns,) + p if src.ns else p
        np = p

        # filter. func may be provided or be class default
        if self.key_filter and not self.key_filter(np, k, v):
            return False

        # index. internal to Cfg class
        full_path = np + (k,)
        if full_path in self.path_index:
            if not self.path_index[full_path].val_equals(v):
                # print 'updating index at ', full_path
                # raise ValueError('unexpected value change at path_index[{}]'.format(full_path))
                self.path_index[full_path].add_src(src)
        else:
            # print 'adding index at ', full_path
            self.path_index[full_path] = indexed_obj_factory(p, k, v)

        return k, v
