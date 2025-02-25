import numpy as np
import pyopencl.cltypes  # noqa: F401
import pyopencl as cl


class Material(object):

    material_struct = np.dtype(
        [("ambience", cl.cltypes.float3),
         ("diffuse", cl.cltypes.float3),
         ("specular", cl.cltypes.float3),
         ("emissive", cl.cltypes.float3),
         ("texture_ambient", cl.cltypes.float3),
         ("texture_diffuse", cl.cltypes.float3),
         ("texture_specular", cl.cltypes.float3),
         ("texture_bump", cl.cltypes.float3),
         ("transparency", np.float32),
         ("optical_density", np.float32),
         ("shininess", np.float32),
         ("reflectiveness", np.float32)  # ugly sollution
         ])

    def __init__(
            self,
            ambient=[0.7, 0.2, 0.3],
            diffuse=[0.7, 0.2, 0.3],
            specular=[0.7, 0.2, 0.3],
            emissive=[0, 0, 0],
            transparency=1,
            optical_density=1,
            shininess=0.1,
            reflectiveness=0,
            texture_diffuse=(-1, 0, 0),
            texture_ambient=(-1, 0, 0),
            texture_specular_color=(-1, 0, 0),
            texture_bump=(-1, 0, 0)  # normals
            ):

        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.emissive = emissive
        self.transparency = transparency
        self.optical_density = optical_density
        self.shininess = shininess
        self.reflectiveness = reflectiveness
        self.texture_diffuse = texture_diffuse
        self.texture_ambient = texture_ambient
        self.texture_specular = texture_specular_color
        self.texture_bump = texture_bump


        if self.texture_diffuse[0] >= 0 and all(e == 0 for e in self.diffuse):
            self.diffuse = [1, 1, 1]
        if self.texture_ambient[0] >= 0 and all(e == 0 for e in self.ambient):
            self.ambient = [1, 1, 1]

        if self.transparency > 0:
            self.reflectiveness = 1 - self.transparency

    def _get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.ambient),
                        cl.array.vec.make_float3(*self.diffuse),
                        cl.array.vec.make_float3(*self.specular),
                        cl.array.vec.make_float3(*self.emissive),
                        cl.array.vec.make_float3(*self.texture_ambient),
                        cl.array.vec.make_float3(*self.texture_diffuse),
                        cl.array.vec.make_float3(*self.texture_specular),
                        cl.array.vec.make_float3(*self.texture_bump),
                        self.transparency,
                        self.optical_density,
                        self.shininess,
                        self.reflectiveness),
                        dtype=self.material_struct)
