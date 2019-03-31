from src.opencl_connector import Connector
from src.gui.main_window import MainWindow
from src.denoiser.base import Denoiser
from src.scene import Scene
import gi
gi.require_version('Gtk', '3.0')  # noqa: E402
from gi.repository import Gtk

from src.objects.camera import Camera
from multiprocessing import Pipe, Process
import datetime

# move to __init__.py
from src.denoiser.mean_pixel import MeanPixel

MS_PER_UPDATE = 0.02


def gui_worker(child_conn, w=300, h=300):
    win = MainWindow(w, h, child_conn)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    child_conn.close()


class Engine(object):

    def __init__(
            self, kernel_filename, scene_filename, width, height, noise, obj):

        scene = Scene(None, None)
        scene.load_from_json(scene_filename)
        if obj:
            scene.load_from_mesh(obj)
        self.camera = Camera(width, height)
        scene.add_object(self.camera)
        self.connector = Connector(
                kernel_filename, scene, width, height, noise)

        self.parent_conn, child_conn = Pipe()
        self.gui_process = Process(
                target=gui_worker, args=(child_conn, width, height))
        self.gui_process.start()
        self.running = True
        self.denoiser = Denoiser.create("MeanPixel", width, height)

        self.actions = {
                a: False for a in [
                    "w", "a", "s", "d",
                    "Up", "Left", "Down", "Right",
                    "q", "e", "plus", "minus"]}

    def collect_action(self, action):

        value = True
        if action[0] == "~":
            action = action[1:]
            value = False

        if action in self.actions:
            self.actions[action] = value

    def update(self):

        if self.actions["plus"]:
            self.camera.speed += 0.001
        if self.actions["minus"]:
            self.camera.speed -= 0.001

        if self.camera.speed < 0:
            self.camera.speed = 0

        self.camera.move(
                self.actions["w"],
                self.actions["s"],
                self.actions["a"],
                self.actions["d"])
        self.camera.rotate(
                self.actions["Up"],
                self.actions["Left"],
                self.actions["Down"],
                self.actions["Right"])
        self.camera.rotate_off_its_axis(
                self.actions["q"],
                self.actions["e"])

    def run(self):

        self.connector.run()

        previous = datetime.datetime.now()
        lag = 0
        while self.running:
            current = datetime.datetime.now()
            elapsed = (current - previous).total_seconds()
            previous = current
            lag += elapsed

            if self.parent_conn.poll():
                try:
                    msg = self.parent_conn.recv()
                except EOFError:
                    self.running = False
                    break
                self.collect_action(msg)

            while lag >= MS_PER_UPDATE:
                self.update()
                lag -= MS_PER_UPDATE

            image = self.connector.get_if_finished()
            if image is not None:
                try:
                    image = self.denoiser.denoise(image, self.connector)
                    self.parent_conn.send(image.tobytes())
                except BrokenPipeError:
                    self.running = False
                    break
                self.connector.run()

        self.gui_process.join()

    def send_and_query(self, status):
        image = self.connector.get_if_finished()
        try:
            self.parent_conn.send(image)
        except BrokenPipeError:
            self.running = False
        else:
            self.connector.run(self.send_and_query)
