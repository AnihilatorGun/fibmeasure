import numpy as np
from imops import binary_dilation, binary_opening, label
from imops.morphology import distance_transform_edt
from skimage.feature import peak_local_max
from skimage.morphology import disk
from skimage.restoration import richardson_lucy

from .base import Transform
from .ops import blocked_lin_fit


class RichardsonLucyDeconv(Transform):
    def __init__(self, psf_size=4, num_iter=4):
        self.psf_size = psf_size
        self.num_iter = num_iter
        self.configure_slider('psf_size', 2, 9, 1, int)
        self.configure_slider('num_iter', 1, 30, 1, int)

    def image(self, image):
        psf = np.ones((self.psf_size, self.psf_size))
        psf /= psf.size

        return richardson_lucy(image, psf, num_iter=self.num_iter)


class Binarize(Transform):
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.configure_slider('threshold', 0, 1, 0.01, float)

    def bin_image(self, image):
        return image >= self.threshold


class Opening(Transform):
    def __init__(self, radius=5):
        self.radius = radius
        self.configure_slider('radius', 0, 16, 1, int)

    def bin_image(self, bin_image):
        return binary_opening(bin_image, disk(self.radius), num_threads=16)


class CCSFilter(Transform):
    def __init__(self, min_ratio=1e-3):
        self.min_ratio = min_ratio
        self.configure_slider('min_ratio', 1e-4, 1e-2, 1e-4, float)

    def bin_image(self, bin_image):
        ccs, labels, sizes = label(bin_image, return_labels=True, return_sizes=True)
        ratios = sizes / np.prod(bin_image.shape)

        return np.isin(ccs, labels[ratios >= self.min_ratio])


class SkeletonizeEDT(Transform):
    def __init__(self, threshold_abs=5, dilation_radius=0, min_size=10):
        self.threshold_abs = threshold_abs
        self.dilation_radius = dilation_radius
        self.min_size = min_size
        self.configure_slider('threshold_abs', 1, 50, 0.1, float)
        self.configure_slider('dilation_radius', 0, 4, 1, int)
        self.configure_slider('min_size', 1, 1000, 1, int)

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


class LinFit(Transform):
    def __init__(self, abs_rvalue_thr=0.8, block=64, use_filtration_image=True, filtration_thr=0.9):
        self.abs_rvalue_thr = abs_rvalue_thr
        self.block = block
        self.use_filtration_image = use_filtration_image
        self.filtration_thr = filtration_thr

        self.configure_slider('abs_rvalue_thr', 0, 1, 0.01, float)
        self.configure_slider('block', 4, 128, 4, int)
        self.configure_slider('use_filtration_image', 0, 1, 1, bool)
        self.configure_slider('filtration_thr', 0, 1, 0.01, float)

    def image_lined(self, skeleton, bin_image):
        filtration_image = bin_image if self.use_filtration_image else None

        return blocked_lin_fit(
            skeleton,
            abs_rvalue_thr=self.abs_rvalue_thr,
            block=self.block,
            filtration_image=filtration_image,
            filtration_thr=self.filtration_thr,
        )
