import numpy as np
from scipy.stats import linregress


def blocked_lin_fit(skeleton, abs_rvalue_thr=0.8, block=16, filtration_image=None, filtration_thr=0.8):
    H, W = skeleton.shape

    result = np.zeros_like(skeleton)

    half_block = block // 2

    for i in range((H + half_block - 1) // half_block):
        for j in range((W + half_block - 1) // half_block):
            crop = skeleton[i * half_block: (i + 2) * half_block, j * half_block: (j + 2) * half_block]

            if crop.sum() >= 4:
                y, x = np.where(crop)

                if np.any(np.diff(x) != 0):
                    line_fit = linregress(x, y)
    
                    if np.abs(line_fit.rvalue) >= abs_rvalue_thr:
                        intercept, slope = line_fit.intercept, line_fit.slope
                        x_c, y_c = np.arange(block), np.arange(block)
    
                        block_lin_interp = np.abs(x_c[None, :] * slope + intercept - y_c[:, None]) < 2

                        assign_size = result[i * half_block: (i + 2) * half_block, j * half_block: (j + 2) * half_block].shape
                        block_lin_interp = block_lin_interp[:assign_size[0], :assign_size[1]]

                        if filtration_image is None:
                            result[i * half_block: (i + 2) * half_block, j * half_block: (j + 2) * half_block] = block_lin_interp
                        else:
                            filtration_crop = filtration_image[i * half_block: (i + 2) * half_block, j * half_block: (j + 2) * half_block]
                            
                            if block_lin_interp.sum() * filtration_thr <= (filtration_crop & block_lin_interp).sum():
                                result[i * half_block: (i + 2) * half_block, j * half_block: (j + 2) * half_block] = block_lin_interp

    return result
