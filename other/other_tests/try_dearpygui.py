import dearpygui.dearpygui as dpg
import dearpygui.demo as demo


def main_demo():
    dpg.create_context()
    dpg.create_viewport(title="Custom Title", width=600, height=600)

    demo.show_demo()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


def main_hello_world():
    dpg.create_context()

    with dpg.window(label="Example Window", tag="primary_window"):
        dpg.add_text("Hello, world")
        dpg.add_button(label="Save")
        dpg.add_input_text(label="string", default_value="Quick brown fox")
        dpg.add_slider_float(label="float", default_value=0.273, max_value=1)

    # create viewport
    # The viewport is the window created by the operating system.
    dpg.create_viewport(title="My title", width=1280, height=720)
    # assign viewport
    dpg.setup_dearpygui()
    # show viewport
    dpg.show_viewport()
    # Associate DPG window to viewport, so that primary window fills viewport
    dpg.set_primary_window("primary_window", True)
    # mainloop
    dpg.start_dearpygui()
    dpg.destroy_context()


def main_directory_picker():
    dpg.create_context()

    def callback(sender, app_data):
        print("OK was clicked.")
        print("Sender: ", sender)
        print("App Data: ", app_data)

    def cancel_callback(sender, app_data):
        print("Cancel was clicked.")
        print("Sender: ", sender)
        print("App Data: ", app_data)

    dpg.add_file_dialog(
        directory_selector=True,
        show=False,
        callback=callback,
        tag="file_dialog_id",
        cancel_callback=cancel_callback,
        width=700,
        height=400,
    )

    with dpg.window(label="Tutorial", width=800, height=300):
        dpg.add_button(
            label="Directory Selector", callback=lambda: dpg.show_item("file_dialog_id")
        )

    dpg.create_viewport(title="Custom Title", width=800, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main_directory_picker()
