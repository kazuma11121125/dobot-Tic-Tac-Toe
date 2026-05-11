import math
import time

from pydobot import Dobot

from geometry import bilinear, get_cell_center, orthogonalize_corners
from robot_types import MAX_MOVE_RETRY, MOVE_RETRY_DELAY_SEC, Point, RobotConfig


class RobotController:
    def __init__(self, config: RobotConfig):
        self.config = config
        self.device = None
        self.board_corners = orthogonalize_corners(config.corners) if config.rectify_board else config.corners
        self.base_z = 0.0
        self.travel_z = 0.0
        self.write_z = 0.0
        self.home_xy = None
        self.start_z = 0.0

    def connect(self) -> None:
        print(f"{self.config.name} 接続中: {self.config.port}")
        self.device = Dobot(port=self.config.port, verbose=True)
        time.sleep(2)

        pose = self.get_current_pose()
        self.home_xy = (pose["x"], pose["y"])
        self.start_z = pose["z"]

        self.base_z = 0.0
        self.travel_z = self.config.travel_offset_mm
        self.write_z = self.config.write_offset_mm

        home_x, home_y = self.home_xy
        self.move_xy(pose["x"], pose["y"], self.travel_z)
        self.move_xy(home_x, home_y, self.travel_z)

        self.move_xy(home_x, home_y, self.travel_z)
        self.retreat()
        print(
            f"{self.config.name} ready: base_z={self.base_z:.2f}, start_z={self.start_z:.2f}, travel_z={self.travel_z:.2f}, "
            f"write_z={self.write_z:.2f}, start={self.home_xy}"
        )

    def close(self) -> None:
        if self.device is None:
            return
        try:
            self.retreat()
        finally:
            self.device.close()
            self.device = None

    def get_current_pose(self):
        if self.device is None:
            raise RuntimeError(f"{self.config.name} は未接続です")
        x, y, z, r, j1, j2, j3, j4 = self.device.pose()
        return {
            "x": x,
            "y": y,
            "z": z,
            "r": r,
            "j1": j1,
            "j2": j2,
            "j3": j3,
            "j4": j4,
        }

    def move_xy(self, x: float, y: float, z: float) -> None:
        if self.device is None:
            raise RuntimeError(f"{self.config.name} は未接続です")

        physical_z = self.start_z + z
        attempt = 0
        while True:
            try:
                self.device.move_to(x, y, physical_z, self.config.draw_r, wait=True)
                return
            except (AttributeError, OSError) as exc:
                attempt += 1
                print(f"{self.config.name} move_to 再試行 {attempt} 回目... ({type(exc).__name__})")
                if attempt >= MAX_MOVE_RETRY:
                    raise RuntimeError(
                        f"{self.config.name} move_to 失敗: x={x:.2f}, y={y:.2f}, z={z:.2f}(abs={physical_z:.2f}), r={self.config.draw_r:.2f}"
                    ) from exc
                time.sleep(MOVE_RETRY_DELAY_SEC)

    def retreat(self) -> None:
        if self.home_xy is None:
            raise RuntimeError(f"{self.config.name} は退避位置が未初期化です")
        x, y = self.home_xy
        self.move_xy(x, y, self.travel_z)

    def draw_board_frame(self) -> None:
        corners = self.board_corners
        left_back = corners["left_back"]
        right_back = corners["right_back"]
        left_front = corners["left_front"]
        right_front = corners["right_front"]

        self.draw_line(left_back, right_back)
        self.draw_line(right_back, right_front)
        self.draw_line(right_front, left_front)
        self.draw_line(left_front, left_back)

        for u in (1.0 / 3.0, 2.0 / 3.0):
            p_top = bilinear(corners, u, 0.0)
            p_bottom = bilinear(corners, u, 1.0)
            self.draw_line(p_top, p_bottom)

        for v in (1.0 / 3.0, 2.0 / 3.0):
            p_left = bilinear(corners, 0.0, v)
            p_right = bilinear(corners, 1.0, v)
            self.draw_line(p_left, p_right)

    def draw_mark(self, mark: str, cell: int) -> None:
        if mark == "X":
            self.draw_x(cell)
        elif mark == "O":
            self.draw_o(cell)
        else:
            raise ValueError(f"未対応のマークです: {mark}")

    def draw_line(self, p1: Point, p2: Point) -> None:
        self.move_xy(p1[0], p1[1], self.travel_z)
        self.move_xy(p1[0], p1[1], self.write_z)
        self.move_xy(p2[0], p2[1], self.write_z)
        self.move_xy(p2[0], p2[1], self.travel_z)

    def draw_x(self, cell: int) -> None:
        corners = self.board_corners
        idx = cell - 1
        row = idx // 3
        col = 2 - (idx % 3)

        margin = 0.2
        u0 = col / 3.0 + margin / 3.0
        u1 = (col + 1) / 3.0 - margin / 3.0
        v0 = row / 3.0 + margin / 3.0
        v1 = (row + 1) / 3.0 - margin / 3.0

        p1 = bilinear(corners, u0, v0)
        p2 = bilinear(corners, u1, v1)
        p3 = bilinear(corners, u0, v1)
        p4 = bilinear(corners, u1, v0)

        self.draw_line(p1, p2)
        self.draw_line(p3, p4)

    def draw_o(self, cell: int) -> None:
        corners = self.board_corners
        center = get_cell_center(corners, cell)
        radius_scale = 0.22

        idx = cell - 1
        row = idx // 3
        col = 2 - (idx % 3)

        left = bilinear(corners, col / 3.0, (row + 0.5) / 3.0)
        right = bilinear(corners, (col + 1) / 3.0, (row + 0.5) / 3.0)
        top = bilinear(corners, (col + 0.5) / 3.0, row / 3.0)
        bottom = bilinear(corners, (col + 0.5) / 3.0, (row + 1) / 3.0)

        cell_w = ((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2) ** 0.5
        cell_h = ((bottom[0] - top[0]) ** 2 + (bottom[1] - top[1]) ** 2) ** 0.5
        radius = min(cell_w, cell_h) * radius_scale

        steps = 24
        points = []
        for i in range(steps + 1):
            t = i / steps
            angle = 2.0 * math.pi * t
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))

        self.move_xy(points[0][0], points[0][1], self.travel_z)
        self.move_xy(points[0][0], points[0][1], self.write_z)
        for p in points[1:]:
            self.move_xy(p[0], p[1], self.write_z)
        self.move_xy(points[0][0], points[0][1], self.travel_z)
