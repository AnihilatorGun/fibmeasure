from dataclasses import dataclass, asdict
from functools import partial
from fibmeasure.fitting.transforms import RichardsonLucyDeconv, Binarize, Opening, CCSFilter, SkeletonizeEDT, LinFit


type Param = int | float | bool


@dataclass
class SliderParams:
    min: Param
    max: Param
    step: Param
    dtype: type
    current_value: Param | None = None
    annotation: str | None = None


class TransformView:
    def __init__(self, transform, visualization_key=None, transform_annotation=None, **slider_configs):
        init_values = {}

        for name, slider_params in slider_configs.items():
            if (current_value := slider_params.current_value) is not None:
                init_values[name] = current_value

        self._transform = transform(**init_values)
        self._slider_configs = slider_configs
        self.set_visualization_key(visualization_key)
        self._transform_annotation = transform_annotation

    @property
    def transform_name(self):
        return self._transform.__class__.__name__
    
    @property
    def annotation(self):
        return self._transform_annotation
    
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
                raise ValueError(f'{self._transform.__class__.__name__} has multiple transformation fields, provide visualization_key manually')

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


VRichardsonLucyDeconv = partial(
    TransformView,
    RichardsonLucyDeconv,
    psf_size=SliderParams(min=2, max=9, step=1, dtype=int),
    num_iter=SliderParams(min=1, max=30, step=1, dtype=int)
)


VBinarize = partial(
    TransformView,
    Binarize,
    threshold=SliderParams(min=0, max=1, step=0.01, dtype=float)
)


VOpening = partial(
    TransformView,
    Opening,
    radius=SliderParams(min=0, max=16, step=1, dtype=int)
)


VCCSFilter = partial(
    TransformView,
    CCSFilter,
    min_ratio=SliderParams(min=1e-4, max=1e-2, step=1e-4, dtype=float)
)


VSkeletonizeEDT = partial(
    TransformView,
    SkeletonizeEDT,
    threshold_abs=SliderParams(min=1, max=50, step=0.1, dtype=float),
    dilation_radius=SliderParams(min=0, max=4, step=1, dtype=int),
    min_size=SliderParams(min=1, max=1000, step=1, dtype=int)
)


VLinFit = partial(
    TransformView,
    LinFit,
    abs_rvalue_thr=SliderParams(min=0, max=1, step=0.01, dtype=float),
    block=SliderParams(min=4, max=128, step=4, dtype=int),
    use_filtration_image=SliderParams(min=0, max=1, step=1, dtype=bool),
    filtration_thr=SliderParams(min=0, max=1, step=0.01, dtype=float),
)
