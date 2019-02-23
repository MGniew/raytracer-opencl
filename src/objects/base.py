class BaseObject(object):

    subclasses = {}

    @classmethod
    def register_object(cls):

        def decorator(subclass):
            cls.subclasses[subclass.__name__] = subclass
            return subclass

        return decorator

    @classmethod
    def create(cls, name, args):

        if name not in cls.subclasses:
            raise ValueError("Bad object name: {}".format(name))
        return cls.subclasses[name](**args)

    def get_cl_repr(self):
        return self._get_cl_repr()
