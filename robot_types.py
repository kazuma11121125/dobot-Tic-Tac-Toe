from dataclasses import dataclass
from typing import Dict, Tuple


MOVE_RETRY_DELAY_SEC = 0.2
MAX_MOVE_RETRY = 10
DEFAULT_DRAW_R = 45.0


Point = Tuple[float, float]
Corners = Dict[str, Point]


@dataclass
class RobotConfig:
    name: str
    mark: str
    port: str
    corners: Corners
    rectify_board: bool = True
    draw_r: float = DEFAULT_DRAW_R
    travel_offset_mm: float = 5.0
    write_offset_mm: float = -0.01
