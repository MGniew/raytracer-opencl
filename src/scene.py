import json
import pywavefront
from src.objects.base import BaseObject

from src.material import Material
from src.objects.camera import Camera
from src.objects.sphere import Sphere
from src.objects.light import Light
from src.objects.triangle import Triangle

import numpy as np


class Scene(object):

    def __init__(self, background_color, global_ambient):
        self.background_color = background_color
        self.global_ambient = global_ambient
        self.objects = dict()
        self.textures = None

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

    def triangle_gen(self, vertices, vertices_format, material):
        formats = vertices_format.split("_")

        normals = []
        tri_vertices = []
        texture_coord = []

        i = 0
        for el in formats:
            i += int(el[1])

        for x in zip(*[iter(vertices)] * i * 3):
            x = list(x)
            while x:
                for el in formats:
                    if el == "T2F":
                        texture_coord.append(np.array(x[:2]))
                        x = x[2:]
                    elif el == "C3F":
                        x = x[3:]
                    elif el == "N3F":
                        normals.append(np.array(x[:3]))
                        x = x[3:]
                    else:
                        tri_vertices.append(np.array(x[:3]))
                        x = x[3:]

            yield Triangle(
                    material,
                    tri_vertices,
                    normals,
                    texture_coord)

            normals = []
            tri_vertices = []
            texture_coord = []

    def load_from_mesh(self, filename):

        scene = pywavefront.Wavefront(filename, collect_faces=True,
                                      create_materials=True)

        textures = {None: -1}
        texture_num = 0

        for name, material in scene.materials.items():
            if material.texture.path and material.texture.path not in textures:
                textures[material.texture.path] = texture_num
                texture_num += 1
            mat = Material(
                    material.ambient,
                    material.diffuse,
                    material.specular,
                    textures[material.texture.path])

            for triangle in self.triangle_gen(
                    material.vertices, material.vertex_format, mat):
                self.add_object(triangle)

        print("Scene loaded!")

        # shininess...
        # emissive...
        # transparency...
        # texture?
