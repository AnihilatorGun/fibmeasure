import numpy as np
from imops import binary_dilation, binary_opening, label
from imops.morphology import distance_transform_edt
from skimage.feature import peak_local_max
from skimage.morphology import disk
from skimage.restoration import richardson_lucy

from .base import Transform, Output
from .ops import blocked_line_fitting_tls, visualize_fitting, measure_thickness
from .utils import draw_segments_on_image


class RichardsonLucyDeconv(Transform):
    def __init__(self, psf_size=4, num_iter=4):
        self.psf_size = psf_size
        self.num_iter = num_iter

    def image(self, image):
        psf = np.ones((self.psf_size, self.psf_size))
        psf /= psf.size

        return richardson_lucy(image, psf, num_iter=self.num_iter)


class Binarize(Transform):
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def bin_image(self, image):
        return image >= self.threshold


class Opening(Transform):
    def __init__(self, radius=5):
        self.radius = radius

    def bin_image(self, bin_image):
        return binary_opening(bin_image, disk(self.radius), num_threads=16)


class CCSFilter(Transform):
    def __init__(self, min_ratio=1e-3):
        self.min_ratio = min_ratio

    def bin_image(self, bin_image):
        ccs, labels, sizes = label(bin_image, return_labels=True, return_sizes=True)
        ratios = sizes / np.prod(bin_image.shape)

        return np.isin(ccs, labels[ratios >= self.min_ratio])


class SkeletonizeEDT(Transform):
    def __init__(self, threshold_abs=5, dilation_radius=0, min_size=10):
        self.threshold_abs = threshold_abs
        self.dilation_radius = dilation_radius
        self.min_size = min_size

    def skeleton(self, bin_image):
        dist = distance_transform_edt(bin_image)
        peaks = peak_local_max(dist, min_distance=1, threshold_abs=self.threshold_abs, labels=bin_image)

        skeleton = np.zeros_like(bin_image)

        for point in peaks:
            skeleton[*point] = True

        if self.dilation_radius > 0:
            skeleton = binary_dilation(skeleton, disk(self.dilation_radius))

        ccs, labels, sizes = label(skeleton, return_labels=True, return_sizes=True)

        return np.isin(ccs, labels[sizes >= self.min_size])


class LineFittingTLS(Transform):
    def __init__(self, linearity_thr=200, block=64, use_filtration_image=True, filtration_thr=0.9):
        self.linearity_thr = linearity_thr
        self.block = block
        self.use_filtration_image = use_filtration_image
        self.filtration_thr = filtration_thr

    def image_lined(self, fitting_results: Output):
        return visualize_fitting(fitting_results)

    def fitting_results(self, skeleton, bin_image):
        filtration_image = bin_image if self.use_filtration_image else None

        return blocked_line_fitting_tls(
            skeleton,
            linearity_thr=self.linearity_thr,
            block=self.block,
            filtration_image=filtration_image,
            filtration_thr=self.filtration_thr,
        )


class SegmentsThickness(Transform):
    def __init__(
        self,
        angles_jitter_deg=10,
        jitter_step_deg=0.25,
        intervals_dist=16,
        max_halfthickness=50,
        steps_per_pix=4,
        boundary_threshold=0.45,
        lp=25,
    ):
        self.angles_jitter_deg = angles_jitter_deg
        self.jitter_step_deg = jitter_step_deg
        self.intervals_dist = intervals_dist
        self.max_halfthickness = max_halfthickness
        self.steps_per_pix = steps_per_pix
        self.boundary_threshold = boundary_threshold
        self.lp = lp

    def segments(self, image, fitting_results):
        return measure_thickness(
            image,
            fitting_results,
            angles_jitter_deg=self.angles_jitter_deg,
            jitter_step_deg=self.jitter_step_deg,
            intervals_dist=self.intervals_dist,
            max_halfthickness=self.max_halfthickness,
            steps_per_pix=self.steps_per_pix,
            boundary_threshold=self.boundary_threshold,
            lp=self.lp,
        )

    def segments_on_image(self, image, segments: Output):
        return draw_segments_on_image(image, segments)
