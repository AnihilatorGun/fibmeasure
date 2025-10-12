from copy import copy
from inspect import signature, isfunction
from typing import Any


type Output = Any


class Transform:
    _transform_name2transform_and_params = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._transform_name2transform_and_params = {}

        for name, method in cls.__dict__.items():
            if isfunction(method) and not name.startswith("_"):
                transform_signature = signature(method)
                required_output_names = []
                other_param_names = []

                for param in transform_signature.parameters.values():
                    param_name = param.name
                    param_annotation = param.annotation
                    
                    if param_annotation == Output:
                        required_output_names.append(param_name)
                    else:
                        other_param_names.append(param_name)

                cls._transform_name2transform_and_params[name] = (method, required_output_names, other_param_names)

        for transform_name, (_, required_output_names, other_param_names) in cls._transform_name2transform_and_params.items():
            for required_output in required_output_names:
                if required_output not in cls._transform_name2transform_and_params:
                    raise RuntimeError(
                        f'{transform_name} requires {required_output} to be implemented ({required_output} has Output annotation)'
                    )

                if len(cls._transform_name2transform_and_params[required_output][1]) != 0:
                    raise RuntimeError(
                        f'{transform_name} requires {required_output}, but '
                        f'implemented method for {required_output} also requires Output'
                    )

    def __call__(self, data_node):
        new_data_node = {}

        # First pass - only methods that do not require output
        for transform_name, (transform_method, required_output_names, other_param_names) in self._transform_name2transform_and_params.items():
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
        for transform_name, (transform_method, required_output_names, other_param_names) in self._transform_name2transform_and_params.items():
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
