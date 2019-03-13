import numpy as np
import pyopencl as cl
from src.objects.base import BaseObject
from src.objects.visible_object import VisibleObject


@BaseObject.register_object()
class Triangle(VisibleObject):

    triangle_struct = np.dtype(
        [("vertices", cl.cltypes.float3, 3),
         ("normals", cl.cltypes.float3, 3),
         ("triangles", cl.cltypes.float3, 3)])

    def __init__(self, material, vertices, normals=None, texture_coord=None):
        super(Triangle, self).__init__(material)
        self.vertices = vertices
        if not normals:
            ab = self.vertices[0] - self.vertices[1]
            ac = self.vertices[0] - self.vertices[2]
            self.normals = [np.cross(ab, ac)] * 3
            self.normals = [a / np.linalg.norm(a) for a in self.normals]
        else:
            self.normals = normals

        self.texture_coord = texture_coord
        if not texture_coord:
            self.texture_coord = self.normals
        self.texture_coord = [a.tolist() for a in self.texture_coord]
        self.vertices = [a.tolist() for a in self.vertices]
        self.normals = [a.tolist() for a in self.normals]

    def _get_cl_repr(self):

        a = np.array(
            ([cl.array.vec.make_float3(*el) for el in self.vertices],
             [cl.array.vec.make_float3(*el) for el in self.normals],
             [cl.array.vec.make_float3(*el) for el in self.texture_coord]),
            dtype=self.triangle_struct)

        return a
