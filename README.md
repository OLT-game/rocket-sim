# 🚀 Space Rocket Altitude & Fuel Efficiency Score Simulator v2.03

真空中のロケット上昇運動を数値計算し、**推進剤プリセットごとの最高高度・評価スコア・推進剤消費量**を比較する Python 製シミュレータです。

Tkinter による GUI と Matplotlib によるグラフ表示を備えており、ロケットの乾燥質量・推進剤質量・推力・O/F 比などを変更しながらシミュレーションできます。

> **注意:** このソフトウェアは教育・研究・数値実験を目的とした簡略化モデルです。実際のロケット設計、性能保証、打上げ計画などには使用しないでください。

---

## 📌 Features

- **真空中のロケット上昇シミュレーション**
  - 高度による地球重力の変化を考慮
  - 推進剤消費によるロケット質量の変化を考慮
  - 推力・乾燥質量・推進剤質量を GUI から変更可能

- **RK4（4次 Runge-Kutta 法）による数値積分**
  - 現在の実装では単純な Euler 法ではなく RK4 を使用
  - 小さな時間刻みで高度・速度を逐次計算

- **推進剤プリセット比較**
  - `config.json` に登録された複数の推進剤を一括シミュレーション
  - Isp、O/F 比、質量流量などをプリセットとして管理

- **O/F 比のリアルタイム変更**
  - GUI のスライダーから O/F 比を変更
  - 燃料質量と酸化剤質量をリアルタイム表示

- **グラフ表示**
  - 高度 - 時間
  - 残り推進剤 - 時間
  - 複数の推進剤を同時比較

- **表示対象の絞り込み**
  - 全件表示
  - 上位 N 件のみ表示
  - 推進剤の状態種別によるフィルタリング

- **高解像度 PNG 保存**
  - 高度グラフ
  - 推進剤グラフ
  - 全体グラフ
  - PNG を 300 DPI で保存

- **ログ機能**
  - 起動・計算・グラフ保存・エラーなどを `log.txt` に記録

---

## 🖥️ Screenshot

スクリーンショットを追加する場合は、例えば次のように配置できます。

```text
assets/
└── screenshot.png
```

README からは以下のように表示できます。

```markdown
![Simulator Screenshot](assets/screenshot.png)
```

---

## 🛠️ Requirements

### Python

- Python **3.8 以上**

### 使用ライブラリ

外部パッケージ:

```bash
pip install matplotlib
```

標準ライブラリ:

- `ctypes`
- `datetime`
- `json`
- `os`
- `time`
- `tkinter`

`tkinter` は Python の標準ライブラリですが、環境によっては別途 GUI コンポーネントの導入が必要です。

---

## 📁 Project Structure

推奨するリポジトリ構成:

```text
rocket-sim/
├── main.py
├── config.json
├── README.md
├── LICENSE
├── .gitignore
└── log.txt
```

現在のメインプログラムは GUI、シミュレーション、グラフ描画、ログ処理を `main.py` にまとめた構成です。

---

## 🚀 Quick Start

### 1. Clone

Windows
```bash
mkdir C:\rocket-project
cd C:\rocket-project

git clone --filter=blob:none --sparse <https://github.com/OLT-game/rocket-sim/tree/main>

cd <rocket-sim>

git sparse-checkout set rocket-sim
```

Linux / Mac

```bash
mkdir rocket-sim-sub && cd rocket-sim-sub
git init

git remote add origin https://github.com/OLT_game/rocket-sim.git

git config core.sparseCheckout true

echo "rocket-sim/*" >> .git/info/sparse-checkout

git pull origin main
```

### 2. Install dependencies

```bash
pip install matplotlib
```

### 3. Place configuration

`main.py` と同じディレクトリに `config.json` を配置します。

### 4. Run

```bash
python main.py
```

---

## ⚙️ Configuration

現在の `config.json` では、ロケット共通パラメータ、シミュレーション設定、推進剤プリセットを分離して管理しています。

### Rocket parameters

```json
{
  "rocket_common_specs": {
    "dry_mass_kg": 1000.0,
    "total_propellant_mass_kg": 10000.0,
    "engine_thrust_N": 100000.0
  }
}
```

| Parameter | Description | Unit |
|---|---|---|
| `dry_mass_kg` | 乾燥質量 | kg |
| `total_propellant_mass_kg` | 推進剤総質量 | kg |
| `engine_thrust_N` | エンジン推力 | N |

---

### Simulation settings

```json
{
  "simulation_settings": {
    "dt": 0.01,
    "g0": 9.80665,
    "earth_radius_m": 6371000.0
  }
}
```

| Parameter | Description | Unit |
|---|---|---|
| `dt` | 数値積分の時間刻み | s |
| `g0` | 標準重力加速度 | m/s² |
| `earth_radius_m` | 地球半径 | m |

現在の設定では `dt = 0.01` 秒です。

---

### Propellant presets

現在の設定ファイルには、以下のプリセットが登録されています。

```text
Methalox
Hydrolox
Ethanol/Air
Kerolox
```

例:

```json
{
  "methalox": {
    "name": "メタン＋液体酸素 (Methalox)",
    "Isp_s": 380.0,
    "of_ratio": 3.5,
    "burn_time_s": 100.0,
    "mass_flow_rate_kg_s": 100.0,
    "state_type": "液体"
  }
}
```

主な項目:

| Parameter | Description |
|---|---|
| `name` | 表示名 |
| `Isp_s` | 比推力 |
| `of_ratio` | O/F 比 |
| `burn_time_s` | プリセット上の燃焼時間 |
| `mass_flow_rate_kg_s` | 質量流量 |
| `state_type` | 推進剤の状態種別 |

---

## 🎮 GUI Controls

### Rocket parameters

左側のスライダーから以下を変更できます。

- 乾燥質量
- 推進剤総質量
- エンジン推力

### O/F ratio

O/F 比をスライダーで変更できます。

```text
O/F = 酸化剤質量 / 燃料質量
```

変更すると、現在の推進剤総質量から

```text
燃料質量
酸化剤質量
```

が再計算され、GUI に表示されます。

---

## 📊 Plot Controls

### Time axis

時間軸を以下から選択できます。

- 秒
- 分

### Display mode

```text
全件表示
上位のみ表示
```

「上位のみ表示」では、最高高度の順位を基準に指定した件数を表示します。

### Propellant filter

推進剤の状態種別によってフィルタリングできます。

```text
all
液体
固体
ハイブリッド
気体
```

---

# 📐 Mathematical Model

このシミュレータは、真空中の一次元的な鉛直上昇を簡略化してモデル化しています。

## 1. Exhaust velocity

比推力 `Isp` と標準重力加速度 `g0` から実効排気速度を求めます。

$$
c = I_{sp} g_0
$$

ここで、

- `c`: 実効排気速度 [m/s]
- `Isp`: 比推力 [s]
- `g0`: 標準重力加速度 [m/s²]

です。

---

## 2. Mass flow rate

質量流量が設定されていない場合、推力と実効排気速度から次式で計算します。

$$
\dot{m} = \frac{F}{c}
$$

つまり、

$$
\dot{m} =
\frac{F}{I_{sp}g_0}
$$

です。

ただし、`config.json` に `mass_flow_rate_kg_s` が設定されている場合は、その値が使用されます。

---

## 3. Fuel / Oxidizer mass

O/F 比を

$$
O/F = \frac{m_{ox}}{m_f}
$$

とすると、推進剤総質量 `m_prop` から燃料・酸化剤質量を

$$
m_f = \frac{m_{prop}}{1 + O/F}
$$

$$
m_{ox} = m_f(O/F)
$$

として求めます。

---

## 4. Gravity

高度 `h` における重力加速度は、地球半径を `R`、標準重力加速度を `g0` として、以下の式で近似しています。

$$
g(h) =
g_0
\left(
\frac{R}{R+h}
\right)^2
$$

実装ではこの高度依存重力を使用して加速度を計算しています。

---

## 5. Rocket acceleration

推力 `F`、ロケット質量 `m`、重力加速度 `g` から、

$$
a =
\frac{F}{m} - g
$$

として加速度を求めます。

---

## 6. RK4 numerical integration

現在のシミュレーションエンジンでは **4次 Runge-Kutta 法（RK4）** を使用しています。

状態変数は主に、

```text
高度
速度
```

です。

各タイムステップで、

```text
k1
k2
k3
k4
```

を計算し、それらを重み付けして次の状態を求めます。

実装上は、推進剤消費による質量変化も各 RK4 ステップの質量評価に反映しています。

---

## 7. Propellant depletion

燃料または酸化剤のどちらかがなくなった場合、エンジン推力を `0` とします。

その後、速度が十分小さくなる、または高度が低下することを利用して最高高度付近を検出し、シミュレーションを終了します。

また、異常な長時間計算を防ぐため最大ステップ数も設定されています。

---

# 🏆 Score

シミュレータには、最高高度と Isp を組み合わせた独自の評価スコアがあります。

現在の実装では、

$$
Score =
\left(
\frac{g_0 h_{max}}{1000}
\right)
\left(
1+\frac{I_{sp}}{500}
\right)
$$

を使用しています。

ここで、

- `h_max`: 最高高度 [m]
- `g0`: 標準重力加速度 [m/s²]
- `Isp`: 比推力 [s]

です。

**このスコアは物理学上の標準的な「燃費スコア」ではなく、このシミュレータ独自の比較指標です。**

そのため、実際のロケット性能や燃料効率を直接表す値ではありません。

---

# 📈 Output

シミュレーション完了後、以下の情報を比較できます。

```text
最高高度
評価スコア
Isp
O/F 比
```

また、グラフでは以下を確認できます。

### Altitude graph

```text
時間 → 高度
```

複数の推進剤について、時間経過による高度変化を比較します。

### Propellant graph

```text
時間 → 残り推進剤
```

燃焼中の推進剤総量の変化を比較します。

---

# 💾 Graph Export

GUI から以下の PNG を保存できます。

```text
rocket_altitude_4k.png
rocket_propellant_4k.png
rocket_full_graph_4k.png
```

保存時には 300 DPI が指定されます。

---

# 📝 Logging

アプリケーションの動作は `log.txt` に記録されます。

例えば、

```text
[Info] 2026/08/17 01:41:38 : "ロケットシミュレータ アプリケーション起動"
[Info] 2026/08/17 01:42:44 : "--- 真空ロケット物理シミュレーション計算開始 ---"
[Info] 2026/08/17 01:42:45 : "全計算およびグラフ表示が完了しました。"
```

のような形式で記録されます。

グラフ保存についてもログが残ります。

---

# ⚠️ Model Limitations

このシミュレータはロケットの実機性能を再現する完全な物理シミュレータではありません。

現在のモデルでは、主に以下を簡略化・省略しています。

- 大気抵抗
- 大気密度の高度変化
- 地球の自転
- 重力以外の天体の影響
- ピッチ・ヨー・ロール
- 多段ロケット
- エンジンの推力曲線
- ノズル膨張比
- 燃焼室圧力
- ターボポンプ等のエンジン内部状態
- 実際の燃料温度・圧力
- 構造重量の変化
- 空力加熱
- 制御系

したがって、結果は**数値モデル上での比較結果**として扱ってください。

---

# 🔬 Example Use Cases

このプロジェクトは、例えば以下のような用途に利用できます。

- ロケット方程式の学習
- 数値積分の学習
- RK4 法の動作確認
- Python GUI の練習
- Matplotlib によるデータ可視化
- パラメータ比較実験
- 推進剤モデルの追加実験
- O/F 比による結果の変化の観察

---

# ➕ Adding a New Propellant

`config.json` の `propellant_presets` に新しい項目を追加することで、比較対象を増やせます。

```json
"example_propellant": {
  "name": "Example Propellant",
  "Isp_s": 300.0,
  "of_ratio": 2.5,
  "burn_time_s": 100.0,
  "mass_flow_rate_kg_s": 100.0,
  "state_type": "液体"
}
```

プログラム側で個別の推進剤を追加する必要はなく、設定ファイルを変更して比較対象を増やせる構成になっています。

---

# 📜 License

This project is licensed under the **MIT License**.

詳細は [`LICENSE`](License) を参照してください。

---

# 👤 Author

**OLT_game**

GitHub:

```text
https://github.com/OLT_game
```

---

# ⭐ Contributing

バグ報告、改善案、新しい推進剤モデル、可視化機能などの Pull Request / Issue を歓迎します。

特に以下のような改善を歓迎します。

- より正確な物理モデル
- 大気抵抗モデル
- 多段ロケット対応
- より柔軟な推進剤データベース
- シミュレーション結果の CSV / JSON 出力
- GUI の改善
- テストコードの追加

---

## ⚠️ Disclaimer

本ソフトウェアの計算結果は簡略化された数値モデルによるものです。

実際のロケット、エンジン、推進剤、航空宇宙機器などの設計・製造・運用に利用することを想定していません。

研究・教育・プログラミング学習・数値実験の目的で使用してください。
