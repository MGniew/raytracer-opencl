import numpy as np
import pyopencl as cl
from PIL import Image


class Connector(object):

    def __init__(self, filename, scene, width, height, noise):
        self.scene = scene
        self.platform = cl.get_platforms()[0]
        self.device = self.platform.get_devices()
        self.context = cl.Context(self.device)
        self.queue = cl.CommandQueue(self.context)
        self.program = self.build_program(filename)
        self.tools = self.build_program("kernels/tools.cl")
        self.width = width
        self.height = height
        self.noise = np.int32(noise)
        self.setup()

    def load_image(self, filename):

        img = Image.open(filename)
        img.load()
        data = np.asarray(img, dtype=np.uint8)

        return data

    def send_textures(self):

        images = []
        max_width = 0
        max_height = 0
        if self.scene.textures:
            textures = {v: k for k, v in self.scene.textures.items()}

            for i in sorted(textures.keys()):
                print(i)
                v = textures[i]
                if v is None:
                    continue
                image = self.load_image(v)

                if image.shape[0] > max_height:
                    max_height = image.shape[0]

                if image.shape[1] > max_width:
                    max_width = image.shape[1]

                images.append(image)

        if len(images) == 0:
            images = [np.zeros((128, 128, 3))]
            max_width = 128
            max_height = 128

        images = [
            np.pad(
                image,
                ((0, max_height - image.shape[0]),
                 (0, max_width - image.shape[1]),
                 (0, 4 - image.shape[2])),
                "constant") for image in images]

        images = np.concatenate(images, 0)
        img_format = cl.ImageFormat(cl.channel_order.RGBA,
                                    cl.channel_type.UNORM_INT8)
        image = cl.Image(self.context,
                         cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                         img_format, hostbuf=images.flatten(), is_array=True,
                         shape=(max_width, max_height, 4),
                         pitches=(max_width * 4, max_width * max_height * 4))

        self.textures = image

    def setup(self):  # delete it later
        self.send_textures()
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

    def build_program(self, filename):

        with open(filename) as f:
            code = f.read()

        return cl.Program(self.context, code).build()

    def get_if_finished(self):

        if (self.event.get_info(cl.event_info.COMMAND_EXECUTION_STATUS) ==
                cl.command_execution_status.COMPLETE):
            self.queue.finish()
            cl.enqueue_copy(self.queue, self.result, self.result_buf)
            return self.result

        return None

    def run(self, callback=None):

        self.camera_d = cl.Buffer(
            self.context,
            cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=np.array(self.scene.get_objects("Camera")))

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
            self.textures,
            self.result_buf
            )

        if callback:
            self.event.set_callback(
                    cl.command_execution_status.COMPLETE,
                    callback)

        self.queue.flush()

    def run_denoise(self, image):

        input_buf = cl.Buffer(
            self.context,
            cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR,
            hostbuf=image)

        self.tools.get_means(
            self.queue,
            (np.int32(self.width/self.noise), np.int32(self.height)),
            None,
            input_buf)

        self.queue.flush()
        self.queue.finish()
        cl.enqueue_copy(self.queue, image, input_buf)
        return image
