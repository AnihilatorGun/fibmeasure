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
    
    def configure_slider(self, name, min, max, step, value_type):
        if not hasattr(self, 'slider_configs'):
            self.slider_configs = {}

        self.slider_configs[name] = (min, max, step, value_type)

    def get_sliders(self):
        slider_configs = getattr(self, 'slider_configs', {})

        slider_params = {}

        for param, (min, max, step, value_type) in slider_configs.items():
            slider_params[param] = (min, max, step, getattr(self, param), value_type)

        return slider_params
