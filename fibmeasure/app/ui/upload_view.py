import flet as ft


class UploadView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="upload")

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        page.overlay.append(self.file_picker)
        self.image_preview = ft.Image(expand=True, fit=ft.ImageFit.CONTAIN)
        self.selected_path = None

        self.controls = [
            ft.Column(
                [
                    ft.Text("Choose image for analysis", size=24, weight="bold"),
                    ft.ElevatedButton("Choose file", on_click=self.pick_file),
                    self.image_preview,
                    ft.ElevatedButton("Next step", on_click=self.next_step, disabled=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=10
            )
        ]

    def pick_file(self, e):
        self.file_picker.pick_files(allow_multiple=False)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_path = e.files[0].path
            self.image_preview.src = self.selected_path
            self.controls[0].controls[-1].disabled = False  # Make button "Next step" active
            self.update()

    def next_step(self, e):
        self.page.client_storage.set("input_image", self.selected_path)
        self.page.go("transform")
