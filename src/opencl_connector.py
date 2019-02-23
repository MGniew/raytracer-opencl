import numpy as np
import pyopencl as cl


class Connector(object):

    def __init__(self, filename, scene, width, height):

        self.scene = scene
        self.platform = cl.get_platforms()[0]
        self.device = self.platform.get_devices()
        self.context = cl.Context(self.device)
        self.queue = cl.CommandQueue(self.context)
        self.program = self.build_program(filename)
        self.width = width
        self.height = height
        self.setup()

    def setup(self):  # delete it later
        self.light_struct = np.dtype([("position", cl.cltypes.float3),
                                      ("ambience", cl.cltypes.float3),
                                      ("diffuse", cl.cltypes.float3),
                                      ("specular", cl.cltypes.float3)])

        self.result = np.zeros((3 * self.width * self.height), dtype=cl.cltypes.int)
        self.camera_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Camera")))
        self.lights_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
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
            self.n_triangles = np.int32(len(self.scene.get_objects("Triangle")))
        else:
            self.n_triangles = np.int32(0)

        self.result_buf = cl.Buffer(
            self.context,
            cl.mem_flags.WRITE_ONLY,
            self.result.nbytes)
        self.event = None

    def build_program(self, filename):

        with open(filename) as f:
            code = f.read()

        return cl.Program(self.context, code).build()

    def get_if_finished(self):

        if (self.event.get_info(cl.event_info.COMMAND_EXECUTION_STATUS) ==
                cl.command_execution_status.COMPLETE):
            self.queue.finish()
            cl.enqueue_copy(self.queue, self.result, self.result_buf)
            return bytes(self.result.tolist())

        return False

    def run(self, callback=None):

        self.camera_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Camera")))

        # self.event = self.program.get_image(
        #     self.queue,
        #     (300, 300),
        #     None,
        #     self.camera_d,
        #     self.lights_d,
        #     self.n_lights,
        #     np.int32(3), np.int32(0),
        #     self.result_buf
        #     )

        self.event = self.program.get_image(
            self.queue,
            (self.width, self.height),
            None,
            self.camera_d,
            self.lights_d,
            self.n_lights,
            self.spheres_d,
            self.n_spheres,
            self.triangles_d,
            self.n_triangles,
            self.result_buf
            )

        if callback:
            self.event.set_callback(
                    cl.command_execution_status.COMPLETE,
                    callback)

        self.queue.flush()
