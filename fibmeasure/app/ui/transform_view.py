import base64
import flet as ft
import io
import numpy as np
from PIL import Image
from skimage.io import imread
from fibmeasure.fitting.transforms import Binarize, Opening, CCSFilter, Skeletonize, LinFit


def np_grayscale_to_base64(img):
    img_min, img_max = float(img.min()), float(img.max())
    if img_max == img_min:
        img8 = np.zeros_like(img, dtype=np.uint8)
    else:
        img8 = ((img - img_min) / (img_max - img_min) * 255).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(img8, mode="L").save(buf, format="PNG")

    return base64.b64encode(buf.getvalue()).decode("utf-8")


class TransformChain:
    transforms = [
        Binarize(),
        Opening(),
        CCSFilter(),
        Skeletonize(),
        LinFit()
    ]

    def __init__(self, source_image):
        self.source_image = source_image
        self.current_transform_idx = 0

        self.transform_result_nodes = {idx: None for idx in range(len(self.transforms))}

    def update_param(self, name, value):
        # Cached node results invalidation
        for idx in range(self.current_transform_idx, len(self.transforms)):
            self.transform_result_nodes[idx] = None

        setattr(self.transforms[self.current_transform_idx], name, value)

    def current_transform_name(self):
        return self.transforms[self.current_transform_idx].__class__.__name__

    def next(self):
        if self.current_transform_idx == len(self.transforms) - 1:
            return False
        
        self.current_transform_idx += 1
        return True
    
    def prev(self):
        if self.current_transform_idx == 0:
            return False
        
        self.current_transform_idx -= 1
        return True

    def get_result_node(self, transform_idx):
        if transform_idx == -1:
            result_node = {'image': self.source_image}
        else:
            result_node = self.transform_result_nodes[transform_idx]

        if result_node is None:
            prev_result_node = self.get_result_node(transform_idx - 1)
            result_node = self.transforms[transform_idx](prev_result_node)
            self.transform_result_nodes[transform_idx] = result_node

        return result_node
    
    def get_result_image(self, transform_idx):
        if transform_idx == -1:
            return self.source_image

        result_node = self.get_result_node(transform_idx)
        visualization_key = self.transforms[transform_idx].get_visualization_key()

        return result_node[visualization_key]

    def get_before_after_images(self):
        return self.get_result_image(self.current_transform_idx - 1), self.get_result_image(self.current_transform_idx)
    
    def get_sliders(self):
        return self.transforms[self.current_transform_idx].get_sliders()


class TransformView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="transform")
        self.page = page

        source_path = page.session.get("source_path")

        self.transform_manager = TransformChain(imread(source_path, as_gray=True).astype(np.float32))

        self.prev_btn = ft.ElevatedButton("Previous", on_click=self.prev_click)
        self.next_btn = ft.ElevatedButton("Next", on_click=self.next_click)

        image_width = page.window.width * 0.5
        image_height = page.window.height * 0.6
        self.before_image = ft.Image(
            width=image_width,
            height=image_height,
            fit=ft.ImageFit.CONTAIN
        )
        self.after_image = ft.Image(
            width=image_width,
            height=image_height,
            fit=ft.ImageFit.CONTAIN
        )

        self.header_text = ft.Text(f"Transform {self.transform_manager.current_transform_name()}", size=32, weight="bold")

        self.slider_view = ft.Column(
            self.build_slider_view_content(),
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        self.header_text,
                        ft.Row(
                            [
                                self.before_image,
                                self.after_image,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        self.slider_view,
                        ft.Row(
                            [
                                self.prev_btn,
                                self.next_btn
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ]

        self.update_images()

    def update_images(self):
        before_image, after_image = self.transform_manager.get_before_after_images()
        self.before_image.src_base64 = np_grayscale_to_base64(before_image)
        self.after_image.src_base64 = np_grayscale_to_base64(after_image)

    def build_slider_view_content(self):
        view_content = []
        self.name2value_type = {}
        self.name2param_text = {}

        for name, (min, max, step, curr_value, value_type) in self.transform_manager.get_sliders().items():
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
                min=min,
                max=max,
                value=curr_value,
                divisions=division,
                data=name,
                on_change=self.on_slider_change
            )
            view_content.append(param_text)
            view_content.append(slider)
            self.name2value_type[name] = value_type
            self.name2param_text[name] = param_text

        return view_content

    def on_slider_change(self, e: ft.ControlEvent):
        name = e.control.data
        value = e.control.value
        value_type = self.name2value_type[name]

        self.transform_manager.update_param(name, value_type(value))

        self.update_images()

        self.name2param_text[name].value = f"{name}: {value_type(value):.4f}"

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
