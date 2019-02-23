import numpy as np
import pyopencl as cl

from src.objects.base import BaseObject
from src.objects.visible_object import VisibleObject


@BaseObject.register_object()
class Sphere(VisibleObject):

    sphere_struct = np.dtype(
        [("center", cl.cltypes.float3),
         ("radius", np.float32)])

    def __init__(self, material, center, radius):
        super(Sphere, self).__init__(material)
        self.radius = radius
        self.center = center

    def _get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.center),
                        self.radius), dtype=self.sphere_struct)
