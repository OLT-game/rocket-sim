# 🚀 宇宙ロケット高度・燃費スコアシミュレータ
*(Space Rocket Altitude & Fuel Efficiency Score Simulator)*

NASA物理モデル（真空・地球の万有引力）に基づき、異なる推進剤（燃料＋酸化剤）の組み合わせにおけるロケットの最高高度および燃費スコアを比較計算・可視化するPython GUIアプリケーションです。

---

## 📌 主な機能

* **物理モデル計算**: ニュートンの万有引力の法則および運動方程式（オイラー法）を用いた正確な軌道・高度計算。
* **直感的なGUI**: `Tkinter` のスライダーを用いたリアルタイムなパラメータ調整（機体重量、推進剤質量、推力）。
* **マルチプロット表示**: `Matplotlib` を使用した高度推移および残り推進剤量のリアルタイムグラフ化。
* **高解像度出力**: 「高度グラフ」「残り推進剤グラフ」「全体グラフ」を個別でPNG画像として保存可能。
* **システム監視＆ログ**: 実行時のシステムリソース（CPU/Disk）監視および動作ログの自動保存機能 (`log.txt`)。

---

## 🛠 動作環境 & 必要ライブラリ

### 前提条件
* **Python**: 3.8 以上

### 依存パッケージのインストール
`tkinter`, `json`, `math`, `os`, `sys`, `time`, `datetime` などの標準ライブラリに加え、以下の外部パッケージが必要です。

```bash
pip install matplotlib psutil
```

---

## 🚀 クイックスタート

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/rocket-simulator.git
cd rocket-simulator
```

### 2. 設定ファイルの配置
実行ファイル (`main.py`) と同じディレクトリに `config.json` を配置します。

```json
{
  "rocket_common_specs": {
    "dry_mass_kg": 1000.0,
    "total_propellant_mass_kg": 10000.0,
    "engine_thrust_N": 100000.0
  },
  "simulation_settings": {
    "g0": 9.80665
  },
  "propellants": {
    "LOX_LH2": {
      "name": "液体酸素 / 液体水素",
      "isp_sec": 450,
      "mixture_ratio_o_f": 6.0
    },
    "LOX_RP1": {
      "name": "液体酸素 / ケロシン",
      "isp_sec": 310,
      "mixture_ratio_o_f": 2.56
    }
  }
}
```

### 3. アプリケーションの起動
```bash
python main.py
```

---

## 🎮 操作方法

1. **パラメータ調整**: 画面左側のスライダーで「機体乾燥質量」「推進剤総質量」「エンジン推力」を任意に調整します。
2. **シミュレーション実行**: 「🌌 物理シミュレーション実行」ボタンをクリックすると計算が始まり、グラフとスコアレポートが即座に更新されます。
3. **グラフの保存**: 画像保存パネルから、必要なグラフ（高度/残り推進剤/全体）を個別に保存できます。

---

## 📐 組み込まれている物理法則・数学公式

本シミュレータは、宇宙工学における以下の基礎方程式に基づき数理モデルを構築しています。

### 1. ツィオルコフスキーのロケット方程式 (Tsiolkovsky Rocket Equation)
推進剤の噴射による実効射出速度 $c$ およびデルタV（速度増分） $\Delta v$ を算出します。

* **実効射出速度**:
  $$c = I_{sp} \cdot g_0$$
  *( $I_{sp}$: 比推力 [s], $g_0$: 地表の標準重力加速度 $9.80665 \text{ m/s}^2$ )*

* **デルタV**:
  $$\Delta v = c \cdot \ln\left(\frac{m_{\text{start}}}{m_{\text{dry}}}\right) = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_{\text{start}}}{m_{\text{dry}}}\right)$$

### 2. 推進剤消費率と質量変化
* **推進剤消費率 $\dot{m}$**:
  $$\dot{m} = \frac{F_{\text{thrust}}}{c} = \frac{F_{\text{thrust}}}{I_{sp} \cdot g_0}$$
* **時間変化に伴う質量 $m(t)$**:
  $$m(t) = m_{\text{dry}} + m_{\text{propellant}}(t)$$

### 3. ニュートンの万有引力の法則
高度上昇に伴う地球重力の減衰（逆二乗則）を計算します。

* **高度 $h$（中心距離 $r = R_{\text{earth}} + h$）における重力加速度 $g(r)$**:
  $$g(r) = \frac{G \cdot M_{\text{earth}}}{r^2}$$
  *( $G$: 万有引力定数 $6.67430 \times 10^{-11} \text{ m}^3/\text{kg}\cdot\text{s}^2$, $M_{\text{earth}}$: 地球質量 $5.972 \times 10^{24} \text{ kg}$, $R_{\text{earth}}$: 地球半径 $6,371,000 \text{ m}$ )*

### 4. 運動方程式（オイラー法による数値積分）
加速度 $a(t)$ から速度 $v(t)$ および高度 $r(t)$ をタイムステップ $\Delta t$ ごとに順次更新します。

* **加速度**: $a(t) = \frac{F_{\text{thrust}}}{m(t)} - g(r)$
* **速度更新**: $v(t + \Delta t) = v(t) + a(t) \cdot \Delta t$
* **位置（高度）更新**: $r(t + \Delta t) = r(t) + v(t) \cdot \Delta t$

---

## 📜 ライセンス

This project is licensed under the MIT License - see the [LICENSE](License) file for details.
