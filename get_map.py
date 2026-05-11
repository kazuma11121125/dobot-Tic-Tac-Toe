import json
from pathlib import Path

from pydobot import Dobot


DEFAULT_PORTS = {
    "A": "/dev/ttyUSB0",
    "B": "/dev/ttyUSB1",
}
DEFAULT_OUTPUT_PATH = Path("calibrated_corners.json")
CORNER_NAMES = ("left_back", "right_back", "left_front", "right_front")


def get_current_pose(device):
    x, y, z, r, j1, j2, j3, j4 = device.pose()
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


def format_corner_map(corners):
    return {
        name: [round(point[0], 3), round(point[1], 3)]
        for name, point in corners.items()
    }


def collect_corners(label, port):
    print(f"\n[{label}] port={port}")
    device = Dobot(port=port, verbose=True)
    corners = {}

    try:
        print(f"{label} を手で合わせてから Enter を押してください。")
        for name in CORNER_NAMES:
            input(f"{label} の {name} を合わせたら Enter を押してください: ")
            pose = get_current_pose(device)
            corners[name] = (pose["x"], pose["y"])
            print(f"{label} {name}: x={pose['x']:.3f}, y={pose['y']:.3f}, z={pose['z']:.3f}")
    finally:
        device.close()

    return corners


def main():
    output_path_text = input(
        f"保存先ファイルを入力してください [{DEFAULT_OUTPUT_PATH}]: "
    ).strip()
    output_path = Path(output_path_text) if output_path_text else DEFAULT_OUTPUT_PATH

    result = {}

    for label in ("A", "B"):
        default_port = DEFAULT_PORTS[label]
        port = input(f"{label} の port を入力してください [{default_port}]: ").strip() or default_port
        corners = collect_corners(label, port)
        result[label] = {
            "port": port,
            "corners": format_corner_map(corners),
        }

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n保存しました: {output_path.resolve()}")
    print("main.py から読む JSON の形:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
