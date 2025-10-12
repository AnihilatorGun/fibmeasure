from dataclasses import dataclass
import numpy as np


def line_params_tls(x, y):
    x_mean, y_mean = x.mean(), y.mean()

    X = np.column_stack((x - x_mean, y - y_mean))
    cov = X.T @ X
    eigvals, eigvecs = np.linalg.eigh(cov)

    idx_min = np.argmin(eigvals)
    A, B = eigvecs[:, idx_min]
    C = -A * x_mean - B * y_mean

    linearity = eigvals.max() / max(eigvals.min(), 1e-9)

    return A, B, C, linearity


@dataclass
class Fitting:
    origin_shape: list
    block_size: int
    fitting_blocked_params: np.ndarray


def blocked_line_fitting_tls(skeleton, linearity_thr=100.0, block=16, filtration_image=None, filtration_thr=0.8, dist_thr=2):
    H, W = skeleton.shape

    half_block = block // 2

    H_block = (H + half_block - 1) // half_block
    W_block = (W + half_block - 1) // half_block
    fitting_blocked_params = np.zeros((H_block, W_block, 4), dtype=np.float32)

    for i in range(H_block):
        for j in range(W_block):
            crop = skeleton[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block]

            if crop.sum() >= 4:
                y, x = np.where(crop)

                A, B, C, linearity = line_params_tls(x, y)

                if linearity >= linearity_thr:
                    if filtration_image is None:
                        fitting_blocked_params[i, j] = np.asarray([A, B, C, 1])
                    else:
                        x_c, y_c = np.arange(block), np.arange(block)
                        block_lin_interp = np.abs(A * x_c[None, :] + B * y_c[:, None] + C) < dist_thr

                        filtration_crop = filtration_image[
                            i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block
                        ]
                        assign_size = filtration_crop.shape
                        block_lin_interp = block_lin_interp[: assign_size[0], : assign_size[1]]

                        if block_lin_interp.sum() * filtration_thr <= (filtration_crop & block_lin_interp).sum():
                            fitting_blocked_params[i, j] = np.asarray([A, B, C, 1])

    return Fitting(skeleton.shape, block, fitting_blocked_params)


def visualize_fitting(fitting, dist_thr=2):
    block = fitting.block_size
    half_block = block // 2
    fitting_blocked_params = fitting.fitting_blocked_params
    H_block, W_block = fitting.fitting_blocked_params.shape[:-1]

    result = np.zeros(fitting.origin_shape, dtype=bool)
    for i in range(H_block):
        for j in range(W_block):
            A, B, C, valid = fitting_blocked_params[i, j]

            if valid:
                x_c, y_c = np.arange(block), np.arange(block)
                block_lin_interp = np.abs(A * x_c[None, :] + B * y_c[:, None] + C) < dist_thr

                assign_size = result[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block].shape

                block_lin_interp = block_lin_interp[: assign_size[0], : assign_size[1]]

                result[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block] = block_lin_interp

    return result
