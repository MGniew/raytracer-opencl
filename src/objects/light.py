import numpy as np
import pyopencl as cl

from src.objects.base import BaseObject

@BaseObject.register_object()
class Light(BaseObject):

    light_struct = np.dtype(
        [("position", cl.cltypes.float3),
         ("ambience", cl.cltypes.float3),
         ("diffuse", cl.cltypes.float3),
         ("specular", cl.cltypes.float3)])

    def __init__(self, position, ambient, diffuse, specular):
        self.position = position
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular

    def get_cl_repr(self):

        return np.array((
                cl.array.vec.make_float3(*self.position),
                cl.array.vec.make_float3(*self.ambient),
                cl.array.vec.make_float3(*self.diffuse),
                cl.array.vec.make_float3(*self.specular)
                ), dtype=self.light_struct)
