# 🚀 Space Rocket Altitude & Fuel Efficiency Score Simulator

**Python + Tkinter + Matplotlib** で開発した、ロケットの上昇運動を数値シミュレーションするデスクトップアプリケーションです。

ロケットの乾燥質量・推進剤質量・エンジン推力などを変更し、複数の推進剤プリセットについて、

* 最高到達高度
* 物理評価スコア
* 推進剤消費
* 速度
* 飛行時間

などを計算・比較できます。

数値積分には **4次 Runge-Kutta 法（RK4）** を使用しており、さらにオプションとして簡易的な大気抵抗モデルを有効化できます。

> **注意:**
> 本ソフトウェアは教育・プログラミング学習・数値実験を目的とした簡略化されたシミュレータです。
> 実際のロケット、エンジン、推進剤、航空宇宙機器の設計・製造・運用・性能保証には使用しないでください。

---

# 📌 Features

## 🚀 Rocket Simulation

ロケットの上昇運動を数値計算します。

GUIから以下の主要パラメータを変更できます。

* 乾燥質量
* 推進剤総質量
* エンジン推力
* O/F比

乾燥質量・推進剤質量・推力はスライダーだけでなく、数値をクリックして直接入力することもできます。

---

## 📐 RK4 Numerical Integration

シミュレーションエンジンには **4次 Runge-Kutta 法（RK4）** を使用しています。

主な状態変数は、

```text
高度
速度
```

です。

各ステップで、

```text
k1
k2
k3
k4
```

を計算し、それらを使用して次の状態を求めます。

また、推進剤消費による質量変化も計算に反映されます。

---

## 🌍 Vacuum / Atmosphere Simulation

飛行環境を切り替えることができます。

### Vacuum Model

大気抵抗を考慮せず、高度による重力変化を考慮します。

### Atmosphere Model

オプションを有効にすると、簡易的な大気モデルが使用されます。

現在の実装では、

```text
rho(h) = rho0 × exp(-h / H)
```

によって大気密度を近似しています。

空気抵抗は、

```text
D = 1/2 × rho × v² × Cd × A
```

として計算されます。

現在の簡易モデルでは、

```text
rho0 = 1.225 kg/m³
H    = 8500 m
Cd   = 0.5
A    = π × 0.5² m²
```

が使用されています。

> この大気モデルは実際の標準大気を完全に再現するものではありません。

---

## 🌎 Altitude-Dependent Gravity

高度による重力加速度の変化を考慮しています。

使用しているモデルは、

$$
g(h)=g_0
\left(
\frac{R}{R+h}
\right)^2
$$

です。

ここで、

* `g(h)` = 高度 `h` における重力加速度
* `g0` = 標準重力加速度
* `R` = 地球半径
* `h` = 高度

です。

現在のデフォルト設定では、

```text
g0 = 9.80665 m/s²
R  = 6371000 m
```

となっています。

---

# ⚗️ Propellant Presets

推進剤の情報はPythonコードではなく、`config.json` で管理されています。

現在の設定ファイルには以下の4種類が登録されています。

| ID            | Propellant |   Isp | O/F | State |
| ------------- | ---------- | ----: | --: | ----- |
| `methalox`    | メタン＋液体酸素   | 380 s | 3.5 | 液体    |
| `hydrolox`    | 水素＋液体酸素    | 450 s | 6.0 | 液体    |
| `ethanol_air` | エタノール＋空気   | 250 s | 9.0 | 液体    |
| `kerolox`     | ケロシン＋液体酸素  | 310 s | 2.5 | 液体    |

例えば `Methalox` は、

```json
{
  "name": "メタン＋液体酸素 (Methalox)",
  "Isp_s": 380.0,
  "isp_sec": 380.0,
  "of_ratio": 3.5,
  "mixture_ratio_o_f": 3.5,
  "burn_time_s": 100.0,
  "mass_flow_rate_kg_s": 100.0,
  "state_type": "液体"
}
```

という形式で登録されています。

---

# ⚗️ O/F Ratio

O/F比は、

$$
O/F=\frac{m_{ox}}{m_f}
$$

として扱います。

ここで、

* `m_ox` = 酸化剤質量
* `m_f` = 燃料質量

です。

推進剤総質量を `m_prop` とすると、

$$
m_f=
\frac{m_{prop}}{1+O/F}
$$

$$
m_{ox}=m_f(O/F)
$$

によって燃料と酸化剤の質量を計算します。

GUI上ではO/F比をリアルタイムに変更でき、それに応じて、

```text
燃料: xxx kg
酸化剤: xxx kg
```

という表示も更新されます。

---

# 🔥 Propellant Mass Flow

現在のシミュレーションでは、比推力から実効排気速度を求め、

$$
c=I_{sp}g_0
$$

さらに推力から質量流量を、

$$
\dot m=
\frac{F}{I_{sp}g_0}
$$

として求めています。

シミュレーション中は燃料と酸化剤の消費量をそれぞれ計算し、どちらかがなくなると推力を停止します。

---

# 🧮 Rocket Acceleration

基本的な加速度は、

$$
a=
\frac{F-D}{m}-g
$$

として計算されます。

ここで、

* `F` = エンジン推力
* `D` = 空気抵抗
* `m` = ロケット質量
* `g` = 高度による重力加速度

です。

大気モデルを無効にした場合は、

```text
D = 0
```

として計算されます。

---

# 🏆 Physical Evaluation Score

シミュレーション結果を比較するため、独自の評価スコアを使用しています。

現在の実装では、

$$
Score=
(g_0h_{max})
\left(
1+\frac{I_{sp}}{500}
\right)
$$

を使用しています。

ここで、

* `h_max` = 最高高度 [km]
* `g0` = 標準重力加速度
* `Isp` = 比推力 [s]

です。

> **重要:**
> このスコアは一般的なロケット工学で使用される標準的な性能指標ではありません。
> このプロジェクト内で複数のシミュレーション結果を比較するために定義した独自の指標です。

したがって、スコアの値を実際のロケット性能や「燃費」と直接対応させることはできません。

---

# 🖥️ GUI

GUIには **Tkinter** を使用しています。

メイン画面は、

```text
┌──────────────────────┬────────────────────────────┐
│                      │                            │
│   Simulation          │      Matplotlib            │
│   Parameters          │                            │
│                      │      Altitude Graph        │
│   Rocket Mass         │                            │
│   Propellant Mass     │      Propellant Graph     │
│   Engine Thrust       │                            │
│   O/F Ratio           │                            │
│                      │                            │
│   Environment         │                            │
│   Settings            │                            │
│                      │                            │
│   Export              │                            │
│                      │                            │
└──────────────────────┴────────────────────────────┘
```

のような構成になっています。

---

# 🎛️ GUI Controls

## Rocket Parameters

以下のパラメータを変更できます。

### Dry Mass

ロケットの乾燥質量です。

```text
Dry Mass [kg]
```

スライダーまたは直接入力で変更できます。

---

### Total Propellant Mass

ロケットに搭載する推進剤総質量です。

```text
Total Propellant Mass [kg]
```

---

### Engine Thrust

エンジン推力です。

```text
Engine Thrust [N]
```

---

## O/F Ratio

O/F比をスライダーまたは直接入力で変更できます。

設定を変更すると、燃料と酸化剤の質量がリアルタイムで再計算されます。

---

# 🌍 Environment Settings

以下のオプションを使用できます。

```text
☐ 地球大気圏影響
  空気抵抗・Isp高度変化を考慮
```

OFFの場合：

```text
真空モデル
```

ONの場合：

```text
大気圏モデル
```

としてシミュレーションされます。

---

# 📊 Graph Display

シミュレーション結果はMatplotlibを使用してグラフ表示されます。

## Altitude Graph

時間に対する高度の変化を表示します。

```text
X軸: 時間
Y軸: 高度 (km)
```

複数の推進剤を同時に表示して比較できます。

---

## Propellant Graph

時間経過による残り推進剤量を表示します。

```text
X軸: 時間
Y軸: 残り推進剤 (kg)
```

---

# 🔎 Plot Filtering

グラフに表示する対象を絞り込むことができます。

## Display Mode

```text
全件表示
上位のみ表示
```

「上位のみ表示」を選択すると、最高高度を基準にランキングされた上位N件だけを表示します。

---

## Propellant Type Filter

推進剤の状態種別によるフィルタリングにも対応しています。

```text
all
液体
固体
ハイブリッド
気体
```

現在の `config.json` に登録されている4種類はすべて「液体」に分類されています。

---

# ⏱️ Time Axis

グラフの時間軸は、

```text
秒
分
```

から選択できます。

内部のシミュレーション時間は秒単位で計算されます。

---

# 🧵 Background Simulation

計算負荷の高いシミュレーションは、GUIとは別のバックグラウンドスレッドで実行されます。

これにより、シミュレーション中でもGUIが完全に停止することを避けています。

処理中は、

```text
⏳ バックグラウンド物理演算中...
```

などの状態が表示されます。

---

# 📈 Simulation Results

計算終了後、推進剤ごとに以下の情報が表示されます。

```text
最高高度
評価スコア
残燃料
残酸化剤
Isp
O/F
```

最高高度を基準として順位付けされます。

---

# 💾 CSV Export

シミュレーション結果はCSVとして保存できます。

出力される主な項目は、

| Column        | Description | Unit |
| ------------- | ----------- | ---- |
| `推進剤名称`       | 推進剤名        | -    |
| `経過時間(s)`     | 経過時間        | s    |
| `高度(m)`       | 高度          | m    |
| `高度(km)`      | 高度          | km   |
| `速度(m/s)`     | 速度          | m/s  |
| `残り推進剤質量(kg)` | 残り推進剤       | kg   |

です。

CSVはUTF-8 BOM付きで保存されるため、Windows環境のExcelなどでも日本語を扱いやすい形式になっています。

---

# 🖼️ High Resolution Graph Export

GUIからグラフをPNGとして保存できます。

### Altitude Graph

```text
rocket_altitude_4k.png
```

### Propellant Graph

```text
rocket_propellant_4k.png
```

### Full Graph

```text
rocket_full_graph_4k.png
```

画像保存時には、

```text
DPI = 300
```

が指定されています。

> ファイル名には `4k` が含まれていますが、これはファイル名上の名称です。
> 実際の画像解像度はグラフサイズと保存時のDPIによって決まります。

---

# 📝 Logging

アプリケーションの動作は `log.txt` に記録されます。

ログには、

* アプリケーション起動
* `config.json` 読み込み
* シミュレーション開始
* CSV保存
* グラフ保存
* エラー

などが記録されます。

現在のログでも、アプリケーション起動後に設定ファイルを読み込み、その後複数回シミュレーションを実行していることを確認できます。

ログ形式は、

```text
[Info] 2026/08/18 08:58:20 : "ロケットシミュレータ アプリケーション起動"
[Info] 2026/08/18 08:58:20 : "『config.json』の読み込みに成功しました"
[Info] 2026/08/18 08:59:19 : "--- ロケット物理シミュレーション計算開始 ---"
```

のようになっています。

---

# ⚙️ Configuration

設定は `config.json` にまとめられています。

現在の基本設定は以下です。

```json
{
  "rocket_common_specs": {
    "dry_mass_kg": 1000.0,
    "total_propellant_mass_kg": 10000.0,
    "engine_thrust_N": 100000.0
  },

  "simulation_settings": {
    "dt": 0.01,
    "g0": 9.80665,
    "earth_radius_m": 6371000.0
  }
}
```

---

## Rocket Parameters

| Parameter                  | Description | Unit |
| -------------------------- | ----------- | ---- |
| `dry_mass_kg`              | 乾燥質量        | kg   |
| `total_propellant_mass_kg` | 推進剤総質量      | kg   |
| `engine_thrust_N`          | エンジン推力      | N    |

現在のデフォルト値は、

```text
Dry Mass       = 1000 kg
Propellant     = 10000 kg
Engine Thrust  = 100000 N
```

です。

---

## Simulation Settings

| Parameter        | Description | Unit |
| ---------------- | ----------- | ---- |
| `dt`             | 基本時間刻み      | s    |
| `g0`             | 標準重力加速度     | m/s² |
| `earth_radius_m` | 地球半径        | m    |

現在は、

```text
dt            = 0.01 s
g0            = 9.80665 m/s²
Earth Radius  = 6371000 m
```

が設定されています。

---

# ➕ Adding a New Propellant

新しい推進剤を追加する場合は、`config.json` の `propellant_presets` に項目を追加します。

例えば、

```json
"example_propellant": {
  "name": "Example Propellant",
  "Isp_s": 300.0,
  "isp_sec": 300.0,
  "of_ratio": 2.5,
  "mixture_ratio_o_f": 2.5,
  "burn_time_s": 100.0,
  "mass_flow_rate_kg_s": 100.0,
  "state_type": "液体"
}
```

のように追加できます。

基本的にはPythonコード側に推進剤ごとの専用処理を追加する必要はなく、設定ファイルからプリセットを読み込む構成になっています。

---

# 📁 Project Structure

推奨されるリポジトリ構成は以下です。

```text
rocket-sim/
│
├── rocket_sim.py
├── config.json
├── README.md
├── LICENSE
├── .gitignore
│
└── log.txt
```

主要な役割は以下の通りです。

| File            | Role                          |
| --------------- | ----------------------------- |
| `rocket_sim.py` | GUI・物理計算・グラフ・CSV出力などのメインプログラム |
| `config.json`   | ロケット設定・シミュレーション設定・推進剤プリセット    |
| `log.txt`       | アプリケーションログ                    |
| `README.md`     | プロジェクト説明                      |
| `LICENSE`       | ライセンス                         |

---

# 🛠️ Requirements

## Python

**Python 3.8以上を推奨**

---

## External Packages

Matplotlibを使用しています。

```bash
pip install matplotlib
```

---

## Standard Libraries

以下はPython標準ライブラリです。

```text
csv
ctypes
datetime
json
math
os
threading
time
tkinter
```

Matplotlibのみ外部パッケージとして必要です。

---

# 🚀 Quick Start

## 1. Clone Repository

GitHubからリポジトリを取得します。

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>
```

---

## 2. Install Dependencies

```bash
pip install matplotlib
```

---

## 3. Check Configuration

以下のファイルが同じディレクトリにあることを確認してください。

```text
rocket_sim.py
config.json
```

`rocket_sim.py` は自身と同じディレクトリにある `config.json` を読み込みます。

---

## 4. Run

```bash
python rocket_sim.py
```

---

# 🖥️ Screenshot

スクリーンショットを追加する場合は、例えば以下の構成にできます。

```text
assets/
└── screenshot.png
```

READMEでは、

```markdown
![Rocket Simulator Screenshot](assets/screenshot.png)
```

として表示できます。

---

# 📐 Mathematical Model

## 1. Effective Exhaust Velocity

比推力から実効排気速度を計算します。

$$
c=I_{sp}g_0
$$

---

## 2. Mass Flow Rate

推力と実効排気速度から、

$$
\dot{m}=
\frac{F}{c}
$$

として質量流量を計算します。

---

## 3. Gravity

高度に応じて、

$$
g(h)=
g_0
\left(
\frac{R}{R+h}
\right)^2
$$

とします。

---

## 4. Drag

大気モデルが有効な場合、

$$
D=
\frac{1}{2}
\rho v^2 C_d A
$$

によって空気抵抗を計算します。

大気密度は簡易的に、

$$
\rho(h)=
\rho_0e^{-h/H}
$$

として近似します。

---

## 5. Acceleration

最終的な加速度は、

$$
a=
\frac{F-D}{m}-g
$$

として計算されます。

---

## 6. RK4

ロケットの高度と速度について、4次Runge-Kutta法を使用します。

概念的には、

```text
k1
 ↓
k2
 ↓
k3
 ↓
k4
 ↓
次の状態
```

という流れで計算します。

現在の基本時間刻みは、

```text
dt = 0.01 s
```

です。

---

# 🛑 Simulation Termination

シミュレーションには最大ステップ数が設定されています。

現在の実装では、

```text
max_steps = 300000
```

です。

また、推進剤がなくなって推力が停止した後、

* 速度が十分小さくなった
* 高度が低下した
* 高度変化がほぼ停止した

などの条件からシミュレーションを終了します。

これにより、最高高度付近で無限に計算し続けることを防いでいます。

---

# ⚠️ Model Limitations

このシミュレータは、実際のロケットを完全に再現する物理シミュレータではありません。

特に以下の要素は簡略化されています。

* 実際の大気構造
* 正確な大気密度
* 実際の抗力係数
* ロケット形状による空力特性
* 地球の自転
* 地球以外の天体による重力
* ピッチ・ヨー・ロール
* 姿勢制御
* 多段ロケット
* 実際のエンジン推力曲線
* 燃焼室圧力
* ノズル膨張比
* ターボポンプなどのエンジン内部状態
* 燃料温度・圧力
* タンク構造
* 構造重量の変化
* 空力加熱
* 実際の燃焼化学
* 制御系
* 着陸・再使用システム

そのため、得られた結果は、

> **このシミュレータの数値モデルにおける比較結果**

として扱ってください。

---

# 🔬 Example Use Cases

このプロジェクトは以下のような学習・実験に利用できます。

* ロケット方程式の学習
* RK4の学習
* 数値積分の実験
* PythonによるGUI開発
* Tkinterの学習
* Matplotlibによる可視化
* JSONによる設定管理
* CSVデータ出力
* パラメータ比較
* O/F比の変化による影響の観察
* 大気抵抗の有無による結果比較
* 新しい推進剤プリセットの追加
* 数値シミュレーションの高速化・改善

---

# 🔧 Technical Overview

このプロジェクトは、主に以下の技術を組み合わせています。

```text
Python
 ├── Tkinter
 │    └── GUI
 │
 ├── Matplotlib
 │    └── グラフ表示・画像出力
 │
 ├── JSON
 │    └── シミュレーション設定
 │
 ├── CSV
 │    └── 数値データ出力
 │
 ├── Threading
 │    └── バックグラウンド計算
 │
 └── RK4
      └── 数値積分
```

---

# 📊 Current Default Configuration

現在の設定ファイルでは、ロケット共通パラメータとして、

```text
乾燥質量       1000 kg
推進剤総質量   10000 kg
エンジン推力   100000 N
```

が設定されています。

また、シミュレーション設定は、

```text
dt             0.01 s
g0             9.80665 m/s²
地球半径       6371000 m
```

です。

推進剤プリセットとして、

```text
Methalox
Hydrolox
Ethanol/Air
Kerolox
```

が登録されています。

---

# 📜 License

This project is licensed under the **MIT License**.

詳細は [`LICENSE`](LICENSE) を参照してください。

---

# 👤 Author

**OLT_game**

GitHub:

```text
https://github.com/OLT_game
```

---

# ⭐ Contributing

バグ報告、改善案、新しい物理モデル、GUI改善などのIssueやPull Requestを歓迎します。

特に以下のような改善を想定しています。

* より正確な大気モデル
* より高度な空気抵抗モデル
* 多段ロケット対応
* 可変推力エンジン
* より柔軟な推進剤データベース
* より高度なエンジンモデル
* CSV / JSONによる詳細な結果出力
* シミュレーション結果の再読み込み
* グラフ機能の拡張
* テストコードの追加
* 計算速度の改善
* GUIの改善

---

# ⚠️ Disclaimer

本ソフトウェアは、教育・研究・プログラミング学習・数値実験を目的とした簡略化モデルです。

計算結果は実際のロケットやエンジンの性能を保証するものではありません。

本ソフトウェアを、

* 実際のロケット設計
* エンジン設計
* 推進剤設計
* 打上げ計画
* 航空宇宙機器の設計・製造・運用
* 安全性評価

などの用途に使用しないでください。

本プロジェクトの計算結果は、あくまで**数値モデル上のシミュレーション結果**として利用してください。
