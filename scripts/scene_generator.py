import argparse

import random
import json
from json import JSONEncoder


class CommonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Vector3):
            return [o.x, o.y, o.z]
        return o.__dict__


class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, v):
        return Vector3(self.x + v.x, self.y + v.y, self.z + v.z)

    def __sub__(self, v):
        return Vector3(self.x - v.x, self.y - v.y, self.z - v.z)

    def __mul__(self, n):
        return Vector3(self.x * n, self.y * n, self.z * n)

    def __truediv__(self, n):
        n = 1.0 if n == 0 else float(n)
        return Vector3(self.x / n, self.y / n, self.z / n)

    def cross(self, v):
        return Vector3(self.y * v.z - self.z * v.y,
                       self.z * v.x - self.x * v.z,
                       self.x * v.y - self.y * v.z)

    def normalize(self):
        self.x = self.x / self.length
        self.y = self.y / self.length
        self.z = self.z / self.length

    def dot(self, v):
        return (self.x * v.x + self.y * v.y + self.z * v.z)

    @property
    def length(self):
        return (self.x ** 2 + self.y ** 2 + self.z ** 2)**(1.0/2)

    def get_as_dict(self, keys=["x", "y", "z"]):
        return {keys[0]: self.x, keys[1]: self.y, keys[2]: self.z}

    @staticmethod
    def get_random(min_val=0, max_val=1):
        return Vector3(random.uniform(min_val, max_val),
                       random.uniform(min_val, max_val),
                       random.uniform(min_val, max_val))


class Scene(object):
    def __init__(self, background_color, global_ambient):
        self.backgroundColor = background_color
        self.globalAmbient = global_ambient


class Camera(object):
    def __init__(self, position, direction, z_near, z_far, povy):
        self.position = position
        self.direction = direction
        self.z_near = z_near
        self.z_far = z_far
        self.povy = povy


class Material(object):
    def __init__(self, ambient, specular, diffuse):
        self.ambient = ambient
        self.specular = specular
        self.diffuse = diffuse


class Sphere(object):
    def __init__(self, position, radius, material):
        self.center = position
        self.radius = radius
        self.material = material


class Light(object):
    def __init__(self, position, ambient, specular, diffuse):
        self.position = position
        self.material = Material(ambient, specular, diffuse)


class Triangle(object):
    def __init__(self, point_a, point_b, point_c):
        self.pointA = point_a
        self.pointB = point_b
        self.pointC = point_c

        vec_ab = point_b - point_a
        vec_ac = point_c - point_a
        normal = vec_ab.cross(vec_ac)
        normal.normalize()

        self.normalA = normal
        self.normalB = normal
        self.normalC = normal
        self.material = Material(Vector3.get_random(),
                                 Vector3.get_random(),
                                 Vector3.get_random())


class Pyramid(object):
    def __init__(self, base_a, base_b, base_c, top):
        self.base_a = base_a
        self.base_b = base_b
        self.base_c = base_c
        self.top = top

    def get_triangle_list(self):
        result = []
        result.append(Triangle(self.top, self.base_a, self.base_b))
        result.append(Triangle(self.top, self.base_b, self.base_c))
        result.append(Triangle(self.top, self.base_c, self.base_a))
        result.append(Triangle(self.base_a, self.base_b, self.base_c))

        return result

    def __copy__(self):
        return type(self)(self.base_a, self.base_b,
                          self.base_c, self.top)


def get_sierpinski_pyramid(level, pyramid):
    result = []
    if level == 0:
        result.append(pyramid)
        return result
    top_pyramid = Pyramid(pyramid.base_a + (pyramid.top - pyramid.base_a)/2,
                          pyramid.base_b + (pyramid.top - pyramid.base_b)/2,
                          pyramid.base_c + (pyramid.top - pyramid.base_c)/2,
                          pyramid.top)
    a_pyramid = Pyramid(pyramid.base_a,
                        pyramid.base_b + (pyramid.base_a - pyramid.base_b)/2,
                        pyramid.base_c + (pyramid.base_a - pyramid.base_c)/2,
                        pyramid.top + (pyramid.base_a - pyramid.top)/2)
    b_pyramid = Pyramid(pyramid.base_a + (pyramid.base_b - pyramid.base_a)/2,
                        pyramid.base_b,
                        pyramid.base_c + (pyramid.base_b - pyramid.base_c)/2,
                        pyramid.top + (pyramid.base_b - pyramid.top)/2)
    c_pyramid = Pyramid(pyramid.base_a + (pyramid.base_c - pyramid.base_a)/2,
                        pyramid.base_b + (pyramid.base_c - pyramid.base_b)/2,
                        pyramid.base_c,
                        pyramid.top + (pyramid.base_c - pyramid.top)/2)
    result += get_sierpinski_pyramid(level - 1, top_pyramid)
    result += get_sierpinski_pyramid(level - 1, a_pyramid)
    result += get_sierpinski_pyramid(level - 1, b_pyramid)
    result += get_sierpinski_pyramid(level - 1, c_pyramid)
    return result


def get_args():

    main_parser = argparse.ArgumentParser(description="Scene Generator")
    main_parser.add_argument("--lights", type=int, help="Number of lights "
                             "(default: %(default)s)", default=3)

    subparsers = main_parser.add_subparsers(dest="parser_name")
    subparsers.required = True

    parser_random = subparsers.add_parser("random",
                                          help="Generates random scene")
    parser_random.add_argument("--spheres", type=int,
                               help="Number of spheres (default: %(default)s)",
                               default=10)
    parser_random.add_argument("--triangles", type=int,
                               help="Number of triangles "
                               "(default: %(default)s)", default=5)

    parser_sierpinski = subparsers.add_parser("sierpinski", help="Generates "
                                              "Sierpinski's pyramid")
    parser_sierpinski.add_argument("--depth", type=int,
                                   help="Depth of recursion "
                                   "(default: %(default)s)", default=3)

    parser_cube_spheres = subparsers.add_parser("cube_of_spheres",
                                                help="Generates cube "
                                                "of random Spheres")
    parser_cube_spheres.add_argument("--side-length", type=int,
                                     help="Number of spheres per side "
                                     "(default: %(default)s)", default=5)

    return main_parser.parse_args()


def generate_sierpinski_pyramid(depth):
    output = {"Triangle": []}

    pyramid = Pyramid(Vector3(-4, 0, 0),
                      Vector3(4, 0, 0),
                      Vector3(0, 0, -2*1.71),
                      Vector3(0, 4, 1/3 * 2*1.71))
    pyramid = get_sierpinski_pyramid(depth, pyramid)
    for x in pyramid:
        output["Triangle"] += x.get_triangle_list()

    return output


def generate_random_scene(n_spheres, n_triangles):
    output = {"Triangle": [],
              "Sphere": []}

    for _ in range(n_triangles):
        tri = Triangle(Vector3.get_random(-5, 5),
                       Vector3.get_random(-5, 5),
                       Vector3.get_random(-5, 5))
        output["Triangle"].append(tri)

    for _ in range(n_spheres):
        sphere = Sphere(Vector3.get_random(-10, 10),
                        random.uniform(0, 5),
                        Material(Vector3.get_random(),
                                 Vector3.get_random(),
                                 Vector3.get_random()))
        output["Sphere"].append(sphere)

    return output


def get_camera():
    return Camera(Vector3(0, 0, 0),
                  Vector3(0, 0, -1),
                  1, 10, 90)


def get_lights(n_lights):
    lights = []
    for _ in range(n_lights):
        light = Light(Vector3.get_random(-10, 10),
                      Vector3.get_random(),
                      Vector3.get_random(),
                      Vector3.get_random())
        lights.append(light)

    return lights


def generate_cube_of_spheres(length):
    output = {"Sphere": []}
    radius = 1
    distance = 2.5

    start = -(length-1) * distance/2
    pos_x = pos_y = pos_z = start

    for x in range(length):
        for y in range(length):
            for z in range(length):
                sphere = Sphere(Vector3(pos_x, pos_y, pos_z),
                                radius,
                                Material(Vector3.get_random(),
                                         Vector3.get_random(),
                                         Vector3.get_random()))
                output["Sphere"].append(sphere)
                pos_z += distance
            pos_z = start
            pos_y += distance
        pos_y = start
        pos_x += distance

    return output


def get_scene_config():
    return Scene(Vector3.get_random(),
                 Vector3.get_random())


def main():

    output = dict()
    args = get_args()
    output["Camera"] = [get_camera()]
    # output["Scene"] = get_scene_config()
    output["Light"] = get_lights(args.lights)

    options = {"random":
               lambda: generate_random_scene(args.spheres, args.triangles),
               "sierpinski":
               lambda: generate_sierpinski_pyramid(args.depth),
               "cube_of_spheres":
               lambda: generate_cube_of_spheres(args.side_length)}

    output.update(options[args.parser_name]())

    with open('scene.json', 'w') as outfile:
        json.dump(output, outfile, cls=CommonEncoder)

if __name__ == "__main__":
    main()
