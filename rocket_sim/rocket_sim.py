from datetime import datetime
import json
import math
import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 高解像度ディスプレイ(DPI)対応 & 日本語フォント設定
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

plt.rcParams["font.sans-serif"] = [
    "MS Gothic",
    "Yu Gothic",
    "Hiragino Sans",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


class Logger:

    def __init__(self, filepath="log.txt"):
        self.filepath = filepath

    def reset(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"ログリセットエラー: {e}")

    def _get_timestamp(self):
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"

    def info(self, message):
        timestamp = self._get_timestamp()
        log_line = f'[Info] {timestamp} : "{message}"\n'
        print(f"[LOG] {message}")
        self._write(log_line)

    def error(self, message):
        timestamp = self._get_timestamp()
        log_line = f'[Error] {timestamp} : "{message}"\n'
        print(f"[ERR] {message}")
        self._write(log_line)

    def _write(self, log_line):
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass


class SpaceRocketSimulatorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("NASA物理モデル 高精度ロケット物理シミュレータ (真空モデル)")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 760)

        self.is_exiting = False  # 強制終了フラグ
        self.last_ui_update_time = 0.0  # GUI更新頻度制限用

        self.logger = Logger()
        self.logger.reset()
        self.logger.info("ロケットシミュレータ (真空モデル) アプリケーション起動")

        self.config = self.load_config()
        if not self.config:
            self.force_exit_process()
            return

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_safe_exit)

    def force_exit_process(self):
        """PythonプロセスをOSレベルで完全にKILLして終了する"""
        self.is_exiting = True
        try:
            plt.close("all")
        except Exception:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

    def load_config(self):
        filename = "config.json"
        if not os.path.exists(filename):
            messagebox.showerror(
                "設定エラー",
                f"『{filename}』が見つかりません。プロジェクト内に配置してください。",
            )
            self.logger.error(f"『{filename}』が見つかりません。")
            return None
        try:
            with open(filename, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.logger.info(f"『{filename}』の読み込みに成功しました")
                return cfg
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"JSON解析エラー: {e}")
            self.logger.error(f"JSON解析エラー: {e}")
            return None

    def setup_ui(self):
        # メインフレーム分割
        left_container = ttk.Frame(self.root)
        left_container.pack(side=tk.LEFT, fill=tk.Y)

        left_scroll = tk.Canvas(left_container, width=340, highlightthickness=0)
        left_scroll.pack(side=tk.LEFT, fill=tk.Y)

        left_scrollbar = ttk.Scrollbar(
            left_container, orient=tk.VERTICAL, command=left_scroll.yview
        )
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_scroll.configure(yscrollcommand=left_scrollbar.set)

        left_frame = ttk.Frame(left_scroll, padding=12)
        left_scroll.create_window((0, 0), window=left_frame, anchor="nw", width=300)

        self.left_frame = left_frame
        self.left_canvas = left_scroll

        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        specs = self.config.get("rocket_common_specs", {})

        # --- パラメータ設定領域 ---
        ttk.Label(
            left_frame, text="⚙ 機体物理仕様パラメータ", font=("Helvetica", 11, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))

        # 乾燥質量
        ttk.Label(left_frame, text="乾燥質量 (Dry Mass) [kg]:").pack(anchor=tk.W)
        self.dry_mass_var = tk.DoubleVar(value=specs.get("dry_mass_kg", 1000.0))
        self.lbl_dry = ttk.Label(left_frame, text=f"{self.dry_mass_var.get():.1f} kg")
        self.lbl_dry.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=100,
            to=5000,
            variable=self.dry_mass_var,
            command=lambda v: self.lbl_dry.config(text=f"{float(v):.1f} kg"),
        ).pack(fill=tk.X, pady=(0, 6))

        # 推進剤質量
        ttk.Label(left_frame, text="推進剤総質量 [kg]:").pack(anchor=tk.W)
        self.prop_mass_var = tk.DoubleVar(
            value=specs.get("total_propellant_mass_kg", 5000.0)
        )
        self.lbl_prop = ttk.Label(left_frame, text=f"{self.prop_mass_var.get():.1f} kg")
        self.lbl_prop.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=500,
            to=30000,
            variable=self.prop_mass_var,
            command=lambda v: self.lbl_prop.config(text=f"{float(v):.1f} kg"),
        ).pack(fill=tk.X, pady=(0, 6))

        # エンジン推力
        ttk.Label(left_frame, text="エンジン推力 [N]:").pack(anchor=tk.W)
        self.thrust_var = tk.DoubleVar(
            value=specs.get("engine_thrust_N", 100000.0)
        )
        self.lbl_thrust = ttk.Label(left_frame, text=f"{self.thrust_var.get():.0f} N")
        self.lbl_thrust.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=10000,
            to=500000,
            variable=self.thrust_var,
            command=lambda v: self.lbl_thrust.config(text=f"{float(v):.0f} N"),
        ).pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # 表示設定
        ttk.Label(
            left_frame, text="📊 グラフ表示設定", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.time_unit_var = tk.StringVar(value="sec")
        time_unit_frame = ttk.Frame(left_frame)
        time_unit_frame.pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(time_unit_frame, text="時間軸単位: ").pack(side=tk.LEFT)
        ttk.Radiobutton(
            time_unit_frame, text="秒 (sec)", value="sec", variable=self.time_unit_var
        ).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(
            time_unit_frame, text="分 (min)", value="min", variable=self.time_unit_var
        ).pack(side=tk.LEFT, padx=3)

        # 実行ボタン
        self.btn_calc = ttk.Button(
            left_frame, text="🚀 精密物理シミュレーション実行", command=self.run_and_plot
        )
        self.btn_calc.pack(fill=tk.X, ipady=6, pady=(4, 6))

        # 動作中プログレスバー
        self.progress_bar = ttk.Progressbar(left_frame, mode="indeterminate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))

        # ステータス表示
        self.lbl_status = ttk.Label(
            left_frame,
            text="状態: 準備完了",
            foreground="blue",
            font=("Helvetica", 9, "bold"),
            wraplength=260,
            justify=tk.LEFT,
        )
        self.lbl_status.pack(anchor=tk.W, pady=(0, 8))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        # 解析結果テキストエリア
        ttk.Label(
            left_frame, text="🏆 物理評価スコア & ランキング", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.result_text = tk.Text(
            left_frame, width=32, height=10, font=("Consolas", 9), relief=tk.SOLID, bd=1
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 画像保存セクション
        ttk.Label(
            left_frame, text="📷 超高解像度 (4K~6K相当) 画像保存", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(4, 4))

        btn_save_all = ttk.Button(
            left_frame, text="💾 全体グラフ保存", command=self.save_graph_all
        )
        btn_save_all.pack(fill=tk.X, ipady=3, pady=2)

        btn_save_alt = ttk.Button(
            left_frame, text="💾 高度グラフ保存", command=self.save_graph_alt
        )
        btn_save_alt.pack(fill=tk.X, ipady=3, pady=2)

        btn_save_prop = ttk.Button(
            left_frame, text="💾 推進剤グラフ保存", command=self.save_graph_prop
        )
        btn_save_prop.pack(fill=tk.X, ipady=3, pady=2)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(
            left_frame, text="🎯 描画対象の設定", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.plot_mode_var = tk.StringVar(value="all")
        plot_mode_frame = ttk.Frame(left_frame)
        plot_mode_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Radiobutton(
            plot_mode_frame,
            text="全件表示",
            value="all",
            variable=self.plot_mode_var,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            plot_mode_frame,
            text="上位のみ表示",
            value="top",
            variable=self.plot_mode_var,
        ).pack(anchor=tk.W)

        self.top_n_var = tk.IntVar(value=10)
        ttk.Label(left_frame, text="表示件数:").pack(anchor=tk.W)
        self.top_n_spin = ttk.Spinbox(
            left_frame,
            from_=1,
            to=100,
            width=8,
            textvariable=self.top_n_var,
            command=self.refresh_plot_selection,
        )
        self.top_n_spin.pack(anchor=tk.W, pady=(0, 8))

        self.plot_filter_var = tk.StringVar(value="all")
        ttk.Label(left_frame, text="燃料の種別:").pack(anchor=tk.W)
        ttk.Combobox(
            left_frame,
            textvariable=self.plot_filter_var,
            values=["all", "液体", "固体", "ハイブリッド", "気体"],
            state="readonly",
            width=18,
        ).pack(anchor=tk.W, pady=(0, 8))
        self.plot_filter_var.trace_add("write", lambda *_: self.refresh_plot_selection())
        self.plot_mode_var.trace_add("write", lambda *_: self.refresh_plot_selection())

        self.left_frame.bind("<Configure>", self._on_left_frame_configure)
        self.left_canvas.bind("<Configure>", self._on_left_canvas_configure)

        # 右側 Matplotlib 2段グラフ領域
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_left_canvas_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_left_frame_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def refresh_plot_selection(self):
        try:
            self.top_n_spin.configure(from_=1, to=max(1, len(self.config.get("propellants", {}))))
        except Exception:
            pass

    def safe_update_gui(self, force=False):
        """GUIのガクガク（描画遅延）を防ぐため、一定時間ごとにのみ描画更新"""
        now = time.time()
        if force or (now - self.last_ui_update_time > 0.05):
            self.last_ui_update_time = now
            try:
                self.root.update_idletasks()
                self.root.update()
            except Exception:
                pass

    def get_acceleration(self, alt, mass, thrust, g0, R_earth):
        """真空中での加速度計算 (推力 - 高度依存重力)"""
        g = g0 * (R_earth / (R_earth + max(0.0, alt))) ** 2
        accel = (thrust / mass) - g
        return accel

    def shorten_text(self, text, max_len=28):
        """GUIで長い表示名が崩れないように短く整形する"""
        if not text:
            return text
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    def format_legend_label(self, text, width=15):
        """凡例の長い名前を 15 文字ごとに改行して画面内に収める"""
        if not text:
            return text
        wrapped = []
        current = ""
        for char in text:
            current += char
            if len(current) >= width and char != " ":
                wrapped.append(current)
                current = ""
        if current:
            wrapped.append(current)
        return "\n".join(wrapped) if wrapped else text

    def run_simulation_precise(self, prop_id):
        """【真空中 超高精度物理計算エンジン (4次ルンゲ＝クッタ法 RK4)】"""
        sim_set = self.config["simulation_settings"]
        prop = self.config["propellants"][prop_id]

        dt = sim_set.get("dt", 0.01)
        g0 = sim_set.get("g0", 9.80665)
        R_earth = sim_set.get("earth_radius_m", 6371000.0)

        dry_mass = self.dry_mass_var.get()
        total_prop_mass = self.prop_mass_var.get()
        thrust_force = self.thrust_var.get()

        isp = prop["isp_sec"]
        c_exhaust = isp * g0
        mix_ratio = prop["mixture_ratio_o_f"]

        fuel_mass = total_prop_mass / (1.0 + mix_ratio)
        oxidizer_mass = total_prop_mass - fuel_mass

        total_m_dot = thrust_force / c_exhaust
        fuel_m_dot = total_m_dot / (1.0 + mix_ratio)
        oxidizer_m_dot = total_m_dot * mix_ratio / (1.0 + mix_ratio)

        altitude = 0.0
        velocity = 0.0
        elapsed_time = 0.0

        log_time = [0.0]
        log_alt = [0.0]
        log_prop_mass = [total_prop_mass]

        running = True
        step_count = 0
        max_steps = 200000

        prev_alt = 0.0
        same_alt_count = 0

        while running and step_count < max_steps:
            if self.is_exiting:
                return None, None, None, 0, 0, 0

            step_count += 1
            current_prop_mass = fuel_mass + oxidizer_mass
            current_mass = dry_mass + current_prop_mass

            # 燃焼処理
            if fuel_mass > 0.0 and oxidizer_mass > 0.0:
                f_req = fuel_m_dot * dt
                o_req = oxidizer_m_dot * dt

                f_ratio = fuel_mass / f_req if f_req > 0 else 1.0
                o_ratio = oxidizer_mass / o_req if o_req > 0 else 1.0
                burn_ratio = min(1.0, f_ratio, o_ratio)

                actual_dt = dt * burn_ratio
                thrust = thrust_force if burn_ratio > 0.0 else 0.0

                fuel_mass -= fuel_m_dot * actual_dt
                oxidizer_mass -= oxidizer_m_dot * actual_dt

                if fuel_mass < 1e-9:
                    fuel_mass = 0.0
                if oxidizer_mass < 1e-9:
                    oxidizer_mass = 0.0
            else:
                thrust = 0.0
                actual_dt = dt

            # 真空中 4次ルンゲ＝クッタ法 (RK4) 数値積分
            k1_v = self.get_acceleration(altitude, current_mass, thrust, g0, R_earth)
            k1_x = velocity

            k2_v = self.get_acceleration(altitude + 0.5 * actual_dt * k1_x, current_mass, thrust, g0, R_earth)
            k2_x = velocity + 0.5 * actual_dt * k1_v

            k3_v = self.get_acceleration(altitude + 0.5 * actual_dt * k2_x, current_mass, thrust, g0, R_earth)
            k3_x = velocity + 0.5 * actual_dt * k2_v

            k4_v = self.get_acceleration(altitude + actual_dt * k3_x, current_mass, thrust, g0, R_earth)
            k4_x = velocity + actual_dt * k3_v

            velocity += (actual_dt / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)
            altitude += (actual_dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
            elapsed_time += actual_dt

            # 10ステップ毎にログ記録（軽量化）
            if step_count % 10 == 0:
                log_time.append(elapsed_time)
                log_alt.append(altitude)
                log_prop_mass.append(fuel_mass + oxidizer_mass)

            # --- 最高高度（アポジー）検知 & 無限ループ防止 ---
            if thrust == 0.0:
                if velocity <= 1e-6 or altitude < prev_alt:
                    running = False  # 最高高度到達

                if abs(altitude - prev_alt) < 1e-7:
                    same_alt_count += 1
                    if same_alt_count > 50:
                        running = False
                else:
                    same_alt_count = 0

            prev_alt = altitude

        max_alt_m = max(log_alt) if len(log_alt) > 0 else 0.0
        max_alt_km = max_alt_m / 1000.0
        score = (g0 * max_alt_m / 1000.0) * (1.0 + (isp / 500.0))

        return log_time, log_alt, log_prop_mass, max_alt_km, score, elapsed_time

    def run_and_plot(self):
        """シミュレーション実行・画面更新"""
        start_time = time.time()

        self.btn_calc.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.lbl_status.config(text="⏳ 物理演算・プロット処理中...", foreground="orange")
        self.safe_update_gui(force=True)

        self.ax1.clear()
        self.ax2.clear()

        unit = self.time_unit_var.get()
        time_divisor = 60.0 if unit == "min" else 1.0
        x_label_str = "時間 (分)" if unit == "min" else "時間 (秒)"

        results = []
        propellants = self.config.get("propellants", {})
        total_items = len(propellants)

        selected_state = self.plot_filter_var.get()
        selected_mode = self.plot_mode_var.get()
        top_n = max(1, self.top_n_var.get())

        if selected_state != "all":
            propellants = {
                prop_id: prop_data
                for prop_id, prop_data in propellants.items()
                if prop_data.get("state_type") == selected_state
            }

        self.logger.info("--- 真空ロケット物理シミュレーション計算開始 ---")

        for idx, (prop_id, prop_data) in enumerate(propellants.items(), 1):
            if self.is_exiting:
                return

            prop_name = prop_data.get("name", prop_id)
            short_name = self.shorten_text(prop_name, max_len=30)

            msg = f"[{idx}/{total_items}] 『{short_name}』"
            self.lbl_status.config(text=f"⏳ {msg}", wraplength=260)
            self.safe_update_gui()

            t_log, alt_log, prop_log, max_alt_km, score, burn_time = (
                self.run_simulation_precise(prop_id)
            )

            if self.is_exiting:
                return

            results.append(
                {
                    "id": prop_id,
                    "name": prop_name,
                    "max_alt_km": max_alt_km,
                    "score": score,
                    "isp": prop_data.get("isp_sec", 0),
                    "mix_ratio": prop_data.get("mixture_ratio_o_f", 0),
                    "time_log": t_log,
                    "alt_log": alt_log,
                    "prop_log": prop_log,
                }
            )

        results.sort(key=lambda x: x["max_alt_km"], reverse=True)
        if selected_mode == "top":
            results = results[:top_n]

        if not results:
            self.progress_bar.stop()
            self.btn_calc.config(state=tk.NORMAL)
            self.lbl_status.config(
                text="⚠️ 実行可能なシミュレーション結果がありません", foreground="orange"
            )
            self.logger.info("シミュレーション結果が空のため描画をスキップしました。")
            return

        num_curves = len(results)
        cmap_name = "tab10" if num_curves <= 10 else "jet"
        cmap = plt.get_cmap(cmap_name, max(1, num_curves))
        lw = 2.0 if num_curves <= 5 else (1.5 if num_curves <= 12 else 1.0)
        alpha_val = 0.9 if num_curves <= 10 else 0.7

        for idx, res in enumerate(results):
            t_axis = [t / time_divisor for t in res["time_log"]]
            alt_axis = [h / 1000.0 for h in res["alt_log"]]

            color = cmap(idx)
            label_str = self.format_legend_label(
                f"{res['name']} ({res['max_alt_km']:.1f} km)", width=15
            )

            self.ax1.plot(
                t_axis, alt_axis, label=label_str, color=color, linewidth=lw, alpha=alpha_val
            )
            self.ax2.plot(
                t_axis, res["prop_log"], label=self.format_legend_label(res["name"], width=15), color=color, linewidth=lw, alpha=alpha_val
            )

        self.ax1.set_ylabel("高度 (km)", fontsize=10, fontweight="bold")
        self.ax1.set_title("真空物理モデル ロケット高度推移比較", fontsize=11, fontweight="bold", pad=8)
        self.ax1.grid(True, linestyle="--", alpha=0.5)
        self.ax1.legend(
            bbox_to_anchor=(1.00, 1.0),
            loc="upper left",
            borderaxespad=0.0,
            fontsize=7,
            frameon=True,
            handlelength=1.8,
            labelspacing=0.6,
            handletextpad=0.6,
        )

        self.ax2.set_xlabel(x_label_str, fontsize=10, fontweight="bold")
        self.ax2.set_ylabel("残り推進剤 (kg)", fontsize=10, fontweight="bold")
        self.ax2.set_title("推進剤消費パターン", fontsize=10, fontweight="bold", pad=6)
        self.ax2.grid(True, linestyle="--", alpha=0.5)
        self.ax2.legend(
            bbox_to_anchor=(1.00, 1.0),
            loc="upper left",
            borderaxespad=0.0,
            fontsize=7,
            frameon=True,
            handlelength=1.8,
            labelspacing=0.6,
            handletextpad=0.6,
        )

        self.fig.subplots_adjust(left=0.10, right=0.78, top=0.93, bottom=0.08, hspace=0.35)
        
        try:
            self.canvas.draw()
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "🏆【最高高度・物理スコア 順位】\n")
            self.result_text.insert(tk.END, "═" * 34 + "\n")

            for rank, res in enumerate(results, 1):
                line = (
                    f" [{rank}位] {res['name']}\n"
                    f"  最高高度: {res['max_alt_km']:>8.2f} km\n"
                    f"  評価スコア: {res['score']:>7.1f}\n"
                    f"  (Isp: {res['isp']}s | O/F: {res['mix_ratio']})\n"
                    f"─" * 34 + "\n"
                )
                self.result_text.insert(tk.END, line)

            calc_time = time.time() - start_time
            self.progress_bar.stop()
            self.btn_calc.config(state=tk.NORMAL)
            self.lbl_status.config(
                text=f"✅ シミュレーション完了 ({calc_time:.3f}秒)", foreground="green"
            )
        except Exception:
            return

        self.logger.info("全計算およびグラフ表示が完了しました。")

    # 高解像度画像保存機能
    def save_graph_alt(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="高度グラフ画像を保存",
            initialfile="rocket_altitude_4k.png",
        )
        if filepath:
            self.fig.tight_layout(rect=[0, 0, 0.82, 1])
            legend = self.ax1.get_legend()
            if legend is not None:
                legend.remove()
            self.fig.savefig(filepath, dpi=300, bbox_inches="tight", pad_inches=0.25)
            self.logger.info(f'高度グラフを高解像度保存: "{filepath}"')
            messagebox.showinfo("保存完了", f"高解像度で高度グラフ画像を保存しました:\n{filepath}")
            self.ax1.legend(
                bbox_to_anchor=(1.00, 1.0),
                loc="upper left",
                borderaxespad=0.0,
                fontsize=7,
                frameon=True,
                handlelength=1.8,
                labelspacing=0.6,
                handletextpad=0.6,
            )

    def save_graph_prop(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="残り推進剤グラフ画像を保存",
            initialfile="rocket_propellant_4k.png",
        )
        if filepath:
            self.fig.tight_layout(rect=[0, 0, 0.82, 1])
            legend = self.ax2.get_legend()
            if legend is not None:
                legend.remove()
            self.fig.savefig(filepath, dpi=300, bbox_inches="tight", pad_inches=0.25)
            self.logger.info(f'残り推進剤グラフを高解像度保存: "{filepath}"')
            messagebox.showinfo("保存完了", f"高解像度で推進剤グラフ画像を保存しました:\n{filepath}")
            self.ax2.legend(
                bbox_to_anchor=(1.00, 1.0),
                loc="upper left",
                borderaxespad=0.0,
                fontsize=7,
                frameon=True,
                handlelength=1.8,
                labelspacing=0.6,
                handletextpad=0.6,
            )

    def save_graph_all(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="全体グラフ画像を保存",
            initialfile="rocket_full_graph_4k.png",
        )
        if filepath:
            self.fig.tight_layout(rect=[0, 0, 0.82, 1])
            for ax in (self.ax1, self.ax2):
                legend = ax.get_legend()
                if legend is not None:
                    legend.remove()
            self.fig.savefig(filepath, dpi=300, bbox_inches="tight", pad_inches=0.25)
            self.logger.info(f'全体高解像度グラフ画像を保存: "{filepath}"')
            messagebox.showinfo("保存完了", f"高解像度で全体グラフ画像を保存しました:\n{filepath}")
            self.ax1.legend(
                bbox_to_anchor=(1.00, 1.0),
                loc="upper left",
                borderaxespad=0.0,
                fontsize=7,
                frameon=True,
                handlelength=1.8,
                labelspacing=0.6,
                handletextpad=0.6,
            )
            self.ax2.legend(
                bbox_to_anchor=(1.00, 1.0),
                loc="upper left",
                borderaxespad=0.0,
                fontsize=7,
                frameon=True,
                handlelength=1.8,
                labelspacing=0.6,
                handletextpad=0.6,
            )

    def on_safe_exit(self):
        """ウィンドウを閉じた際に確実にプロセス全体を破棄・完全終了させる"""
        self.logger.info("アプリケーション終了命令受信 -> プロセスを強制Killします")
        self.force_exit_process()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpaceRocketSimulatorApp(root)
    root.mainloop()