import os
from subprocess import call
import chess
import dearpygui.dearpygui as dpg

from threadpool import threadpool


class Gui:
    def __init__(self):
        self.popup_items = []

        self.init()

    def init(self):
        dpg.create_context()
        dpg.create_viewport(title='Chessr', width=1500,
                            height=1000, resizable=False)

        width, height, channels, data = dpg.load_image("out.svg.png")
        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                width=width, height=height, default_value=data, tag="board")

        with dpg.window(label="Status paneel", width=500, height=500, no_resize=True, no_close=True, no_collapse=True, no_title_bar=True, no_move=True):
            dpg.add_text("Status paneel")
            self.turn_text = dpg.add_text(".... ... aan de beurt")
            dpg.add_button(label="Exit!", callback=self.stop_callback)

        with dpg.window(label="Controle paneel", width=500, height=500, pos=(0, 500), no_resize=True, no_close=True, no_collapse=True, no_title_bar=True, no_move=True) as self.control_panel:
            dpg.add_text("Controle paneel")

        with dpg.window(label="Bord", width=1000, height=1000, pos=(500, 0), no_resize=True, no_close=True, no_collapse=True, no_title_bar=True, no_move=True) as self.bord_panel:
            dpg.add_image("board")

        dpg.setup_dearpygui()
        dpg.show_viewport()

    def set_turn(self, turn):
        if turn == chess.WHITE:
            dpg.set_value(self.turn_text, "Jij bent aan de beurt")
        else:
            dpg.set_value(self.turn_text, "Chessr is aan de beurt")

    def set_board(self):
        os.system("qlmanage -t -s 982 -o . out.svg")
        width, height, channels, data = dpg.load_image("out.svg.png")
        with dpg.texture_registry():
            dpg.set_value("board", data)

    def popup_options(self, title, options, callback):
        self.popup_items.append(dpg.add_text(title, parent=self.control_panel))
        for option in options:
            self.popup_items.append(dpg.add_button(
                label=option, callback=callback, user_data=option, parent=self.control_panel))

    def popup_string_callback(self, sender, app_data, user_data):
        self.callback(dpg.get_value("popup_input"))

    def popup_string(self, prompt, callback):
        self.callback = callback
        self.popup_items.append(dpg.add_text(
            prompt, parent=self.control_panel))
        self.popup_items.append(dpg.add_input_text(
            tag="popup_input", parent=self.control_panel))
        self.popup_items.append(dpg.add_button(
            label="Oke", callback=self.popup_string_callback, parent=self.control_panel))

    def remove_popups(self):
        for item in self.popup_items:
            dpg.delete_item(item)
        self.popup_items = []

    def update(self):
        if not dpg.is_dearpygui_running():
            return False
        dpg.render_dearpygui_frame()
        return True

    def stop_callback(self, sender, app_data, user_data):
        self.stop()

    def stop(self):
        dpg.stop_dearpygui()
        dpg.destroy_context()
