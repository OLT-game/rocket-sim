import csv
import ctypes
from datetime import datetime
import json
import math
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 高解像度ディスプレイ(DPI)対応 & 日本語フォント設定
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except (AttributeError, OSError):
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
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

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
    LEGEND_MAX_ROWS = 30

    def __init__(self, root):
        self.root = root
        self.root.title(
            "NASA物理モデル 高精度ロケット物理シミュレータ (大気圏/CSV出力拡張版)"
        )
        self.root.geometry("1400x950")
        self.root.minsize(1200, 760)

        self.is_exiting = False  # 強制終了フラグ
        self.last_results = []  # CSV保存用データキャッシュ

        self.logger = Logger()
        self.logger.reset()
        self.logger.info("ロケットシミュレータ アプリケーション起動")

        self.config = self.load_config()
        if not self.config:
            self.force_exit_process()
            return

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_safe_exit)

    def force_exit_process(self):
        """GUIとMatplotlibリソースを安全に解放して終了する"""
        self.is_exiting = True
        try:
            plt.close("all")
        except Exception as e:
            self.logger.error(f"Matplotlib終了処理エラー: {e}")
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def load_config(self):
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        filename = os.path.basename(config_path)
        if not os.path.exists(config_path):
            messagebox.showerror(
                "設定エラー",
                f"『{filename}』が見つかりません。プロジェクト内に配置してください。",
            )
            self.logger.error(f"『{filename}』が見つかりません。")
            return None
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.logger.info(f"『{filename}』の読み込みに成功しました")
                return cfg
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"JSON解析エラー: {e}")
            self.logger.error(f"JSON解析エラー: {e}")
            return None

    def get_propellant_dict(self):
        """設定ファイルから推進剤データを取得（新旧フォーマット対応）"""
        if "propellant_presets" in self.config:
            return self.config["propellant_presets"]
        return self.config.get("propellants", {})

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

        # マウスホイールによるスクロールイベント設定
        def _on_mousewheel(event):
            if event.num == 4:
                left_scroll.yview_scroll(-1, "units")
            elif event.num == 5:
                left_scroll.yview_scroll(1, "units")
            else:
                left_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            left_scroll.bind_all("<MouseWheel>", _on_mousewheel)
            left_scroll.bind_all("<Button-4>", _on_mousewheel)
            left_scroll.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            left_scroll.unbind_all("<MouseWheel>")
            left_scroll.unbind_all("<Button-4>")
            left_scroll.unbind_all("<Button-5>")

        left_container.bind("<Enter>", _bind_mousewheel)
        left_container.bind("<Leave>", _unbind_mousewheel)

        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        specs = self.config.get("rocket_common_specs", {})

        # --- パラメータ設定領域 ---
        ttk.Label(
            left_frame, text="⚙ 機体物理仕様パラメータ", font=("Helvetica", 11, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))

        # 乾燥質量
        ttk.Label(
            left_frame, text="乾燥質量 (Dry Mass) [kg] (クリックで手入力):"
        ).pack(anchor=tk.W)
        self.dry_mass_var = tk.DoubleVar(value=specs.get("dry_mass_kg", 1000.0))
        self.lbl_dry = ttk.Label(
            left_frame,
            text=f"{self.dry_mass_var.get():.1f} kg",
            foreground="blue",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        self.lbl_dry.pack(anchor=tk.W)
        self.slider_dry = ttk.Scale(
            left_frame,
            from_=100,
            to=5000,
            variable=self.dry_mass_var,
            command=lambda v: self.lbl_dry.config(text=f"{float(v):.1f} kg"),
        )
        self.slider_dry.pack(fill=tk.X, pady=(0, 6))
        self.lbl_dry.bind(
            "<Button-1>",
            lambda e: self.prompt_edit_value(
                "乾燥質量 (kg)",
                self.dry_mass_var,
                self.slider_dry,
                10.0,
                500000.0,
                lambda: self.lbl_dry.config(
                    text=f"{self.dry_mass_var.get():.1f} kg"
                ),
            ),
        )

        # 推進剤質量
        ttk.Label(left_frame, text="推進剤総質量 [kg] (クリックで手入力):").pack(
            anchor=tk.W
        )
        self.prop_mass_var = tk.DoubleVar(
            value=specs.get("total_propellant_mass_kg", 10000.0)
        )
        self.lbl_prop = ttk.Label(
            left_frame,
            text=f"{self.prop_mass_var.get():.1f} kg",
            foreground="blue",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        self.lbl_prop.pack(anchor=tk.W)
        self.slider_prop = ttk.Scale(
            left_frame,
            from_=500,
            to=30000,
            variable=self.prop_mass_var,
            command=lambda v: [
                self.lbl_prop.config(text=f"{float(v):.1f} kg"),
                self.update_of_ratio_preview(),
            ],
        )
        self.slider_prop.pack(fill=tk.X, pady=(0, 6))
        self.lbl_prop.bind(
            "<Button-1>",
            lambda e: self.prompt_edit_value(
                "推進剤総質量 (kg)",
                self.prop_mass_var,
                self.slider_prop,
                100.0,
                10000000.0,
                lambda: [
                    self.lbl_prop.config(
                        text=f"{self.prop_mass_var.get():.1f} kg"
                    ),
                    self.update_of_ratio_preview(),
                ],
            ),
        )

        # エンジン推力
        ttk.Label(left_frame, text="エンジン推力 [N] (クリックで手入力):").pack(
            anchor=tk.W
        )
        self.thrust_var = tk.DoubleVar(
            value=specs.get("engine_thrust_N", 100000.0)
        )
        self.lbl_thrust = ttk.Label(
            left_frame,
            text=f"{self.thrust_var.get():.0f} N",
            foreground="blue",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        self.lbl_thrust.pack(anchor=tk.W)
        self.slider_thrust = ttk.Scale(
            left_frame,
            from_=10000,
            to=500000,
            variable=self.thrust_var,
            command=lambda v: self.lbl_thrust.config(text=f"{float(v):.0f} N"),
        )
        self.slider_thrust.pack(fill=tk.X, pady=(0, 6))
        self.lbl_thrust.bind(
            "<Button-1>",
            lambda e: self.prompt_edit_value(
                "エンジン推力 (N)",
                self.thrust_var,
                self.slider_thrust,
                1000.0,
                50000000.0,
                lambda: self.lbl_thrust.config(
                    text=f"{self.thrust_var.get():.0f} N"
                ),
            ),
        )

        # --- O/F比 (混合比) 設定UI ---
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(
            left_frame,
            text="⚗️ O/F比 (混合比) リアルタイム設定",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))

        self.of_ratio_var = tk.DoubleVar(value=3.5)
        self.lbl_of = ttk.Label(
            left_frame,
            text="O/F比: 3.50 (クリックで手入力)",
            foreground="blue",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        self.lbl_of.pack(anchor=tk.W)
        self.slider_of = ttk.Scale(
            left_frame,
            from_=1.0,
            to=10.0,
            variable=self.of_ratio_var,
            command=lambda v: self.update_of_ratio_preview(),
        )
        self.slider_of.pack(fill=tk.X, pady=(0, 4))
        self.lbl_of.bind(
            "<Button-1>",
            lambda e: self.prompt_edit_value(
                "O/F比 (混合比)",
                self.of_ratio_var,
                self.slider_of,
                0.1,
                50.0,
                lambda: self.update_of_ratio_preview(),
            ),
        )

        self.lbl_fuel_ox_ratio = ttk.Label(
            left_frame,
            text="燃料: 0.0 kg | 酸化剤: 0.0 kg",
            font=("Consolas", 8),
            foreground="darkblue",
        )
        self.lbl_fuel_ox_ratio.pack(anchor=tk.W, pady=(0, 6))
        self.update_of_ratio_preview()

        # --- 環境・物理物理オプション ---
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(
            left_frame, text="🌍 飛行環境シミュレーションモデル", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.use_atmosphere_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left_frame,
            text="地球大気圏影響 (空気抵抗・Isp高度変化) を考慮",
            variable=self.use_atmosphere_var,
        ).pack(anchor=tk.W, pady=(0, 6))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        # 表示設定
        ttk.Label(
            left_frame, text="📊 グラフ表示設定", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.time_unit_var = tk.StringVar(value="sec")
        time_unit_frame = ttk.Frame(left_frame)
        time_unit_frame.pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(time_unit_frame, text="時間軸単位: ").pack(side=tk.LEFT)
        ttk.Radiobutton(
            time_unit_frame,
            text="秒 (sec)",
            value="sec",
            variable=self.time_unit_var,
        ).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(
            time_unit_frame,
            text="分 (min)",
            value="min",
            variable=self.time_unit_var,
        ).pack(side=tk.LEFT, padx=3)

        # 実行ボタン
        self.btn_calc = ttk.Button(
            left_frame,
            text="🚀 精密物理シミュレーション実行",
            command=self.start_simulation_thread,
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
            left_frame,
            text="🏆 物理評価スコア & ランキング",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))

        self.result_text = tk.Text(
            left_frame,
            width=32,
            height=10,
            font=("Consolas", 9),
            relief=tk.SOLID,
            bd=1,
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # エクスポートセクション
        ttk.Label(
            left_frame,
            text="💾 データ & 画像エクスポート",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(4, 4))

        btn_export_csv = ttk.Button(
            left_frame, text="📄 時系列数値データ (CSV) 保存", command=self.export_to_csv
        )
        btn_export_csv.pack(fill=tk.X, ipady=3, pady=2)

        btn_save_all = ttk.Button(
            left_frame, text="🖼️ 全体グラフ保存 (4K~6K)", command=self.save_graph_all
        )
        btn_save_all.pack(fill=tk.X, ipady=3, pady=2)

        btn_save_alt = ttk.Button(
            left_frame, text="🖼️ 高度グラフ保存", command=self.save_graph_alt
        )
        btn_save_alt.pack(fill=tk.X, ipady=3, pady=2)

        btn_save_prop = ttk.Button(
            left_frame, text="🖼️ 推進剤グラフ保存", command=self.save_graph_prop
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

        self.plot_filter_var.trace_add(
            "write", lambda *_: self.refresh_plot_selection()
        )
        self.plot_mode_var.trace_add(
            "write", lambda *_: self.refresh_plot_selection()
        )

        self.left_frame.bind("<Configure>", self._on_left_frame_configure)
        self.left_canvas.bind("<Configure>", self._on_left_canvas_configure)

        # 右側 Matplotlib 2段グラフ領域
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2, 1, figsize=(9, 7.5), sharex=True
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.refresh_plot_selection()

    def prompt_edit_value(
        self, title, target_var, slider, min_val, max_val, update_callback
    ):
        """数字部分をクリックして手動数値入力を行うダイアログ（スライダー範囲の自動追従付き）"""
        val = simpledialog.askfloat(
            "数値の手動入力",
            f"新しい {title} を入力してください:\n(設定可能範囲: {min_val} ~ {max_val})",
            initialvalue=target_var.get(),
            minvalue=min_val,
            maxvalue=max_val,
            parent=self.root,
        )
        if val is not None:
            # スライダーの最大/最小値を入力値に合わせて拡張
            current_from = slider.cget("from")
            current_to = slider.cget("to")
            if val < current_from:
                slider.configure(from_=val)
            if val > current_to:
                slider.configure(to_=val)

            target_var.set(val)
            update_callback()

    def update_of_ratio_preview(self):
        """O/F比に基づく燃料・酸化剤初期質量のプレビュー更新"""
        r = self.of_ratio_var.get()
        total_m = self.prop_mass_var.get()
        m_fuel = total_m / (1.0 + r)
        m_ox = m_fuel * r
        self.lbl_of.config(text=f"O/F比: {r:.2f} (クリックで手入力)")
        self.lbl_fuel_ox_ratio.config(
            text=f"燃料: {m_fuel:.1f}kg | 酸化剤: {m_ox:.1f}kg"
        )

    def _on_left_canvas_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_left_frame_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def refresh_plot_selection(self):
        try:
            propellants = self.get_propellant_dict()
            selected_state = self.plot_filter_var.get()
            if selected_state != "all":
                propellants = {
                    p_id: p_data
                    for p_id, p_data in propellants.items()
                    if p_data.get("state_type") == selected_state
                }
            count = max(1, len(propellants))
            self.top_n_spin.configure(from_=1, to=count)
        except Exception:
            pass

    def set_simulation_controls_enabled(self, enabled):
        """シミュレーション実行ボタンと進捗バーを一括制御"""
        self.btn_calc.config(state=tk.NORMAL if enabled else tk.DISABLED)
        if enabled:
            self.progress_bar.stop()
        else:
            self.progress_bar.start(10)

    def save_single_axis(self, axis, filepath):
        """指定された1つのグラフだけを余白込みで保存"""
        self.canvas.draw()
        renderer = self.canvas.get_renderer()
        bbox = axis.get_tightbbox(renderer).transformed(
            self.fig.dpi_scale_trans.inverted()
        )
        self.fig.savefig(
            filepath,
            dpi=300,
            bbox_inches=bbox.expanded(1.08, 1.15),
            pad_inches=0.15,
        )

    def get_legend_column_count(self, item_count):
        """凡例を30行ごとに右側へ列追加するための列数を返す"""
        return max(
            1, (item_count + self.LEGEND_MAX_ROWS - 1) // self.LEGEND_MAX_ROWS
        )

    def add_right_side_legend(self, axis, item_count):
        """凡例をグラフ右側に最大30行/列で配置"""
        axis.legend(
            bbox_to_anchor=(1.00, 1.0),
            loc="upper left",
            borderaxespad=0.0,
            fontsize=7,
            frameon=True,
            handlelength=1.8,
            labelspacing=0.6,
            handletextpad=0.6,
            columnspacing=1.2,
            ncol=self.get_legend_column_count(item_count),
        )

    def adjust_plot_area_for_legends(self, item_count):
        """凡例列数に応じて右余白を調整"""
        legend_columns = self.get_legend_column_count(item_count)
        right_margin = max(0.44, 0.78 - (legend_columns - 1) * 0.11)
        self.fig.subplots_adjust(
            left=0.10,
            right=right_margin,
            top=0.93,
            bottom=0.08,
            hspace=0.35,
        )

    def get_acceleration(
        self, alt, vel, mass, thrust, g0, R_earth, use_atmosphere
    ):
        """加速度演算 (推力 - 空気抵抗 - 高度依存重力)"""
        g = g0 * (R_earth / (R_earth + max(0.0, alt))) ** 2
        drag = 0.0

        if use_atmosphere and alt >= 0.0:
            # 簡易大気密度モデル: rho(h) = rho0 * exp(-h / h0)
            rho0 = 1.225  # kg/m^3
            scale_height = 8500.0  # m
            rho = rho0 * math.exp(-alt / scale_height)

            # 空気抵抗 D = 0.5 * rho * v^2 * Cd * A (Cd=0.5, A=半径0.5mの円)
            cd = 0.5
            area = math.pi * (0.5**2)
            drag = 0.5 * rho * (vel**2) * cd * area * (1.0 if vel >= 0 else -1.0)

        return ((thrust - drag) / mass) - g

    def shorten_text(self, text, max_len=28):
        """テキストの短縮表示"""
        if not text:
            return text
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    def format_legend_label(self, text, width=15):
        """凡例の改行フォーマット"""
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

    def run_simulation_precise(self, prop_id, override_of_ratio=None):
        """【高精度物理計算エンジン (大気影響選択・4次ルンゲ＝クッタ法 RK4)】"""
        sim_set = self.config["simulation_settings"]
        propellants = self.get_propellant_dict()
        prop = propellants[prop_id]

        dt = sim_set.get("dt", 0.01)
        g0 = sim_set.get("g0", 9.80665)
        R_earth = sim_set.get("earth_radius_m", 6371000.0)
        dry_mass = self.dry_mass_var.get()
        total_prop_mass = self.prop_mass_var.get()
        thrust_force = self.thrust_var.get()
        use_atmosphere = self.use_atmosphere_var.get()

        isp_vac = prop.get("Isp_s", prop.get("isp_sec", 300.0))
        isp_sl = prop.get("Isp_sl_s", isp_vac * 0.85)

        user_of_ratio = (
            override_of_ratio
            if override_of_ratio is not None
            else self.of_ratio_var.get()
        )
        design_of_ratio = prop.get("of_ratio", prop.get("mixture_ratio_o_f", 3.5))

        m_fuel = total_prop_mass / (1.0 + user_of_ratio)
        m_ox = m_fuel * user_of_ratio

        altitude = 0.0
        velocity = 0.0
        elapsed_time = 0.0
        max_altitude = altitude

        log_time = [0.0]
        log_alt = [0.0]
        log_vel = [0.0]
        log_prop_mass = [m_fuel + m_ox]

        running = True
        step_count = 0
        max_steps = 300000

        prev_alt = 0.0
        same_alt_count = 0

        while running and step_count < max_steps:
            if self.is_exiting:
                return [], [], [], [], 0, 0, 0, 0.0, 0.0

            step_count += 1

            # 高度に応じた比推力Ispの補間演算
            if use_atmosphere:
                rho_ratio = math.exp(-max(0.0, altitude) / 8500.0)
                current_isp = isp_sl + (isp_vac - isp_sl) * (1.0 - rho_ratio)
            else:
                current_isp = isp_vac

            c_exhaust = current_isp * g0
            total_m_dot = thrust_force / c_exhaust
            m_dot_fuel = total_m_dot / (1.0 + design_of_ratio)
            m_dot_ox = m_dot_fuel * design_of_ratio

            if m_fuel > 0.0 and m_ox > 0.0 and total_m_dot > 0.0:
                actual_dt = min(dt, m_fuel / m_dot_fuel, m_ox / m_dot_ox)
                thrust = thrust_force
                current_m_dot = total_m_dot
            else:
                thrust = 0.0
                current_m_dot = 0.0
                actual_dt = dt

            prop_mass = m_fuel + m_ox

            # 2階常微分方程式に対する 4次ルンゲ＝クッタ法 (RK4)
            m1 = dry_mass + prop_mass
            m2 = dry_mass + max(
                0.0, prop_mass - current_m_dot * actual_dt * 0.5
            )
            m4 = dry_mass + max(0.0, prop_mass - current_m_dot * actual_dt)

            k1_v = self.get_acceleration(
                altitude, velocity, m1, thrust, g0, R_earth, use_atmosphere
            )
            k1_x = velocity

            k2_v = self.get_acceleration(
                altitude + 0.5 * actual_dt * k1_x,
                velocity + 0.5 * actual_dt * k1_v,
                m2,
                thrust,
                g0,
                R_earth,
                use_atmosphere,
            )
            k2_x = velocity + 0.5 * actual_dt * k1_v

            k3_v = self.get_acceleration(
                altitude + 0.5 * actual_dt * k2_x,
                velocity + 0.5 * actual_dt * k2_v,
                m2,
                thrust,
                g0,
                R_earth,
                use_atmosphere,
            )
            k3_x = velocity + 0.5 * actual_dt * k2_v

            k4_v = self.get_acceleration(
                altitude + actual_dt * k3_x,
                velocity + actual_dt * k3_v,
                m4,
                thrust,
                g0,
                R_earth,
                use_atmosphere,
            )
            k4_x = velocity + actual_dt * k3_v

            velocity += (actual_dt / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)
            altitude += (actual_dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
            elapsed_time += actual_dt

            if thrust > 0.0:
                m_fuel = max(0.0, m_fuel - m_dot_fuel * actual_dt)
                m_ox = max(0.0, m_ox - m_dot_ox * actual_dt)

            max_altitude = max(max_altitude, altitude)

            if step_count % 10 == 0:
                log_time.append(elapsed_time)
                log_alt.append(altitude)
                log_vel.append(velocity)
                log_prop_mass.append(m_fuel + m_ox)

            # アポジー（最高高度）達成判定
            if thrust == 0.0:
                if velocity <= 1e-6 or altitude < prev_alt:
                    running = False

                if abs(altitude - prev_alt) < 1e-7:
                    same_alt_count += 1
                    if same_alt_count > 50:
                        running = False
                else:
                    same_alt_count = 0

            prev_alt = altitude

        if log_time[-1] != elapsed_time:
            log_time.append(elapsed_time)
            log_alt.append(altitude)
            log_vel.append(velocity)
            log_prop_mass.append(m_fuel + m_ox)

        max_alt_km = max_altitude / 1000.0
        score = (g0 * max_alt_km) * (1.0 + (isp_vac / 500.0))

        return (
            log_time,
            log_alt,
            log_vel,
            log_prop_mass,
            max_alt_km,
            score,
            elapsed_time,
            m_fuel,
            m_ox,
        )

    def start_simulation_thread(self):
        """マルチスレッド処理でバックグラウンド実行を起動"""
        self.set_simulation_controls_enabled(False)
        self.lbl_status.config(
            text="⏳ バックグラウンド物理演算中...", foreground="orange"
        )

        threading.Thread(target=self._run_and_plot_worker, daemon=True).start()

    def _run_and_plot_worker(self):
        """スレッド内で重い計算処理を実行"""
        start_time = time.time()
        results = []
        propellants = self.get_propellant_dict()

        selected_state = self.plot_filter_var.get()
        selected_mode = self.plot_mode_var.get()
        top_n = max(1, self.top_n_var.get())

        if selected_state != "all":
            propellants = {
                prop_id: prop_data
                for prop_id, prop_data in propellants.items()
                if prop_data.get("state_type") == selected_state
            }

        total_items = len(propellants)
        self.logger.info("--- ロケット物理シミュレーション計算開始 ---")

        for idx, (prop_id, prop_data) in enumerate(propellants.items(), 1):
            if self.is_exiting:
                return

            prop_name = prop_data.get("name", prop_id)
            short_name = self.shorten_text(prop_name, max_len=30)

            # メインスレッドでのGUIステータス更新
            self.root.after(
                0,
                lambda m=f"[{idx}/{total_items}] 『{short_name}』": self.lbl_status.config(
                    text=f"⏳ {m}", wraplength=260
                ),
            )

            (
                t_log,
                alt_log,
                vel_log,
                prop_log,
                max_alt_km,
                score,
                burn_time,
                rem_fuel,
                rem_ox,
            ) = self.run_simulation_precise(prop_id)

            if self.is_exiting:
                return

            results.append(
                {
                    "id": prop_id,
                    "name": prop_name,
                    "max_alt_km": max_alt_km,
                    "score": score,
                    "isp": prop_data.get("Isp_s", prop_data.get("isp_sec", 0)),
                    "mix_ratio": self.of_ratio_var.get(),
                    "rem_fuel": rem_fuel,
                    "rem_ox": rem_ox,
                    "time_log": t_log,
                    "alt_log": alt_log,
                    "vel_log": vel_log,
                    "prop_log": prop_log,
                }
            )

        results.sort(key=lambda x: x["max_alt_km"], reverse=True)
        if selected_mode == "top":
            results = results[:top_n]

        self.last_results = results  # CSV保存用

        calc_time = time.time() - start_time
        # 描画処理はメインスレッドへ移送
        self.root.after(0, lambda: self._update_gui_with_results(results, calc_time))

    def _update_gui_with_results(self, results, calc_time):
        """メインスレッドでグラフ描画と表示を更新"""
        if self.is_exiting:
            return

        self.ax1.clear()
        self.ax2.clear()

        unit = self.time_unit_var.get()
        time_divisor = 60.0 if unit == "min" else 1.0
        x_label_str = "時間 (分)" if unit == "min" else "時間 (秒)"

        if not results:
            self.set_simulation_controls_enabled(True)
            self.lbl_status.config(
                text="⚠️ 該当するシミュレーション結果がありません", foreground="orange"
            )
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
                t_axis,
                alt_axis,
                label=label_str,
                color=color,
                linewidth=lw,
                alpha=alpha_val,
            )
            self.ax2.plot(
                t_axis,
                res["prop_log"],
                label=self.format_legend_label(res["name"], width=15),
                color=color,
                linewidth=lw,
                alpha=alpha_val,
            )

        env_str = "（大気圏モデル）" if self.use_atmosphere_var.get() else "（真空モデル）"
        self.ax1.set_ylabel("高度 (km)", fontsize=10, fontweight="bold")
        self.ax1.set_title(
            f"ロケット高度推移比較 {env_str}", fontsize=11, fontweight="bold", pad=8
        )
        self.ax1.grid(True, linestyle="--", alpha=0.5)
        self.add_right_side_legend(self.ax1, num_curves)

        self.ax2.set_xlabel(x_label_str, fontsize=10, fontweight="bold")
        self.ax2.set_ylabel("残り推進剤 (kg)", fontsize=10, fontweight="bold")
        self.ax2.set_title("推進剤消費パターン", fontsize=10, fontweight="bold", pad=6)
        self.ax2.grid(True, linestyle="--", alpha=0.5)
        self.add_right_side_legend(self.ax2, num_curves)
        self.adjust_plot_area_for_legends(num_curves)

        try:
            self.canvas.draw()
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "🏆【最高高度・物理スコア 順位】\n")
            self.result_text.insert(tk.END, "═" * 34 + "\n")

            for rank, res in enumerate(results, 1):
                separator = "─" * 34 + "\n"
                line = (
                    f" [{rank}位] {res['name']}\n"
                    f"  最高高度: {res['max_alt_km']:>8.2f} km\n"
                    f"  評価スコア: {res['score']:>7.1f}\n"
                    f"  残燃料: {res['rem_fuel']:>6.1f}kg | 残酸化剤: {res['rem_ox']:>6.1f}kg\n"
                    f"  (Isp: {res['isp']}s | O/F: {res['mix_ratio']:.2f})\n"
                    f"{separator}"
                )
                self.result_text.insert(tk.END, line)

            self.lbl_status.config(
                text=f"✅ シミュレーション完了 ({calc_time:.3f}秒)", foreground="green"
            )
        except Exception as e:
            self.logger.error(f"グラフ描画・結果表示エラー: {e}")
            self.lbl_status.config(
                text="❌ 描画中にエラーが発生しました", foreground="red"
            )
        finally:
            self.set_simulation_controls_enabled(True)

    # --- CSVデータ保存機能 ---
    def export_to_csv(self):
        if not self.last_results:
            messagebox.showwarning(
                "警告", "保存対象のデータがありません。先にシミュレーションを実行してください。"
            )
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="時系列物理データをCSV保存",
            initialfile="rocket_simulation_data.csv",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "推進剤名称",
                        "経過時間(s)",
                        "高度(m)",
                        "高度(km)",
                        "速度(m/s)",
                        "残り推進剤質量(kg)",
                    ]
                )

                for res in self.last_results:
                    p_name = res["name"]
                    for t, alt, vel, prop_m in zip(
                        res["time_log"],
                        res["alt_log"],
                        res["vel_log"],
                        res["prop_log"],
                    ):
                        writer.writerow(
                            [
                                p_name,
                                f"{t:.2f}",
                                f"{alt:.2f}",
                                f"{alt/1000.0:.3f}",
                                f"{vel:.2f}",
                                f"{prop_m:.2f}",
                            ]
                        )

            self.logger.info(f'CSVデータを出力しました: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"時系列数値データをCSV形式で保存しました:\n{filepath}"
            )
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {e}")
            messagebox.showerror("保存エラー", f"CSVファイルの書き込みに失敗しました:\n{e}")

    # --- 高解像度画像保存機能 ---
    def save_graph_alt(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="高度グラフ画像を保存",
            initialfile="rocket_altitude_4k.png",
        )
        if filepath:
            self.save_single_axis(self.ax1, filepath)
            self.logger.info(f'高度グラフを高解像度保存: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"高解像度で高度グラフ画像を保存しました:\n{filepath}"
            )
            self.canvas.draw()

    def save_graph_prop(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="残り推進剤グラフ画像を保存",
            initialfile="rocket_propellant_4k.png",
        )
        if filepath:
            self.save_single_axis(self.ax2, filepath)
            self.logger.info(f'残り推進剤グラフを高解像度保存: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"高解像度で推進剤グラフ画像を保存しました:\n{filepath}"
            )
            self.canvas.draw()

    def save_graph_all(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="全体グラフ画像を保存",
            initialfile="rocket_full_graph_4k.png",
        )
        if filepath:
            self.adjust_plot_area_for_legends(len(self.ax1.lines))
            self.fig.savefig(
                filepath, dpi=300, bbox_inches="tight", pad_inches=0.25
            )
            self.logger.info(f'全体高解像度グラフ画像を保存: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"高解像度で全体グラフ画像を保存しました:\n{filepath}"
            )
            self.canvas.draw()

    def on_safe_exit(self):
        """ウィンドウを閉じた際にGUIリソースを安全に破棄して終了する"""
        self.logger.info("アプリケーション終了命令受信 -> 安全に終了します")
        self.force_exit_process()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpaceRocketSimulatorApp(root)
    root.mainloop()