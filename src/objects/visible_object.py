import numpy as np

from src.objects.base import BaseObject
from src.material import Material


class VisibleObject(BaseObject):

    def __init__(self, material):

        if isinstance(material, dict):
            self.material = Material(**material)
        else:
            self.material = material

    def get_cl_repr(self):
        child_repr = self._get_cl_repr()
        child_mat_repr = self.material._get_cl_repr()
        new_type = np.dtype(
                child_repr.dtype.descr + child_mat_repr.dtype.descr)
        result = np.array(
                child_repr.tolist() + child_mat_repr.tolist(), dtype=new_type)

        return result
