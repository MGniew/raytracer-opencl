import numpy as np
import pyopencl as cl
import pyopencl.cltypes
import pyopencl.array
import math

from src.objects.base import BaseObject


@BaseObject.register_object()
class Camera(BaseObject):

    camera_struct = np.dtype(
        [("position", cl.cltypes.float3),
         ("topLeftCorner", cl.cltypes.float3),
         ("rightVector", cl.cltypes.float3),
         ("upVector", cl.cltypes.float3),
         ("worldWidth", cl.cltypes.float),
         ("worldHeight", cl.cltypes.float),
         ("zFar", cl.cltypes.float)])

    def __init__(
            self,
            width=300,
            height=300,
            position=[0, 0, -2],
            direction=[0, 0, 1],
            z_near=0.1,
            z_far=30,
            povy=90):

        self.position = np.array(position)
        self.z_far = z_far
        self.direction = np.array(direction)
        self.direction = self.direction / np.linalg.norm(self.direction)
        aspect = width/height
        self.z_near = z_near
        self.world_height = 2 * math.tan((povy * math.pi/180)/2) * z_near
        self.world_width = aspect * self.world_height
        self.up = np.array([0, 1, 0])
        self.up = np.cross(
                    np.cross(self.direction, self.up),
                    direction)
        self.up = self.up / np.linalg.norm(self.up)
        self.right = np.cross(self.direction, self.up)

        self.update()

    def get_light_at_camera_position(self):
        return np.array((cl.array.vec.make_float3(*self.position.tolist()),
                         cl.array.vec.make_float3(0.5, 0.4, 0.5),
                         cl.array.vec.make_float3(0.5, 0.5, 0.5),
                         cl.array.vec.make_float3(0.2, 0.4, 0.5)),
                        dtype=Camera.light_struct)

    def move(self, forward, backward, left, right):

        if forward:
            self.position = self.position + self.direction * 0.01
        elif backward:
            self.position = self.position - self.direction * 0.01

        if left:
            self.position = self.position - self.right * 0.01
        elif right:
            self.position = self.position + self.right * 0.01

        self.update()

    def rotate(self, up, left, down, right):

        angle_lr = math.pi/100
        angle_ud = math.pi/100

        if right == left:
            angle_lr = 0
        elif left:
            angle_lr *= -1
        if down == up:
            angle_ud = 0
        elif up:
            angle_ud *= -1

        if angle_ud != 0:
            axis = self.right
            self.up = rotate_vec(self.up, axis, angle_ud)
            self.up = self.up / np.linalg.norm(self.up)
            self.direction = rotate_vec(self.direction, axis, angle_ud)
            self.direction = self.direction / np.linalg.norm(self.direction)

        if angle_lr != 0:
            axis = self.direction
            self.up = rotate_vec(self.up, axis, angle_lr)
            self.up = self.up / np.linalg.norm(self.up)
            self.right = rotate_vec(self.right, axis, angle_lr)
            self.right = self.right / np.linalg.norm(self.right)

        self.update()

    def set_options(self, position, direction):
        self.position = position
        self.direction = direction / np.linalg.norm(direction)
        self.update()

    def update(self):

        self.top_left = self.position + self.z_near * self.direction
        self.top_left = self.top_left + self.world_height/2 * self.up
        self.top_left = self.top_left - self.world_width/2 * self.right

    def get_cl_repr(self):

        return np.array((cl.array.vec.make_float3(*self.position.tolist()),
                         cl.array.vec.make_float3(*self.top_left.tolist()),
                         cl.array.vec.make_float3(*self.right.tolist()),
                         cl.array.vec.make_float3(*self.up.tolist()),
                         np.float(self.world_width),
                         np.float(self.world_height),
                         np.float(self.z_far)),
                        dtype=Camera.camera_struct)

    def rotate_aroud_center(self):

        self.move(False, False, False, True)
        self.direction = np.array([0, 0, 0]) - self.position
        self.direction = self.direction / np.linalg.norm(self.direction)

        self.up = np.cross(self.right, self.direction)
        self.up = self.up / np.linalg.norm(self.up)

        self.right = np.cross(self.direction, self.up)
        self.right = self.right / np.linalg.norm(self.right)
        self.update()

    def rotate_off_its_axis(self):

        angle = math.pi / 400
        self.direction = rotate_vec(self.direction, self.up, angle)
        self.right = rotate_vec(self.right, self.up, angle)
        self.update()


def rotate_vec(vec, axis, angle):

    a = math.sin(angle)
    b = math.cos(angle)

    x = (b + axis[0]**2 * (1 - b)) * vec[0]
    x += (axis[0] * axis[1] * (1 - b) - (axis[2] * a)) * vec[1]
    x += (axis[1] * a + axis[0] * axis[2] * (1 - b)) * vec[2]

    y = (axis[2] * a + axis[0] * axis[1] * (1 - b)) * vec[0]
    y += (b + axis[1]**2 * (1 - b)) * vec[1]
    y += (axis[1] * axis[2] * (1 - b) - axis[0] * a) * vec[2]

    z = (axis[0]*axis[2] * (1 - b) - axis[1] * a) * vec[0]
    z += (axis[0] * a + axis[1] * axis[2] * (1 - b)) * vec[1]
    z += (b + axis[2]**2 * (1-b)) * vec[2]

    return np.array([x, y, z])
