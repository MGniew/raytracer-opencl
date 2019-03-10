import numpy as np
import pyopencl as cl
from PIL import Image


class Connector(object):

    def __init__(self, filename, scene, width, height, frame_buffer):
        self.scene = scene
        self.platform = cl.get_platforms()[0]
        self.device = self.platform.get_devices()
        self.context = cl.Context(self.device)
        self.queue = cl.CommandQueue(self.context)
        self.program = self.build_program(filename)
        self.width = width
        self.height = height
        self.noise = np.int32(4)
        self.setup()
        # self.result = np.frombuffer(frame_buffer.get_obj())

    def load_image(self, filename):

        img = Image.open(filename)
        img.load()
        return np.asarray(img, dtype="int32")

    def send_textures(self):

        textures = {v: k for k, v in self.scene.textures.items()}
        images = []

        for k, v in textures:
            image = self.load_image(v)
            images.append(image)

    def setup(self):  # delete it later
        self.light_struct = np.dtype([("position", cl.cltypes.float3),
                                      ("ambience", cl.cltypes.float3),
                                      ("diffuse", cl.cltypes.float3),
                                      ("specular", cl.cltypes.float3)])

        self.result = np.zeros(
                (self.width * self.height * 3), dtype=cl.cltypes.char)
        self.camera_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Camera")))
        self.lights_d = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Light")))
        self.n_lights = np.int32(len(self.scene.get_objects("Light")))
        self.spheres_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Sphere")))
        if self.scene.get_objects("Sphere"):
            self.n_spheres = np.int32(len(self.scene.get_objects("Sphere")))
        else:
            self.n_spheres = np.int32(0)
        self.triangles_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Triangle")))
        if self.scene.get_objects("Triangle"):
            self.n_triangles = np.int32(
                    len(self.scene.get_objects("Triangle")))
        else:
            self.n_triangles = np.int32(0)

        self.result_buf = cl.Buffer(
            self.context,
            cl.mem_flags.WRITE_ONLY,
            self.result.nbytes)
        self.event = None

        # self.kernel = self.program.get_image
        # self.kernel.set_args(
        #     self.camera_d,
        #     self.lights_d,
        #     self.n_lights,
        #     self.spheres_d,
        #     self.n_spheres,
        #     self.triangles_d,
        #     self.n_triangles,
        #     self.noise,
        #     self.result_buf)

    def build_program(self, filename):

        with open(filename) as f:
            code = f.read()

        return cl.Program(self.context, code).build()

    def get_if_finished(self):

        if (self.event.get_info(cl.event_info.COMMAND_EXECUTION_STATUS) ==
                cl.command_execution_status.COMPLETE):
            self.queue.finish()
            cl.enqueue_copy(self.queue, self.result, self.result_buf)
            #  return bytes(self.result.tolist())
            return self.result

        return None

    def run(self, callback=None):

        self.camera_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Camera")))

        # self.event = cl.enqueue_nd_range_kernel(
        #         self.queue,
        #         self.kernel,
        #         (np.int32(self.width/self.noise), np.int32(self.height)),
        #         None)

        self.event = self.program.get_image(
            self.queue,
            (np.int32(self.width/self.noise), np.int32(self.height)),
            None,
            self.camera_d,
            self.lights_d,
            self.n_lights,
            self.spheres_d,
            self.n_spheres,
            self.triangles_d,
            self.n_triangles,
            self.noise,
            self.result_buf
            )

        if callback:
            self.event.set_callback(
                    cl.command_execution_status.COMPLETE,
                    callback)

        self.queue.flush()
