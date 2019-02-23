import json

from src.objects.base import BaseObject
from src.objects.camera import Camera
from src.objects.sphere import Sphere
from src.objects.light import Light


class Scene(object):

    def __init__(self, background_color, global_ambient):
        self.background_color = background_color
        self.global_ambient = global_ambient
        self.objects = dict()

    def add_object(self, obj):

        obj_type = obj.__class__.__name__
        if obj_type not in self.objects:
            self.objects[obj_type] = [obj]
        else:
            self.objects[obj_type].append(obj)

    def get_objects(self, obj_type, cl_repr=True):

        if obj_type not in self.objects:
            return None

        if cl_repr:
            return [obj.get_cl_repr() for obj in self.objects[obj_type]]

        return self.objects[obj_type]

    def load_from_json(self, filename):

        with open(filename) as f:
            data = json.load(f)

        for k, v in data.items():
            for obj in v:
                obj = BaseObject.create(k, obj)
                self.add_object(obj)
