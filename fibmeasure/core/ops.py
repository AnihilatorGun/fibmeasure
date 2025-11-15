from dataclasses import dataclass

import numpy as np
from scipy.ndimage import map_coordinates


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
    block: int
    params: np.ndarray
    block_indices: np.ndarray


def blocked_line_fitting_tls(
    skeleton, linearity_thr=100.0, block=16, filtration_image=None, filtration_thr=0.8, dist_thr=2
):
    H, W = skeleton.shape
    half_block = block // 2

    x_c = np.arange(block)
    y_c = np.arange(block)

    H_block = (H + half_block - 1) // half_block
    W_block = (W + half_block - 1) // half_block

    params = []
    block_indices = []

    for i in range(H_block):
        for j in range(W_block):
            y_start, y_end = i * half_block, (i + 2) * half_block
            x_start, x_end = j * half_block, (j + 2) * half_block

            crop = skeleton[y_start:y_end, x_start:x_end]

            if np.count_nonzero(crop) < 4:
                continue

            y, x = np.where(crop)
            A, B, C, linearity = line_params_tls(x, y)

            if linearity < linearity_thr:
                continue

            if filtration_image is None:
                params.append((A, B, C))
                block_indices.append((i, j))
                continue

            block_mask = np.abs(A * x_c[None, :] + B * y_c[:, None] + C) < dist_thr

            filtration_crop = filtration_image[y_start:y_end, x_start:x_end]
            h, w = filtration_crop.shape
            block_mask = block_mask[:h, :w]

            n_line_pixels = np.count_nonzero(block_mask)
            n_filtered = np.count_nonzero(filtration_crop & block_mask)

            if n_line_pixels * filtration_thr <= n_filtered:
                params.append((A, B, C))
                block_indices.append((i, j))

    params = np.asarray(params, dtype=np.float32)
    block_indices = np.asarray(block_indices, dtype=int)

    return Fitting(skeleton.shape, block, params, block_indices)


def visualize_fitting(fitting, dist_thr=2):
    block = fitting.block
    half_block = block // 2
    params = fitting.params
    block_indices = fitting.block_indices

    result = np.zeros(fitting.origin_shape, dtype=bool)
    x_c, y_c = np.arange(block), np.arange(block)

    for (i, j), (A, B, C) in zip(block_indices, params, strict=True):
        y_start, y_end = i * half_block, (i + 2) * half_block
        x_start, x_end = j * half_block, (j + 2) * half_block
        block_mask = np.abs(A * x_c[None, :] + B * y_c[:, None] + C) < dist_thr

        h, w = result[y_start:y_end, x_start:x_end].shape
        block_mask = block_mask[:h, :w]

        result[y_start:y_end, x_start:x_end] = block_mask

    return result


def measure_thickness(
    image: np.ndarray,
    fitting,
    *,
    angles_jitter_deg=15,
    jitter_step_deg=1,
    intervals_dist=4,
    max_halfthickness=50,
    steps_per_pix=1,
    boundary_threshold=0.5,
    lp=25,
):
    block = fitting.block
    half_block = block // 2
    params = fitting.params
    block_indices = fitting.block_indices

    intervals = []

    for (i, j), (A, B, C) in zip(block_indices, params):
        offset = np.array([i * half_block, j * half_block])
        d = np.array([A, -B], dtype=np.float32)
        p = np.array([B, A], dtype=np.float32)

        if abs(B) > abs(A):
            x0 = 0
            y0 = -C / B
        else:
            y0 = 0
            x0 = -C / A

        max_shift = 2 * d * block
        n_points = np.ceil(4 * block / intervals_dist).astype(int)
        points = np.array([y0, x0], dtype=np.float32) + np.linspace(-max_shift, max_shift, n_points)
        points = np.round(points).astype(np.uint16)

        points_mask = (points[:, 0] >= 0) & (points[:, 0] < block) & (points[:, 1] >= 0) & (points[:, 1] < block)
        points = points[points_mask]

        segments = measure_fiber_thickness_with_jitter(
            points=points + offset,
            pv=p,
            image=image,
            max_halfthickness=max_halfthickness,
            steps_per_pix=steps_per_pix,
            angles_jitter_deg=angles_jitter_deg,
            jitter_step_deg=jitter_step_deg,
            boundary_threshold=boundary_threshold,
            lp=lp,
        )

        intervals.append(segments)

    intervals = np.concat(intervals, axis=0)

    return intervals


def measure_fiber_thickness_with_jitter(
    points,
    pv,
    image,
    max_halfthickness,
    steps_per_pix=1,
    angles_jitter_deg=15,
    jitter_step_deg=1,
    boundary_threshold=0.5,
    lp=25,
):
    assert np.issubdtype(image.dtype, np.floating)
    assert isinstance(max_halfthickness, int)

    steps = np.linspace(
        -max_halfthickness, max_halfthickness, 2 * max_halfthickness * steps_per_pix + 1, dtype=np.float32
    )
    center_idx = max_halfthickness * steps_per_pix

    angles_positive_deg = np.arange(0, angles_jitter_deg + jitter_step_deg, jitter_step_deg)
    angles = np.deg2rad(np.concatenate([-angles_positive_deg[1:][::-1], angles_positive_deg]))
    cos_a, sin_a = np.cos(angles), np.sin(angles)
    R = np.stack([np.stack([cos_a, -sin_a], axis=1), np.stack([sin_a, cos_a], axis=1)], axis=1)  # (K, 2, 2)
    pv_rot = (R @ pv[None, :, None])[..., 0]  # (K, 2)

    p_all = points[:, None, None, :] + steps[None, None, :, None] * pv_rot[None, :, None, :]  # p_all: (N, K, S, 2)

    interpolated = map_coordinates(image, np.moveaxis(p_all, -1, 0), order=1, mode='nearest', prefilter=False)
    inside = interpolated >= boundary_threshold  # inside: (N, K, S)

    left_mask = inside[..., :center_idx][..., ::-1]
    right_mask = inside[..., center_idx + 1 :]

    left_dist = np.argmax(~left_mask, axis=-1) + 1
    right_dist = np.argmax(~right_mask, axis=-1) + 1

    left_dist[left_mask.all(axis=-1)] = left_mask.shape[-1]
    right_dist[right_mask.all(axis=-1)] = right_mask.shape[-1]

    points_minus = points[:, None, :] - pv_rot[None, :, :] * left_dist[..., None] / steps_per_pix
    points_plus = points[:, None, :] + pv_rot[None, :, :] * right_dist[..., None] / steps_per_pix

    lengths = np.linalg.norm(points_plus - points_minus, axis=-1)  # (N, K)

    lengths_percentile = np.percentile(lengths, q=lp, axis=-1)
    angle_indices = np.arange(len(angles))
    best_idx = np.array(
        [np.mean(angle_indices[length <= length_p]) for length, length_p in zip(lengths, lengths_percentile)]
    )
    best_idx = np.round(best_idx).astype(int)

    rows = np.arange(points.shape[0])

    segments_best = np.stack([points_minus[rows, best_idx], points_plus[rows, best_idx]], axis=1)

    return segments_best
