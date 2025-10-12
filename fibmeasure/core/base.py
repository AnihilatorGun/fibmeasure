from dataclasses import dataclass
from inspect import signature, isfunction
from typing import Any, Callable, List


type Output = Any


@dataclass(frozen=True)
class TransformSpec:
    method: Callable
    dependencies: List[str]
    params: List[str]


class Transform:
    """
    Base class for defining data transformations with declarative dependencies.

    A transformation is defined as a method of a subclass. 
    Methods can depend on outputs of other methods via `Output` annotation.
    Supports only depth-1 dependencies (Output of Output not allowed).
    """
    _name2transform_spec: dict[str, TransformSpec] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls is Transform:
            return

        cls._name2transform_spec = {}

        for name, method in cls.__dict__.items():
            if isfunction(method) and not name.startswith("_"):
                sig = signature(method)
                deps, params = [], []
                for param in sig.parameters.values():
                    if param.annotation == Output:
                        deps.append(param.name)
                    else:
                        params.append(param.name)

                cls._name2transform_spec[name] = TransformSpec(method, deps, params)

        # validate dependencies
        for name, spec in cls._name2transform_spec.items():
            for dep in spec.dependencies:
                if dep not in cls._name2transform_spec:
                    raise RuntimeError(
                        f"{cls.__name__}.{name} requires output '{dep}', "
                        f"but no method '{dep}' is defined."
                    )

                if cls._name2transform_spec[dep].dependencies:
                    raise RuntimeError(
                        f"{cls.__name__}.{name} requires '{dep}', but '{dep}' "
                        f"also requires an Output (depth > 1 not allowed)."
                    )

    def _run_transforms(self, inputs, outputs, require_output: bool):
        for name, spec in self._name2transform_spec.items():
            if (len(spec.dependencies) != 0) != require_output:
                continue

            params = {}
            for dep in spec.dependencies:
                if dep not in outputs:
                    raise ValueError(f"{name} depends on missing output '{dep}'")

                params[dep] = outputs[dep]

            for p in spec.params:
                if p == "self":
                    continue

                if p not in inputs:
                    raise ValueError(f"{self.__class__.__name__}.{name} requires '{p}'")

                params[p] = inputs[p]

            outputs[name] = spec.method(self, **params)

    def __call__(self, inputs: dict[str, Any]) -> dict[str, Any]:
        outputs = {}
        self._run_transforms(inputs, outputs, require_output=False)
        self._run_transforms(inputs, outputs, require_output=True)

        for k, v in inputs.items():
            outputs.setdefault(k, v)

        return outputs
