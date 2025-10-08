import flet as ft


def is_valid_pixel_spacing(pixel_spacing):
    try:
        pixel_spacing = float(pixel_spacing)
        return True
    except ValueError:
        return False


class UploadView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="upload")
        self.page = page

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        page.overlay.append(self.file_picker)

        self.image_preview = ft.Image(expand=True, fit=ft.ImageFit.CONTAIN)
        self.source_path = None

        self.choose_btn = ft.ElevatedButton("Choose file", on_click=self.pick_file)
        self.next_btn = ft.ElevatedButton("Next step", on_click=self.next_button_click, disabled=True)

        self.pixel_spacing_tf = ft.TextField(
            label="Pixel spacing", 
            width=600, 
            helper_text='Must be a positive real number, separator - a period',
            on_change=self.pixel_spacing_on_change
        )

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Choose image for analysis", size=32, weight="bold"),
                        self.choose_btn,
                        self.image_preview,
                        self.pixel_spacing_tf,
                        self.next_btn,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ]

    def pixel_spacing_on_change(self, e):
        value = e.control.value

        if not is_valid_pixel_spacing(value):
            self.pixel_spacing_tf.error_text = 'Invalid pixel spacing. Must be a positive real number, separator - a period'
        else:
            self.pixel_spacing_tf.error_text = None

        self.page.update()

    def pick_file(self, e):
        self.file_picker.pick_files(allow_multiple=False)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.source_path = e.files[0].path
            self.image_preview.src = self.source_path
            self.next_btn.disabled = False  # Make button "Next step" active
            self.page.update()

    def next_button_click(self, e):
        if is_valid_pixel_spacing(self.pixel_spacing_tf.value):
            self.next_step(e)

    def next_step(self, e):
        self.page.session.set("source_path", self.source_path)
        self.page.session.set("pixel_spacing", float(self.pixel_spacing_tf.value))
        self.page.go("transform")
