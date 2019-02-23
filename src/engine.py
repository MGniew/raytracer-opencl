from src.opencl_connector import Connector
from src.gui.main_window import MainWindow
from src.scene import Scene
from gi.repository import Gtk

from src.objects.light import Light
from src.objects.camera import Camera
from src.material import Material
from multiprocessing import Pipe, Process
import threading
import datetime
import time


def gui_worker(child_conn, w=300, h=300):
    win = MainWindow(w, h, child_conn)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


class Engine(object):

    def __init__(self, kernel_filename, scene_filename, width, height):
        scene = Scene(None, None)
        scene.load_from_json(scene_filename)
        self.camera = Camera(width, height)
        scene.add_object(self.camera)
        scene.add_object(Light(
            Material(
                [0.5, 0.4, 0.5],
                [0.5, 0.5, 0.5],
                [0.4, 0.3, 0.4]),
            [0, 5, 2]))
        self.connector = Connector(
                kernel_filename, scene, width, height)

        self.parent_conn, child_conn = Pipe()
        self.gui_process = Process(
                target=gui_worker, args=(child_conn, width, height))
        self.gui_process.start()

        self.actions = {a: False for a in ["w", "a", "s", "d"]}
        # self.input_thread = Process(target=self.input_worker)
        # self.input_thread.start()

    #  def input_worker(self):
    #      while True:
    #          msg = self.parent_conn.recv()
    #          print(msg)

    def collect_action(self, action):

        value = True
        if action[0] == "~":
            action = action[1:]
            value = False

        if action in self.actions:
            self.actions[action] = value

    def run(self):

        # self.connector.run(self.send_and_query)
        self.connector.run()
        # start = datetime.datetime.now()
        # stop = datetime.datetime.now()

        while True:
            if self.parent_conn.poll():
                msg = self.parent_conn.recv()
                self.collect_action(msg)

            # delta = stop - start
            # if delta.total_seconds() > 0.001:
            #     start = datetime.datetime.now() + ....
            #     self.camera.move(
            #             self.actions["w"],
            #             self.actions["s"],
            #             self.actions["a"],
            #             self.actions["d"])

            image = self.connector.get_if_finished()
            if image:
                self.camera.move(
                        self.actions["w"],
                        self.actions["s"],
                        self.actions["a"],
                        self.actions["d"])
                self.parent_conn.send(image)
                self.connector.run()

        self.gui_process.join()

    def send_and_query(self, status):
        image = self.connector.get_if_finished()
        self.parent_conn.send(image)
        self.connector.run(self.send_and_query)
