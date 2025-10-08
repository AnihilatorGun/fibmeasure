import numpy as np
from imops import binary_dilation, binary_opening, label
from skimage.morphology import disk, skeletonize

from .base import Transform
from .ops import blocked_lin_fit


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


class Skeletonize(Transform):
    def __init__(self, dilation_radius=3):
        self.dilation_radius = dilation_radius

    def skeleton(self, bin_image):
        skeleton = skeletonize(bin_image)

        if self.dilation_radius > 0:
            skeleton = binary_dilation(skeleton, disk(self.dilation_radius))

        return skeleton


class LinFit(Transform):
    def __init__(self, abs_rvalue_thr = 0.8, block = 64, use_filtration_image = True, filtration_thr = 0.9):
        self.abs_rvalue_thr = abs_rvalue_thr
        self.block = block
        self.use_filtration_image = use_filtration_image
        self.filtration_thr = filtration_thr

    def image_lined(self, skeleton, bin_image):
        filtration_image = bin_image if self.use_filtration_image else None

        return blocked_lin_fit(
            skeleton, 
            abs_rvalue_thr=self.abs_rvalue_thr,
            block=self.block,
            filtration_image=filtration_image,
            filtration_thr=self.filtration_thr
        )
