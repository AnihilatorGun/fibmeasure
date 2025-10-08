import flet as ft


class UploadView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="upload")
        self.page = page

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        page.overlay.append(self.file_picker)

        self.image_preview = ft.Image(expand=True, fit=ft.ImageFit.CONTAIN)
        self.selected_path = None

        self.choose_btn = ft.ElevatedButton("Choose file", on_click=self.pick_file)
        self.next_btn = ft.ElevatedButton("Next step", on_click=self.next_step, disabled=True)

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Choose image for analysis", size=32, weight="bold"),
                        self.choose_btn,
                        self.image_preview,
                        self.next_btn,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ]

    def pick_file(self, e):
        self.file_picker.pick_files(allow_multiple=False)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_path = e.files[0].path
            self.image_preview.src = self.selected_path
            self.next_btn.disabled = False  # Make button "Next step" active
            self.page.update()

    def next_step(self, e):
        self.page.client_storage.set("input_image", self.selected_path)
        self.page.go("transform")
