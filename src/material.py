import numpy as np
import pyopencl.cltypes  # noqa: F401
import pyopencl as cl


class Material(object):

    material_struct = np.dtype(
        [("ambience", cl.cltypes.float3),
         ("diffuse", cl.cltypes.float3),
         ("specular", cl.cltypes.float3),
         ("texture_num", np.float32),
         ("padding", np.float32, 3)  # ugly sollution
         ])

    def __init__(
            self,
            ambient=[0.7, 0.2, 0.3],
            diffuse=[0.7, 0.2, 0.3],
            specular=[0.7, 0.2, 0.3],
            texture_num=-1):
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.texture_num = texture_num

    def _get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.ambient),
                        cl.array.vec.make_float3(*self.diffuse),
                        cl.array.vec.make_float3(*self.specular),
                        self.texture_num,
                        [np.float32(1)] * 3,
                        ),
                        dtype=self.material_struct)
