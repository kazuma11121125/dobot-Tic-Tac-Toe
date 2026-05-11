import math

from robot_types import Corners, Point


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def bilinear(corners: Corners, u: float, v: float) -> Point:
    # corners の left_back, right_back, left_front, right_front を使って、(u, v) に対応する座標を返す。
    left_back = corners["left_back"]
    right_back = corners["right_back"]
    left_front = corners["left_front"]
    right_front = corners["right_front"]

    top = (lerp(left_back[0], right_back[0], u), lerp(left_back[1], right_back[1], u))
    bottom = (lerp(left_front[0], right_front[0], u), lerp(left_front[1], right_front[1], u))
    return lerp(top[0], bottom[0], v), lerp(top[1], bottom[1], v)


def get_cell_center(corners: Corners, cell: int) -> Point:
    # cell は 1 から 9 までの整数で、左上が 1、右下が 9 とする。
    idx = cell - 1
    row = idx // 3
    col = 2 - (idx % 3)
    u = (col + 0.5) / 3.0
    v = (row + 0.5) / 3.0
    return bilinear(corners, u, v)


def orthogonalize_corners(corners: Corners) -> Corners:
    left_back = corners["left_back"]
    right_back = corners["right_back"]
    left_front = corners["left_front"]
    right_front = corners["right_front"]

    center_x = (left_back[0] + right_back[0] + left_front[0] + right_front[0]) / 4.0
    center_y = (left_back[1] + right_back[1] + left_front[1] + right_front[1]) / 4.0

    width_vec = (
        (right_back[0] - left_back[0]) + (right_front[0] - left_front[0]),
        (right_back[1] - left_back[1]) + (right_front[1] - left_front[1]),
    )
    width_norm = math.hypot(width_vec[0], width_vec[1])
    if width_norm == 0.0:
        return corners
    u = (width_vec[0] / width_norm, width_vec[1] / width_norm)

    height_vec = (
        (left_front[0] - left_back[0]) + (right_front[0] - right_back[0]),
        (left_front[1] - left_back[1]) + (right_front[1] - right_back[1]),
    )
    proj = height_vec[0] * u[0] + height_vec[1] * u[1]
    ortho_h = (height_vec[0] - proj * u[0], height_vec[1] - proj * u[1])
    height_norm = math.hypot(ortho_h[0], ortho_h[1])
    if height_norm == 0.0:
        v = (-u[1], u[0])
    else:
        v = (ortho_h[0] / height_norm, ortho_h[1] / height_norm)

    width = (
        math.hypot(right_back[0] - left_back[0], right_back[1] - left_back[1])
        + math.hypot(right_front[0] - left_front[0], right_front[1] - left_front[1])
    ) / 2.0
    height = (
        math.hypot(left_front[0] - left_back[0], left_front[1] - left_back[1])
        + math.hypot(right_front[0] - right_back[0], right_front[1] - right_back[1])
    ) / 2.0

    half_w = width / 2.0
    half_h = height / 2.0

    return {
        "left_back": (center_x - u[0] * half_w - v[0] * half_h, center_y - u[1] * half_w - v[1] * half_h),
        "right_back": (center_x + u[0] * half_w - v[0] * half_h, center_y + u[1] * half_w - v[1] * half_h),
        "left_front": (center_x - u[0] * half_w + v[0] * half_h, center_y - u[1] * half_w + v[1] * half_h),
        "right_front": (center_x + u[0] * half_w + v[0] * half_h, center_y + u[1] * half_w + v[1] * half_h),
    }
