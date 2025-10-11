import base64
import flet as ft
import io
import numpy as np
from PIL import Image
from skimage.io import imread

from .pluggins import HoldButton
from fibmeasure.app.core.transform_handler import TransformHandler
from fibmeasure.app.core.utils import np_grayscale_to_base64


class TransformView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="transform")
        self.page = page

        source_path = page.session.get("source_path")

        source_image = imread(source_path, as_gray=True).astype(np.float32)
        self._buffer_image = np_grayscale_to_base64(source_image)

        self.transform_manager = TransformHandler(source_image)

        self.prev_btn = ft.ElevatedButton("Previous", on_click=self.prev_click)
        self.next_btn = ft.ElevatedButton("Next", on_click=self.next_click)
        self.show_source_btn = HoldButton(
            'Show source image',
            self.swap_right_image_with_buffer_image,
            self.swap_right_image_with_buffer_image,
        )

        image_width = page.window.width * 0.5
        image_height = page.window.height * 0.6
        self.before_image = ft.Image(width=image_width, height=image_height, fit=ft.ImageFit.CONTAIN)
        self.after_image = ft.Image(width=image_width, height=image_height, fit=ft.ImageFit.CONTAIN)

        self.header_text = ft.Text(
            f"Transform {self.transform_manager.current_transform_name()}", size=32, weight="bold"
        )

        self.slider_view = ft.Column(
            self.build_slider_view_content(),
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                self.header_text,
                                self.show_source_btn,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                self.before_image,
                                self.after_image,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        self.slider_view,
                        ft.Row(
                            [self.prev_btn, self.next_btn],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        ]

        self.update_images()

    def swap_right_image_with_buffer_image(self, e):
        tmp = self._buffer_image

        self._buffer_image = self.after_image.src_base64
        self.after_image.src_base64 = tmp

        self.after_image.update()

    def disable_buttons(self):
        self.prev_btn.disabled = True
        self.next_btn.disabled = True
        self.show_source_btn.disabled = True

    def enable_buttons(self):
        self.prev_btn.disabled = False
        self.next_btn.disabled = False
        self.show_source_btn.disabled = False

    def update_images(self):
        before_image, after_image = self.transform_manager.get_before_after_images()
        self.before_image.src_base64 = np_grayscale_to_base64(before_image)
        self.after_image.src_base64 = np_grayscale_to_base64(after_image)

    def build_slider_view_content(self):
        view_content = []
        self.name2value_type = {}
        self.name2param_text = {}

        for name, slider_params in self.transform_manager.get_sliders().items():
            min, max, step, curr_value, value_type = slider_params.min, slider_params.max, slider_params.step, slider_params.current_value, slider_params.dtype

            if value_type == float:
                division = (max - min) / step
            elif value_type == int:
                division = (max - min + step - 1) // step
            elif value_type == bool:
                division = 1
            else:
                raise RuntimeError(f"Unknown value_type - {value_type}")

            param_text = ft.Text(f"{name}: {curr_value:.4f}", size=16)
            slider = ft.Slider(
                min=min, max=max, value=curr_value, divisions=division, data=name, on_change=self.on_slider_change
            )
            view_content.append(param_text)
            view_content.append(slider)
            self.name2value_type[name] = value_type
            self.name2param_text[name] = param_text

        return view_content

    def on_slider_change(self, e: ft.ControlEvent):
        self.disable_buttons()
        self.page.update()

        name = e.control.data
        value = e.control.value
        value_type = self.name2value_type[name]

        self.transform_manager.update_param(name, value_type(value))
        self.update_images()
        self.name2param_text[name].value = f"{name}: {value_type(value):.4f}"

        self.enable_buttons()
        self.page.update()

    def prev_click(self, e):
        if self.transform_manager.prev():
            self.header_text.value = f"Transform {self.transform_manager.current_transform_name()}"

            self.update_images()

            new_sliders = self.build_slider_view_content()
            self.slider_view.controls.clear()
            self.slider_view.controls.extend(new_sliders)

            self.page.update()

    def next_click(self, e):
        if self.transform_manager.next():
            self.header_text.value = f"Transform {self.transform_manager.current_transform_name()}"

            self.update_images()

            new_sliders = self.build_slider_view_content()
            self.slider_view.controls.clear()
            self.slider_view.controls.extend(new_sliders)

            self.page.update()
