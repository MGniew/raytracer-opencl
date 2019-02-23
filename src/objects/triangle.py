import numpy as np
import pyopencl as cl
from src.objects.base import BaseObject
from src.objects.visible_object import VisibleObject


@BaseObject.register_object()
class Triangle(VisibleObject):

    triangle_struct = np.dtype(
        [("vertices", cl.cltypes.float3),
         ("normals", cl.cltypes.float3)])

    def __init__(self, material, vertices, normals=None):
        self.vertices = vertices
        if not normals:
            ab = self.vertices[0] - self.vertices[1]
            ac = self.vertices[0] - self.vertices[2]
            self.vertices = [np.cross(ab, ac)] * 3
        else:
            self.normals = normals

    def _get_cl_repr(self):  # TODO: make it work

        return np.array(
            ([cl.array.vec.make_float3(*el) for el in self.vertices],
             [cl.array.vec.make_float3(*el) for el in self.normals]),
            dtype=self.light_struct)
