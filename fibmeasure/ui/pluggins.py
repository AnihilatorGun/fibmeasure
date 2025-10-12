import flet as ft


class HoldButton(ft.GestureDetector):
    def __init__(self, text, on_hold_start=None, on_hold_end=None, *, width: int | None = None, height: int | None = None):
        self._on_hold_start = on_hold_start
        self._on_hold_end = on_hold_end
        self._holding = False

        self._enabled_color = ft.Colors.BLUE
        self._disabled_color = ft.Colors.GREY
        self._pressed_color = ft.Colors.BLUE_800

        self._container = ft.Container(
            content=ft.Text(text, color=ft.Colors.WHITE),
            bgcolor=self._enabled_color,
            border_radius=8,
            padding=10,
            width=width,
            height=height,
            alignment=ft.alignment.center,
        )

        super().__init__(
            content=self._container,
            on_tap_down=self._start_hold,
            on_tap_up=self._end_hold,
            on_pan_end=lambda e: self._end_hold(e),
            on_long_press_end=lambda e: self._end_hold(e),
            on_exit=lambda e: self._end_hold(e),
        )

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool):
        self._disabled = bool(value)
        self._container.bgcolor = (
            self._disabled_color if self._disabled else self._enabled_color
        )

        # Bypass initial disable=False setting
        if getattr(self._container, "_Control__page", None) is not None:
            self._container.update()

    def _start_hold(self, e):
        if self._holding or self.disabled:
            return
        self._holding = True

        self._container.bgcolor = self._pressed_color
        self._container.update()

        self._on_hold_start(e)

    def _end_hold(self, e):
        if not self._holding:
            return
        self._holding = False

        self._container.bgcolor = self._enabled_color
        self._container.update()

        self._on_hold_end(e)
