from pydobot import Dobot
import math
import time


MOVE_RETRY_DELAY_SEC = 0.2
DEFAULT_DRAW_R = 45.0


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


def lerp(a, b, t):
	return a + (b - a) * t


def bilinear(corners, u, v):
	left_back = corners["left_back"]
	right_back = corners["right_back"]
	left_front = corners["left_front"]
	right_front = corners["right_front"]

	top = (lerp(left_back[0], right_back[0], u), lerp(left_back[1], right_back[1], u))
	bottom = (lerp(left_front[0], right_front[0], u), lerp(left_front[1], right_front[1], u))
	return lerp(top[0], bottom[0], v), lerp(top[1], bottom[1], v)


def move_xy(device, x, y, z, r):
	attempt = 0
	while True:
		try:
			device.move_to(x, y, z, r, wait=True)
			return
		except AttributeError:
			# pydobot 側で応答が欠けると NoneType 参照で落ちることがあるため再試行。
			attempt += 1
			print(f"move_to 再試行 {attempt} 回目...")
			time.sleep(MOVE_RETRY_DELAY_SEC)
		except OSError:
			attempt += 1
			print(f"move_to 再試行 {attempt} 回目...")
			time.sleep(MOVE_RETRY_DELAY_SEC)


def draw_line(device, p1, p2, travel_z, write_z, r):
	move_xy(device, p1[0], p1[1], travel_z, r)
	move_xy(device, p1[0], p1[1], write_z, r)
	move_xy(device, p2[0], p2[1], write_z, r)
	move_xy(device, p2[0], p2[1], travel_z, r)


def draw_board_frame(device, corners, travel_z, write_z, r):
	left_back = corners["left_back"]
	right_back = corners["right_back"]
	left_front = corners["left_front"]
	right_front = corners["right_front"]

	# 外枠
	draw_line(device, left_back, right_back, travel_z, write_z, r)
	draw_line(device, right_back, right_front, travel_z, write_z, r)
	draw_line(device, right_front, left_front, travel_z, write_z, r)
	draw_line(device, left_front, left_back, travel_z, write_z, r)

	# 縦線 (u=1/3, 2/3)
	for u in (1.0 / 3.0, 2.0 / 3.0):
		p_top = bilinear(corners, u, 0.0)
		p_bottom = bilinear(corners, u, 1.0)
		draw_line(device, p_top, p_bottom, travel_z, write_z, r)

	# 横線 (v=1/3, 2/3)
	for v in (1.0 / 3.0, 2.0 / 3.0):
		p_left = bilinear(corners, 0.0, v)
		p_right = bilinear(corners, 1.0, v)
		draw_line(device, p_left, p_right, travel_z, write_z, r)


def get_cell_center(corners, cell):
	idx = cell - 1
	row = idx // 3
	col = 2 - (idx % 3)
	u = (col + 0.5) / 3.0
	v = (row + 0.5) / 3.0
	return bilinear(corners, u, v)


def draw_x(device, corners, cell, travel_z, write_z, r):
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

	draw_line(device, p1, p2, travel_z, write_z, r)
	draw_line(device, p3, p4, travel_z, write_z, r)


def draw_o(device, corners, cell, travel_z, write_z, r):
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
		angle = 2.0 * 3.1415926535 * t
		x = center[0] + radius * math.cos(angle)
		y = center[1] + radius * math.sin(angle)
		points.append((x, y))

	move_xy(device, points[0][0], points[0][1], travel_z, r)
	move_xy(device, points[0][0], points[0][1], write_z, r)
	for p in points[1:]:
		move_xy(device, p[0], p[1], write_z, r)
	move_xy(device, points[0][0], points[0][1], travel_z, r)


def print_board(board):
	for r in range(3):
		row = []
		for c in range(3):
			v = board[r][c]
			row.append(v if v else str(r * 3 + c + 1))
		print(" " + " | ".join(row))
		if r < 2:
			print("---+---+---")


def check_winner(board):
	lines = []
	lines.extend(board)
	lines.extend([[board[0][c], board[1][c], board[2][c]] for c in range(3)])
	lines.append([board[0][0], board[1][1], board[2][2]])
	lines.append([board[0][2], board[1][1], board[2][0]])

	for line in lines:
		if line[0] and line[0] == line[1] == line[2]:
			return line[0]
	return None


def is_full(board):
	return all(board[r][c] for r in range(3) for c in range(3))


def ask_cell(board, player):
	while True:
		raw = input(f"{player} の手番です。置くマスを 1-9 で入力: ").strip()
		if not raw.isdigit():
			print("数字を入力してください。")
			continue
		cell = int(raw)
		if cell < 1 or cell > 9:
			print("1-9 の範囲で入力してください。")
			continue
		row = (cell - 1) // 3
		col = (cell - 1) % 3
		if board[row][col]:
			print("そのマスは埋まっています。")
			continue
		return cell


def main():
	# ポート名は環境に合わせて変更してください
	# Windows: 'COM3', 'COM4' など
	# Linux/Mac: '/dev/ttyUSB0' など
	port = '/dev/ttyUSB0'
	device = Dobot(port=port, verbose=True)
	time.sleep(2)

	# 既存計測値をベースに盤面四隅を設定
	corners = {
            "left_back": (245.66, 62.10),
            "right_back": (282.00, 0.00),
            "left_front": (302.85, 69.19),
            "right_front": (308.89, 11.43),
	}

	try:
		pose = get_current_pose(device)
		base_z = pose["z"]
		write_z = base_z - 5.0
		travel_z = base_z + 5.0
		draw_r = DEFAULT_DRAW_R
		print(f"開始高さ Z={base_z:.2f} を基準に、書く時 -5mm / 移動時 +5mm にします。")
		print(f"移動高さ Z={travel_z:.2f}, 書く高さ Z={write_z:.2f}, R={draw_r:.2f} で描画します。")

		print("起動時の高さへ上げます...")
		move_xy(device, pose["x"], pose["y"], travel_z, draw_r)

		print("枠を描画します...")
		draw_board_frame(device, corners, travel_z, write_z, draw_r)

		board = [["" for _ in range(3)] for _ in range(3)]
		current = "X"

		while True:
			print("\n現在の盤面:")
			print_board(board)

			cell = ask_cell(board, current)
			row = (cell - 1) // 3
			col = (cell - 1) % 3
			board[row][col] = current

			if current == "X":
				draw_x(device, corners, cell, travel_z, write_z, draw_r)
			else:
				draw_o(device, corners, cell, travel_z, write_z, draw_r)

			winner = check_winner(board)
			if winner:
				print("\n最終盤面:")
				print_board(board)
				print(f"{winner} の勝ちです。")
				break

			if is_full(board):
				print("\n最終盤面:")
				print_board(board)
				print("引き分けです。")
				break

			current = "O" if current == "X" else "X"

	except RuntimeError as e:
		print(f"描画を中断しました: {e}")

	finally:
		device.close()


if __name__ == "__main__":
	main()