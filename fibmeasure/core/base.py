from copy import copy
from inspect import signature, isfunction
from typing import Any


type Output = Any


class Transform:
    _transform_methods = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._transform_methods = []

        for name, method in cls.__dict__.items():
            if isfunction(method) and not name.startswith("_"):
                cls._transform_methods.append(method)

    def __call__(self, data_node):
        new_data_node = {}
        name2transform_and_required_output_names = {}

        for transform_method in self._transform_methods:
            name = transform_method.__name__
            transform_signature = signature(transform_method)
            required_output_names = []
            other_param_names = []
            
            for param in transform_signature.parameters.values():
                param_name = param.name
                param_annotation = param.annotation
                
                if param_annotation == Output:
                    required_output_names.append(param_name)
                else:
                    other_param_names.append(param_name)

            name2transform_and_required_output_names[name] = (transform_method, required_output_names, other_param_names)

        # Validation
        for transform_name, (_, required_output_names, _) in name2transform_and_required_output_names.items():
            for required_output in required_output_names:
                if required_output not in name2transform_and_required_output_names:
                    raise RuntimeError(f'{transform_name} requires {required_output} to be implemented as Output field')

                if len(name2transform_and_required_output_names[required_output][1]) != 0:
                    raise RuntimeError(f'{transform_name} requires {required_output}, but implemented method for {required_output} also requires Output')

        # First pass - only methods that do not require output
        for transform_name, (transform_method, required_output_names, other_param_names) in name2transform_and_required_output_names.items():
            if len(required_output_names) == 0:
                params_dict = {}

                for param_name in other_param_names:
                    if param_name != 'self':
                        if param_name not in data_node:
                            raise ValueError(f'{self.__class__.__name__}.{transform_name} requires {param_name}')

                        params_dict[param_name] = data_node[param_name]

                result = transform_method(self, **params_dict)
                new_data_node[transform_name] = result

        # Second pass - only methods that require output
        for transform_name, (transform_method, required_output_names, other_param_names) in name2transform_and_required_output_names.items():
            if len(required_output_names) != 0:
                params_dict = {required_output_name: new_data_node[required_output_name] for required_output_name in required_output_names}

                for param_name in other_param_names:
                    if param_name != 'self':
                        if param_name not in data_node:
                            raise ValueError(f'{self.__class__.__name__}.{transform_name} requires {param_name}')

                        params_dict[param_name] = data_node[param_name]

                result = transform_method(self, **params_dict)
                new_data_node[transform_name] = result

        for name, value in data_node.items():
            if name not in new_data_node:
                new_data_node[name] = value

        return new_data_node
