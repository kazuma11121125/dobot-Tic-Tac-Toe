class TicTacToeGame:
    def __init__(self):
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.current = "X"

    def print_board(self):
        for r in range(3):
            row = []
            for c in range(3):
                v = self.board[r][c]
                row.append(v if v else str(r * 3 + c + 1))
            print(" " + " | ".join(row))
            if r < 2:
                print("---+---+---")

    def ask_cell(self) -> int:
        while True:
            raw = input(f"{self.current} の手番です。置くマスを 1-9 で入力: ").strip()
            if not raw.isdigit():
                print("数字を入力してください。")
                continue
            cell = int(raw)
            if cell < 1 or cell > 9:
                print("1-9 の範囲で入力してください。")
                continue
            row = (cell - 1) // 3
            col = (cell - 1) % 3
            if self.board[row][col]:
                print("そのマスは埋まっています。")
                continue
            return cell

    def apply_move(self, cell: int) -> None:
        row = (cell - 1) // 3
        col = (cell - 1) % 3
        self.board[row][col] = self.current

    def check_winner(self):
        lines = []
        lines.extend(self.board)
        lines.extend([[self.board[0][c], self.board[1][c], self.board[2][c]] for c in range(3)])
        lines.append([self.board[0][0], self.board[1][1], self.board[2][2]])
        lines.append([self.board[0][2], self.board[1][1], self.board[2][0]])

        for line in lines:
            if line[0] and line[0] == line[1] == line[2]:
                return line[0]
        return None

    def is_full(self) -> bool:
        return all(self.board[r][c] for r in range(3) for c in range(3))

    def switch_turn(self) -> None:
        self.current = "O" if self.current == "X" else "X"
