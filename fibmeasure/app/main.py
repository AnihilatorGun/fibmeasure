import flet as ft
from ui.upload_view import UploadView
#from .ui.transform_view import TransformView
#from .ui.result_view import ResultView

def main(page: ft.Page):
    page.title = "Fiber Thickness Analyzer"
    page.window_width = 1200
    page.window_height = 1200
    page.theme_mode = "light"

    # Навигация между экранами
    views = {
        "upload": UploadView(page),
        #"transform": TransformView(page),
        #"result": ResultView(page),
    }

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        page.views.append(views[e.route])
        page.update()

    page.on_route_change = route_change
    page.go("upload")

ft.app(target=main)