from copy import copy
from inspect import signature, isfunction
import ipywidgets as widgets
from IPython.display import display


class Transform:
    _transform_methods = []
    _visualization_key = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._transform_methods = []

        for name, method in cls.__dict__.items():
            if isfunction(method) and not name.startswith("_"):
                cls._transform_methods.append(method)
                last_name = name

        if len(cls._transform_methods) == 1:
            cls._visualization_key = last_name

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        
        if name == '_visualization_key' and value is None:
            raise ValueError(f'{self.__class__.__name__} implemented with multiple transformations. Set _visualization_key manually')
        
        return value

    def __setattr__(self, name, value):
        if name.startswith("_") or isfunction(value):
            super().__setattr__(name, value)
            return

        if not hasattr(self, "_changable_params"):
            super().__setattr__("_changable_params", {})

        self._changable_params[name] = value
        super().__setattr__(name, value)

    def __call__(self, data_node):
        new_data_node = copy(data_node)

        for transform_method in self._transform_methods:
            name = transform_method.__name__
            transform_signature = signature(transform_method)
            params_dict = {}

            for param in transform_signature.parameters:
                if param != 'self':
                    if param not in data_node:
                        raise ValueError(f'{self.__class__.__name__}.{name} requires {param}')

                    params_dict[param] = data_node[param]

            result = transform_method(self, **params_dict)
            new_data_node[name] = result

        return new_data_node
    
    def get_visualization_key(self):
        return self._visualization_key

    def get_sliders(self):
        sliders = {}
        for name, value in self._changable_params.items():
            slider = None
            
            if isinstance(value, int):
                slider = widgets.IntSlider(value=value, min=0, max=value*2 or 10, description=name)
            elif isinstance(value, float):
                slider = widgets.FloatSlider(value=value, min=0.0, max=value*2 or 1.0, step=0.01, description=name)
            elif isinstance(value, bool):
                slider = widgets.SelectionSlider(value=value, options=[True, False], description=name)
            sliders[name] = slider
        return sliders

    def interactive_view(self, data_node, visualize_func):
        sliders = self.get_sliders()

        def update(**kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            result = self(data_node)
            visualize_func(result)

        out = widgets.interactive_output(update, sliders)
        display(widgets.VBox(list(sliders.values())))
        display(out)
