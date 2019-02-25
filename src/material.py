import numpy as np
import pyopencl.cltypes
import pyopencl as cl


class Material(object):

    material_struct = np.dtype(
        [("ambience", cl.cltypes.float3),
         ("diffuse", cl.cltypes.float3),
         ("specular", cl.cltypes.float3)])

    def __init__(
            self,
            ambient=[0.7, 0.2, 0.3],
            diffuse=[0.7, 0.2, 0.3],
            specular=[0.7, 0.2, 0.3]):
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular

    def _get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.ambient),
                        cl.array.vec.make_float3(*self.diffuse),
                        cl.array.vec.make_float3(*self.specular)),
                        dtype=self.material_struct)
