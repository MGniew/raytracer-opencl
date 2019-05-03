import json
import pywavefront
from src.objects.base import BaseObject

from src.material import Material
from src.objects.camera import Camera
from src.objects.sphere import Sphere
from src.objects.light import Light
from src.objects.triangle import Triangle
from PIL import Image

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

    def triangle_gen(
            self, vertices, vertices_format, material, width=0, height=0):
        formats = vertices_format.split("_")

        print(width, height)
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
                        texture_coord.append(
                                np.array([x[0], 1 - x[1], width, height]))
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

    def load_image(self, filename):

        img = Image.open(filename)
        img.load()
        data = np.asarray(img, dtype=np.uint8)

        return data

    def load_from_mesh(self, filename):

        textures = {None: (-1, 0, 0)}
        texture_num = 0
        num_triangles = 0

        def load_texture(texture):
            nonlocal texture_num
            if texture:
                if texture.path not in textures:
                    height, width, _ = self.load_image(texture.path).shape
                    textures[texture.path] = (texture_num, width, height)
                    texture_num += 1
                return textures[texture.path]
            return (-1, 0, 0)

        scene = pywavefront.Wavefront(filename, collect_faces=True,
                                      create_materials=True)
        for name, material in scene.materials.items():
            print(material.__dict__)

            diff_texture = load_texture(material.texture)
            ambi_texture = load_texture(material.texture_ambient)
            spec_texture = load_texture(material.texture_specular_color)
            bump_texture = load_texture(material.texture_bump)
            reflectiveness = 0

            mat = Material(
                    material.ambient,
                    material.diffuse,
                    material.specular,
                    material.emissive,
                    material.transparency,
                    material.optical_density,
                    material.shininess,
                    reflectiveness,
                    texture_diffuse=diff_texture,
                    texture_ambient=ambi_texture,
                    texture_specular_color=spec_texture,
                    texture_bump=bump_texture)

            for triangle in self.triangle_gen(
                    material.vertices,
                    material.vertex_format,
                    mat, diff_texture[1], diff_texture[2]):
                self.add_object(triangle)
                num_triangles += 1

        self.textures = textures
        print("Triangles:", num_triangles)
        print("Scene loaded!")
