from copy import copy
from dataclasses import dataclass, asdict
from functools import partial, cache
from . import transforms
from ..assets import TRANSFORM_VIEW_ASSETS


type Param = int | float | bool


@dataclass
class SliderParams:
    view_name: str
    current_value: Param
    min: Param
    max: Param
    step: Param
    dtype: type
    annotation: str | None = None


class TransformView:
    def __init__(
        self, transform, visualization_key=None, transform_name=None, transform_annotation=None, **slider_configs
    ):
        init_values = {}

        for name, slider_params in slider_configs.items():
            init_values[name] = slider_params.current_value

        self._transform = transform(**init_values)
        self._slider_configs = slider_configs
        self.set_visualization_key(visualization_key)
        self._transform_name = transform_name
        self._transform_annotation = transform_annotation

    @property
    def transform_name(self):
        return self._transform.__class__.__name__ if self._transform_name is None else self._transform_name

    @property
    def transform_annotation(self):
        return '' if self._transform_annotation is None else self._transform_annotation

    @property
    def visualization_key(self):
        return self._visualization_key

    def __call__(self, node):
        return self._transform(node)

    def set_visualization_key(self, visualization_key):
        self._visualization_key = visualization_key

        if visualization_key is None:
            if len(self._transform._transform_methods) == 1:
                self._visualization_key = self._transform._transform_methods[0].__name__
            else:
                raise ValueError(
                    f'{self._transform.__class__.__name__} has multiple transformation fields, provide visualization_key manually'
                )

    def set_current_value(self, name, value):
        setattr(self._transform, name, value)

    def get_sliders(self):
        sliders = {}

        for name, slider_config in self._slider_configs.items():
            current_value = getattr(self._transform, name)
            slider = SliderParams(**asdict(slider_config))
            slider.current_value = current_value

            sliders[name] = slider

        return sliders


def _config2view_params(config):
    view_params = {}

    for name, value in config.items():
        if isinstance(value, dict):
            slider_params_parsed = copy(value)

            match slider_params_parsed['dtype']:
                case 'int':
                    dtype = int
                case 'float':
                    dtype = float
                case 'bool':
                    dtype = bool
                case _:
                    raise ValueError(f'Unknown dtype in {name} - {dtype}')
                
            slider_params_parsed['dtype'] = dtype

            for slider_param_name, slider_param_value in value.items():
                if slider_param_name != 'dtype' and slider_param_name != 'annotation' and slider_param_name != 'view_name':
                    slider_params_parsed[slider_param_name] = dtype(slider_param_value)

            view_params[name] = SliderParams(**slider_params_parsed)
        else:
            view_params[name] = value

    return view_params


@cache
def __getattr__(name):
    if name == "__path__":
        return []
    
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)

    match name:
        case "SliderParams":
            return SliderParams
        case "TransformView":
            return TransformView
        case "Param":
            return Param
        case _:
            if name.startswith("V") and (origin_name := name[1:]) in TRANSFORM_VIEW_ASSETS:
                config = TRANSFORM_VIEW_ASSETS[origin_name]
                transform_view_class = partial(
                    TransformView,
                    getattr(transforms, origin_name),
                    **_config2view_params(config),
                )
                return transform_view_class
            else:
                raise AttributeError(name)
