import numpy as np
import pyopencl as cl

from src.objects.base import BaseObject
from src.objects.visible_object import VisibleObject


@BaseObject.register_object()
class Light(VisibleObject):

    light_struct = np.dtype(
        [("position", cl.cltypes.float3)])

    def __init__(self, material, position):
        super(Light, self).__init__(material)
        self.position = position

    def _get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.position),),
                        dtype=self.light_struct)
