from robot_controller import RobotController
from tic_tac_toe import TicTacToeGame


class DualDobotMatch:
    def __init__(self, robot_a: RobotController, robot_b: RobotController):
        self.robot_a = robot_a
        self.robot_b = robot_b
        self.game = TicTacToeGame()

    def run(self) -> None:
        self.robot_a.connect()
        self.robot_b.connect()
        try:
            self._draw_initial_board()
            self._run_game_loop()
        finally:
            self.robot_a.close()
            self.robot_b.close()

    def _draw_initial_board(self) -> None:
        while True:
            try:
                # A が盤面を描く間、B は退避点で待機する。
                self.robot_b.retreat()
                print("盤面をA側で描画します...")
                self.robot_a.draw_board_frame()
                self.robot_a.retreat()
                return
            except Exception as exc:
                print(f"盤面描画に失敗しました。退避して再試行します。 ({type(exc).__name__})")
                self._recover_robots()

    def _run_game_loop(self) -> None:
        while True:
            print("\n現在の盤面:")
            self.game.print_board()

            cell = self.game.ask_cell()

            active, inactive = self._select_robots(self.game.current)

            draw_succeeded = False
            try:
                # 非描画機を先に退避させ、盤面への進入を1台に制限する。
                inactive.retreat()
                active.draw_mark(self.game.current, cell)

                # 描画後は両機体を待避点に戻す。
                inactive.retreat()
                active.retreat()
                draw_succeeded = True
            except Exception as exc:
                print(
                    f"描画に失敗しました。{self.game.current}{cell} はスキップして次に進みます。 ({type(exc).__name__})"
                )
                self._recover_robots()

            if draw_succeeded:
                self.game.apply_move(cell)

                winner = self.game.check_winner()
                if winner:
                    print("\n最終盤面:")
                    self.game.print_board()
                    print(f"{winner} の勝ちです。")
                    return

                if self.game.is_full():
                    print("\n最終盤面:")
                    self.game.print_board()
                    print("引き分けです。")
                    return

                self.game.switch_turn()

    def _select_robots(self, mark: str):
        if mark == "X":
            return self.robot_a, self.robot_b
        return self.robot_b, self.robot_a

    def _recover_robots(self) -> None:
        for robot in (self.robot_a, self.robot_b):
            try:
                robot.retreat()
            except Exception as exc:
                print(f"{robot.config.name} の退避に失敗しました。 ({type(exc).__name__})")
