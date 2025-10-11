from dataclasses import dataclass, asdict
from functools import partial
from fibmeasure.fitting.transforms import RichardsonLucyDeconv, Binarize, Opening, CCSFilter, SkeletonizeEDT, LinFit


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
    def __init__(self, transform, visualization_key=None, transform_annotation=None, **slider_configs):
        init_values = {}

        for name, slider_params in slider_configs.items():
            init_values[name] = slider_params.current_value

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
    psf_size=SliderParams(view_name='PSF Size', current_value=4, min=2, max=9, step=1, dtype=int, annotation='Point spread function kernel size, kernel is square and uniform.'),
    num_iter=SliderParams(view_name='Number of iterations', current_value=4, min=1, max=30, step=1, dtype=int, annotation='This parameter plays the role of regularisation. See skimage.restoration.richardson_lucy')
)


VBinarize = partial(
    TransformView,
    Binarize,
    threshold=SliderParams(view_name='Threshold', current_value=0.5, min=0, max=1, step=0.01, dtype=float, annotation='Binary threshold for grayscaled image.')
)


VOpening = partial(
    TransformView,
    Opening,
    radius=SliderParams(view_name='Opening size', current_value=5, min=0, max=16, step=1, dtype=int, annotation='Kernel size for binary opening operation. This is approximately the maximum size of the connectivity components to be removed.')
)


VCCSFilter = partial(
    TransformView,
    CCSFilter,
    min_ratio=SliderParams(view_name='Min size ratio', current_value=1e-3, min=1e-4, max=1e-2, step=1e-4, dtype=float, annotation='The ratio of the connectivity component volume to the image volume, below which the connectivity component is removed.')
)


VSkeletonizeEDT = partial(
    TransformView,
    SkeletonizeEDT,
    threshold_abs=SliderParams(view_name='Min dist', current_value=5, min=1, max=50, step=0.1, dtype=float, annotation='Minimum distance from the extremum to the edge.'),
    dilation_radius=SliderParams(view_name='Dilation size', current_value=1, min=0, max=4, step=1, dtype=int, annotation='The radius of expansion of the points obtained. Expansion is applied after finding the maximum points.'),
    min_size=SliderParams(view_name='Min size', current_value=11, min=1, max=1000, step=1, dtype=int, annotation='Min size of connected component, filter is applied at the end.')
)


VLinFit = partial(
    TransformView,
    LinFit,
    block=SliderParams(view_name='Block size', current_value=64, min=4, max=128, step=4, dtype=int, annotation='The size of the block within which interpolation will take place.'),
    abs_rvalue_thr=SliderParams(view_name='Minimal r-value', current_value=0.8, min=0, max=1, step=0.01, dtype=float, annotation='Minimal Pierson correlation coefficient'),
    use_filtration_image=SliderParams(view_name='Use filtration image', current_value=True, min=0, max=1, step=1, dtype=bool, annotation='Whether to use the image from the previous step for additional filtering.'),
    filtration_thr=SliderParams(view_name='Min filtration recall', current_value=0.9, min=0, max=1, step=0.01, dtype=float, annotation='How well the interpolated line inside the block should intersect with the image. Only works if use_filtration_image=True.'),
)
