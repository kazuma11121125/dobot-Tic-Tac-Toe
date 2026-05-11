import json
from pathlib import Path

from match_coordinator import DualDobotMatch
from robot_controller import RobotController
from robot_types import RobotConfig


DEFAULT_CONFIG_PATH = Path("calibrated_corners.json")


def load_robot_config(path: Path, label: str, mark: str, default_port: str) -> RobotConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    robot_data = data[label]
    corners = {
        name: (float(point[0]), float(point[1]))
        for name, point in robot_data["corners"].items()
    }
    return RobotConfig(
        name=label,
        mark=mark,
        port=robot_data.get("port", default_port),
        corners=corners,
    )


def main():
    # 重要: corners は JSON から読み込みます。
    # 起動時に現在位置を退避位置として使い、Z の基準は起動時に 0 とします。
    config_path = DEFAULT_CONFIG_PATH
    config_a = load_robot_config(config_path, "A", "X", "/dev/ttyUSB0")
    config_b = load_robot_config(config_path, "B", "O", "/dev/ttyUSB1")

    robot_a = RobotController(config_a)
    robot_b = RobotController(config_b)
    match = DualDobotMatch(robot_a, robot_b)
    match.run()


if __name__ == "__main__":
    main()
