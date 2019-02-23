from gi.repository import Gtk, GdkPixbuf, GLib, Gdk


class MainWindow(Gtk.Window):

    def __init__(self, w, h, child_conn):

        super(MainWindow, self).__init__(title="RayTracingOpenCL")

        self.child_conn = child_conn
        self.w, self.h = w, h
        self.already_pressed = {
                k: False for k in ["w", "a", "s", "d",
                                   "Up", "Left", "Right", "Down",
                                   "Escape"]}

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.image = Gtk.Image()
        vbox.pack_start(self.image, True, True, 0)

        self.bar = Gtk.Statusbar()
        self.context = self.bar.get_context_id("default")
        self.bar.push(self.context, "Status")
        vbox.pack_start(self.bar, False, True, 0)
        self.add(vbox)

        self.connect("key-press-event", self.on_key_pressed)
        self.connect("key-release-event", self.on_key_released)
        GLib.io_add_watch(
                self.child_conn,
                GLib.PRIORITY_DEFAULT,
                GLib.IOCondition(GLib.IO_IN),
                self.on_new_frame_ready,
                None)

    def on_new_frame_ready(self, source_object, result, user_data):
        buff = source_object.recv()
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                    buff,
                    GdkPixbuf.Colorspace.RGB, False,
                    8, self.w, self.h, self.w*3)
        self.image.set_from_pixbuf(pixbuf)

        return True

    def on_key_released(self, source, event):
        key = Gdk.keyval_name(event.keyval)
        if key not in self.already_pressed:
            return
        self.already_pressed[key] = False
        self.child_conn.send("~" + key)

    def on_key_pressed(self, source, event):
        print("key")
        key = Gdk.keyval_name(event.keyval)
        if key not in self.already_pressed:
            return
        if not self.already_pressed[key]:
            self.already_pressed[key] = True
            self.child_conn.send(key)
