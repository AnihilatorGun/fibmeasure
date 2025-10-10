import flet as ft


class HoldButton:
    def __init__(
        self, text: str, on_hold_start=None, on_hold_end=None, *, width: int | None = None, height: int | None = None
    ):
        self.text = text
        self.on_hold_start = on_hold_start
        self.on_hold_end = on_hold_end
        self.width = width
        self.height = height

        self._holding = False

    def _start_hold(self, e):
        if self._holding:
            return
        self._holding = True

        self._container.bgcolor = ft.Colors.BLUE_800
        self._container.update()

        if callable(self.on_hold_start):
            self.on_hold_start(e)

    def _end_hold(self, e):
        if not self._holding:
            return
        self._holding = False

        self._container.bgcolor = ft.Colors.BLUE
        self._container.update()

        if callable(self.on_hold_end):
            self.on_hold_end(e)

    def build(self):
        self._container = ft.Container(
            content=ft.Text(self.text, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE,
            border_radius=8,
            padding=10,
            width=self.width,
            height=self.height,
            alignment=ft.alignment.center,
        )

        return ft.GestureDetector(
            content=self._container,
            on_tap_down=self._start_hold,
            on_tap_up=self._end_hold,
            on_pan_end=lambda e: self._end_hold(e),
            on_long_press_end=lambda e: self._end_hold(e),
            on_exit=lambda e: self._end_hold(e),
        )
