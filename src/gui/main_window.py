import gi
gi.require_version('Gtk', '3.0')  # noqa: E402
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

import datetime


class MainWindow(Gtk.Window):

    def __init__(self, w, h, child_conn):

        super(MainWindow, self).__init__(title="RayTracingOpenCL")
        self.child_conn = child_conn
        self.w, self.h = w, h
        self.already_pressed = {
                k: False for k in ["w", "a", "s", "d",
                                   "Up", "Left", "Right", "Down",
                                   "Escape", "q", "e", "plus", "minus"]}
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.image = Gtk.Image()
        vbox.pack_start(self.image, True, True, 0)

        self.status = Gtk.Label()

        vbox.pack_start(self.status, False, True, 0)
        self.add(vbox)

        self.connect("key-press-event", self.on_key_pressed)
        self.connect("key-release-event", self.on_key_released)
        GLib.io_add_watch(
                self.child_conn,
                GLib.PRIORITY_DEFAULT_IDLE,
                GLib.IOCondition(GLib.IO_IN),
                self.on_new_frame_ready,
                None)

        self.start = datetime.datetime.now()
        self.fps = 0

    def on_new_frame_ready(self, source_object, result, user_data):
        buff = source_object.recv()
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                    buff,
                    GdkPixbuf.Colorspace.RGB, False,
                    8, self.w, self.h, self.w * 3)
        self.image.set_from_pixbuf(pixbuf)

        self.stop = datetime.datetime.now()
        time_elapsed = (self.stop - self.start).total_seconds()
        self.fps = 0.9 * self.fps + (1/time_elapsed) * 0.1
        self.status.set_label("{:4.2f} FPS".format(self.fps))
        self.start = self.stop
        return True

    def on_key_released(self, source, event):
        key = Gdk.keyval_name(event.keyval)
        if key not in self.already_pressed:
            return
        self.already_pressed[key] = False
        self.child_conn.send("~" + key)

    def on_key_pressed(self, source, event):
        key = Gdk.keyval_name(event.keyval)
        if key not in self.already_pressed:
            return
        if not self.already_pressed[key]:
            self.already_pressed[key] = True
            self.child_conn.send(key)
