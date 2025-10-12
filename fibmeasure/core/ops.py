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


def blocked_line_fitting_tls(skeleton, linearity_thr=100.0, block=16, filtration_image=None, filtration_thr=0.8, dist_thr=2):
    H, W = skeleton.shape

    result = np.zeros_like(skeleton)

    half_block = block // 2

    for i in range((H + half_block - 1) // half_block):
        for j in range((W + half_block - 1) // half_block):
            crop = skeleton[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block]

            if crop.sum() >= 4:
                y, x = np.where(crop)

                A, B, C, linearity = line_params_tls(x, y)

                if linearity >= linearity_thr:
                    x_c, y_c = np.arange(block), np.arange(block)

                    block_lin_interp = np.abs(A * x_c[None, :] + B * y_c[:, None] + C) < dist_thr

                    assign_size = result[
                        i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block
                    ].shape
                    block_lin_interp = block_lin_interp[: assign_size[0], : assign_size[1]]

                    if filtration_image is None:
                        result[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block] = (
                            block_lin_interp
                        )
                    else:
                        filtration_crop = filtration_image[
                            i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block
                        ]

                        if block_lin_interp.sum() * filtration_thr <= (filtration_crop & block_lin_interp).sum():
                            result[i * half_block : (i + 2) * half_block, j * half_block : (j + 2) * half_block] = (
                                block_lin_interp
                            )

    return result
