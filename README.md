# Dual Dobot Tic-Tac-Toe

2台のDobotで三目並べを行うサンプルです。

この実装は次の方針です。
- A側が盤面(外枠と格子)を描画
- AはX、BはOを担当
- 描画していない側は待避点に退避
- 1ターンで盤面に進入するのは1台のみ

## 必要環境

- Python 3.9+
- pydobot
- Dobot 2台
- Linuxの場合、シリアルデバイスへのアクセス権限

インストール例:

```bash
pip install pydobot
```

## ファイル構成

- main.py
  - 起動エントリポイント
  - JSON から RobotConfig を読み込み、対戦実行を開始
- robot_types.py
  - 設定データ型(RobotConfig)と定数
- geometry.py
  - 座標補間(lerp, bilinear)
- robot_controller.py
  - 1台分の接続、移動、退避、描画を担当するRobotController
- tic_tac_toe.py
  - 盤面状態、入力、勝敗判定を担当するTicTacToeGame
- match_coordinator.py
  - 2台の進行制御を行うDualDobotMatch
- get_map.py
  - 手で合わせた位置を Enter で4点記録して JSON に保存する校正ツール

## 実行方法

1. main.py の設定を実機に合わせる
  - 迷う場合は先に `python3 get_map.py` で2台分の4隅を保存する
2. 実行

```bash
python main.py
```

## 設定項目の意味

main.py 内のRobotConfigには次を設定します。

- name
  - ロボット識別名(A/B)
- mark
  - 担当記号(X/O)
- port
  - シリアルポート(例: /dev/ttyUSB0)
- corners
  - 盤面4隅の座標
  - left_back, right_back, left_front, right_front
  - `python3 get_map.py` で記録した JSON をそのまま使える
- draw_r
  - エンドエフェクタ姿勢R
- travel_offset_mm
  - 起動時Zからの移動高さオフセット
- write_offset_mm
  - 起動時Zからの描画高さオフセット

## 座標合わせ(2台の座標系統合)

同じ盤面を使う場合は、A/Bそれぞれで同じ4点を計測して設定します。

手順:
1. 盤面の4隅を物理的に決める
2. Aで4隅を記録してcornersに設定
3. Bでも同じ4隅を記録してcornersに設定
4. 複数マス中心をA/Bで順に指示し、ズレを確認
5. ズレが大きい点を再計測

注意:
- AとBで同じ値になる必要はありません
- 重要なのは、同じ物理位置に対して各機体のcornersが正しく対応することです

起動時の退避位置は、接続直後に取得した現在位置をそのまま使います。

## 座標4点の保存

`get_map.py` は、A/B の2台それぞれについて、ロボットを目視で4隅に合わせて Enter を押すたびに、その時点の座標を保存します。

```bash
python3 get_map.py
```

保存先は既定で `calibrated_corners.json` です。`main.py` はこの JSON を読み込んで使います。

## 安全運用ルール

- 描画前に非描画機を退避
- 描画後に描画機を退避
- 例外時もclose時に退避を試行
- move失敗時は再試行し、上限超過でRuntimeError

## トラブルシュート

- 接続できない
  - portが正しいか確認
  - 他プロセスがポートを掴んでいないか確認
- 動きがずれる
  - cornersを再計測
- 高さが合わない
  - travel_offset_mm, write_offset_mmを調整