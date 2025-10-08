import flet as ft
from ui.upload_view import UploadView
from ui.transform_view import TransformView
#from .ui.result_view import ResultView

def main(page: ft.Page):
    page.title = "Fiber Thickness Analyzer"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.maximized = True

    view_fabrics = {
        "upload": lambda: UploadView(page),
        "transform": lambda: TransformView(page),
        #"result": lambda: ResultView(page),
    }

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        page.views.append(view_fabrics[e.route]())
        page.update()

    page.on_route_change = route_change
    page.go("upload")

ft.app(target=main)
