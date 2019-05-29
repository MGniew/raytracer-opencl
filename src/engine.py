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
import png
import numpy as np
import os

# move to __init__.py
from src.denoiser.mean_pixel import MeanPixel  # noqa: F401

MS_PER_UPDATE = 0.02


def gui_worker(child_conn, w=300, h=300):
    win = MainWindow(w, h, child_conn)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    child_conn.close()


class Engine(object):

    def __init__(
            self, kernel_filename, scene_filename,
            width, height, noise, obj, animation, record, no_gui):

        self._run = self.animation_run if animation else self.normal_run
        self.record = record
        self.no_gui = no_gui
        if self.record:
            os.makedirs("animation")
        self.frame = 0
        self.wait = animation
        self.width, self.height = width, height
        self.actions_list = self.get_action_list()
        scene = Scene(None, None)
        scene.load_from_json(scene_filename)
        if obj:
            scene.load_from_mesh(obj)
        self.camera = Camera(width, height)
        scene.add_object(self.camera)
        self.connector = Connector(
                kernel_filename, scene, width, height, noise)

        if not self.no_gui:
            self.parent_conn, child_conn = Pipe()
            self.gui_process = Process(
                    target=gui_worker, args=(child_conn, width, height))
            self.gui_process.start()

        self.running = True
        self.denoiser = Denoiser.create("MeanPixel", width, height)

        self.next_frame = True

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

    def normal_run(self):
        self.current = datetime.datetime.now()
        self.elapsed = (self.current - self.previous).total_seconds()
        self.previous = self.current
        self.lag += self.elapsed

        if self.parent_conn.poll():
            try:
                msg = self.parent_conn.recv()
            except EOFError:
                self.running = False
                return False
            self.collect_action(msg)

        while self.lag >= MS_PER_UPDATE:
            self.update()
            self.lag -= MS_PER_UPDATE
        return True

    def get_action_list(self):
        action_list = []
        action_list += ["Nothing"] * 10
        action_list += ["q"] * 60
        action_list += ["w"] * 250
        action_list += ["Up"] * 30
        action_list += ["Nothing"] * 10
        action_list += ["Down"] * 30
        action_list += ["q"] * 90
        action_list += ["e"] * 150 
        action_list += ["w"] * 280
        action_list += ["e"] * 45
        action_list += ["Up"] * 30
        action_list += ["Nothing"] * 10
        action_list += ["Down"] * 30
        action_list += ["e"] * 90
        action_list += ["q"] * 45
        action_list += ["w"] * 125
        action_list += ["e"] * 90
        action_list += ["w"] * 60
        action_list += ["e"] * 365


        return action_list

    def action_generator(self):

        if self.actions_list:
            self.actions[self.actions_list.pop(0)] = False
        else:
            return False
        if self.actions_list:
            self.actions[self.actions_list[0]] = True

        return True

    def animation_run(self):

        if not self.no_gui:
            if self.parent_conn.poll():
                try:
                    self.parent_conn.recv()
                except EOFError:
                    self.running = False
                    return False
        self.running = self.action_generator()
        self.update()
        return self.running

    def run(self):

        self.connector.run()
        self.previous = datetime.datetime.now()
        self.lag = 0
        while self.running:
            if not self._run():
                break
            image = self.connector.get_result(self.wait)
            if image is not None:
                # image = self.denoiser.denoise(image, self.connector)
                if self.record:
                    self.save_frame(image)
                if not self.no_gui:
                    try:
                        self.parent_conn.send(image.tobytes())
                    except BrokenPipeError:
                        self.running = False
                        break
                self.connector.run()

        print("Quitting")
        self.parent_conn.close()
        self.gui_process.terminate()
        self.gui_process.join()

    def send_and_query(self, status):
        image = self.connector.get_result(self.wait)
        try:
            self.parent_conn.send(image)
        except BrokenPipeError:
            self.running = False
        else:
            self.connector.run(self.send_and_query)

    def save_frame(self, data):

        data = np.reshape(data, (self.height, self.width*3))
        with open("animation/{}.png".format(self.frame), "wb") as f:
            w = png.Writer(self.width, self.height)
            w.write(f, data)

        self.frame += 1
