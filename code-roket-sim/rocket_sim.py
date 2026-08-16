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
import psutil

# 日本語フォント設定
plt.rcParams["font.sans-serif"] = [
    "MS Gothic",
    "Yu Gothic",
    "Hiragino Sans",
    "DejaVu Sans",
]


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
        self._write(log_line)

    def error(self, message):
        timestamp = self._get_timestamp()
        log_line = f'[error] {timestamp} : "{message}"\n'
        self._write(log_line)

    def _write(self, log_line):
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"ログ書き込みエラー: {e}")


class SpaceRocketSimulatorApp:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "NASA物理モデル 真空・万有引力 宇宙ロケット高度・燃費スコアシミュレータ"
        )
        self.root.geometry("1350x900")

        self.logger = Logger("log.txt")
        self.after_id = None
        self.is_running = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_safe_exit)

        # 宇宙定数（NASA標準値）
        self.AU = 1.496e11  # 天文単位 (m)
        self.M_EARTH = 5.972e24  # 地球質量 (kg)
        self.G = 6.67430e-11  # 万有引力定数 (m^3/kg/s^2)
        self.R_EARTH = 6371000.0  # 地球平均半径 (m)

        self.config = self.load_config()
        if not self.config:
            self.on_safe_exit()
            return

        self.setup_ui()
        self.update_system_stats()

    def load_config(self):
        filename = "config.json"
        if not os.path.exists(filename):
            messagebox.showerror(
                "エラー",
                f"『{filename}』が見つかりません。config.jsonを配置してください。",
            )
            return None
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def setup_ui(self):
        top_bar = ttk.Frame(self.root, padding=5, relief=tk.RIDGE)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        self.lbl_cpu = ttk.Label(
            top_bar,
            text="CPU: -- %",
            font=("Consolas", 10, "bold"),
            foreground="green",
        )
        self.lbl_cpu.pack(side=tk.LEFT, padx=15)

        self.lbl_rom = ttk.Label(
            top_bar, text="ROM(Disk): -- %", font=("Consolas", 10, "bold")
        )
        self.lbl_rom.pack(side=tk.LEFT, padx=15)

        self.lbl_status = ttk.Label(
            top_bar,
            text="状態: 待機中",
            font=("Helvetica", 10, "bold"),
            foreground="gray",
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=15)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, padding=10, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(main_frame, padding=10)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        specs = self.config.get("rocket_common_specs", {})

        ttk.Label(
            left_frame,
            text="【宇宙探査機 仕様設定】",
            font=("Helvetica", 11, "bold"),
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(left_frame, text="機体乾燥質量 (機体のみ) [kg]:").pack(
            anchor=tk.W
        )
        self.dry_mass_var = tk.DoubleVar(
            value=specs.get("dry_mass_kg", 1000.0)
        )
        self.dry_mass_label = ttk.Label(
            left_frame, text=f"{self.dry_mass_var.get():.0f} kg"
        )
        self.dry_mass_label.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=100,
            to=100000,
            variable=self.dry_mass_var,
            command=lambda v: self.dry_mass_label.config(
                text=f"{float(v):.0f} kg"
            ),
        ).pack(fill=tk.X, pady=(0, 4))

        ttk.Label(left_frame, text="推進剤（燃料+酸化剤）総質量 [kg]:").pack(
            anchor=tk.W
        )
        self.prop_mass_var = tk.DoubleVar(
            value=specs.get("total_propellant_mass_kg", 10000.0)
        )
        self.prop_mass_label = ttk.Label(
            left_frame, text=f"{self.prop_mass_var.get():.0f} kg"
        )
        self.prop_mass_label.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=1000,
            to=100000000,
            variable=self.prop_mass_var,
            command=lambda v: self.prop_mass_label.config(
                text=f"{float(v):.0f} kg"
            ),
        ).pack(fill=tk.X, pady=(0, 4))

        ttk.Label(left_frame, text="エンジン推力 [N]:").pack(anchor=tk.W)
        self.thrust_var = tk.DoubleVar(
            value=specs.get("engine_thrust_N", 100000.0)
        )
        self.thrust_label = ttk.Label(
            left_frame, text=f"{self.thrust_var.get():.0f} N"
        )
        self.thrust_label.pack(anchor=tk.W)
        ttk.Scale(
            left_frame,
            from_=1000,
            to=50000000,
            variable=self.thrust_var,
            command=lambda v: self.thrust_label.config(
                text=f"{float(v):.0f} N"
            ),
        ).pack(fill=tk.X, pady=(0, 4))

        ttk.Separator(left_frame, orient="horizontal").pack(
            fill=tk.X, pady=8
        )

        self.btn_run = ttk.Button(
            left_frame,
            text="🌌 物理シミュレーション実行",
            command=self.run_instant_space_simulation,
        )
        self.btn_run.pack(fill=tk.X, ipady=6, pady=2)

        # 画像保存ボタン群（個別保存機能）
        save_frame = ttk.LabelFrame(
            left_frame, text=" 📷 画像出力（個別保存） ", padding=4
        )
        save_frame.pack(fill=tk.X, pady=6)

        ttk.Button(
            save_frame,
            text="📈 「高度グラフ」のみ保存",
            command=self.save_graph_altitude,
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            save_frame,
            text="📉 「残り推進剤グラフ」のみ保存",
            command=self.save_graph_propellant,
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            save_frame,
            text="🖼️ 全体グラフ（両方）を保存",
            command=self.save_graph_all,
        ).pack(fill=tk.X, pady=2)

        ttk.Label(
            left_frame,
            text="【詳細スコア・燃費解析レポート】",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(8, 2))
        result_frame = ttk.Frame(left_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_text = tk.Text(
            result_frame,
            width=44,
            height=10,
            font=("Consolas", 8),
            yscrollcommand=scrollbar.set,
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)

        # ---------------- 右側エリア ----------------
        graph_box = ttk.Frame(right_frame)
        graph_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        legend_box = ttk.LabelFrame(
            right_frame, text=" 推進剤・スコア一覧 ", padding=5
        )
        legend_box.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2,
            1,
            figsize=(7, 7),
            sharex=True,
            gridspec_kw={"height_ratios": [2, 1]},
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_box)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        leg_scroll = ttk.Scrollbar(legend_box)
        leg_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.legend_listbox = tk.Listbox(
            legend_box,
            width=28,
            font=("Consolas", 9),
            yscrollcommand=leg_scroll.set,
            relief=tk.FLAT,
        )
        self.legend_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        leg_scroll.config(command=self.legend_listbox.yview)

    def update_system_stats(self):
        if not self.is_running:
            return
        try:
            self.lbl_cpu.config(text=f"CPU: {psutil.cpu_percent():>4.1f} %")
            self.lbl_rom.config(
                text=f"ROM: {psutil.disk_usage('/').percent:>4.1f} %"
            )
        except Exception:
            pass

        if self.is_running:
            self.after_id = self.root.after(1000, self.update_system_stats)

    def format_time(self, seconds):
        if seconds < 60:
            return f"{seconds:.1f} 秒"
        elif seconds < 3600:
            return f"{seconds / 60.0:.1f} 分"
        elif seconds < 172800:
            return f"{seconds / 3600.0:.1f} 時間"
        else:
            return f"{seconds / 86400.0:.2f} 日"

    def run_instant_space_simulation(self):
        self.logger.reset()

        dry_mass = self.dry_mass_var.get()
        total_prop_mass = self.prop_mass_var.get()
        thrust_force = self.thrust_var.get()

        # ---------------- ログ設定内容出力 ----------------
        self.logger.info("===== シミュレーション設定パラメーター =====")
        self.logger.info(f"機体乾燥質量 (機体重量): {dry_mass} kg")
        self.logger.info(f"推進剤初期質量: {total_prop_mass} kg")
        self.logger.info(
            f"ロケット初期総質量: {dry_mass + total_prop_mass} kg"
        )
        self.logger.info(f"エンジン推力: {thrust_force} N")
        self.logger.info("環境条件: 真空（空気抵抗なし）・地球万有引力考慮")
        self.logger.info(f"万有引力定数 G: {self.G} m^3/kg/s^2")
        self.logger.info(f"地球質量 M: {self.M_EARTH} kg")
        self.logger.info("==========================================")

        self.lbl_status.config(
            text="⚡ NASAモデル軌道・燃費計算中...", foreground="orange"
        )
        self.root.update_idletasks()

        start_time = time.time()

        sim_set = self.config.get("simulation_settings", {})
        propellants = self.config.get("propellants", {})

        g0 = sim_set.get("g0", 9.80665)
        GM_earth = self.G * self.M_EARTH

        self.ax1.clear()
        self.ax2.clear()
        self.legend_listbox.delete(0, tk.END)

        results = []
        MAX_STEPS = 100000
        max_flight_time_sec = 0

        for prop_id, prop in propellants.items():
            name = prop["name"]
            isp = prop["isp_sec"]
            mix_ratio = prop.get("mixture_ratio_o_f", 1.0)

            fuel_mass = total_prop_mass / (1.0 + mix_ratio)
            ox_mass = total_prop_mass - fuel_mass

            c_exhaust = isp * g0
            total_m_dot = thrust_force / c_exhaust
            fuel_m_dot = total_m_dot / (1.0 + mix_ratio)
            ox_m_dot = total_m_dot - fuel_m_dot

            r = self.R_EARTH
            velocity = 0.0
            elapsed_time = 0.0

            log_t_sec = [0.0]
            log_dist_km = [0.0]
            log_p = [total_prop_mass]

            running = True
            step = 0
            base_dt = 0.1

            while running and step < MAX_STEPS:
                curr_prop_mass = fuel_mass + ox_mass
                curr_mass = dry_mass + curr_prop_mass

                g_earth = GM_earth / (r**2)

                if fuel_mass > 0 and ox_mass > 0:
                    thrust = thrust_force
                    dt = base_dt
                    f_consumed = fuel_m_dot * dt
                    o_consumed = ox_m_dot * dt

                    if f_consumed > fuel_mass or o_consumed > ox_mass:
                        thrust = 0
                        fuel_mass = 0
                        ox_mass = 0
                    else:
                        fuel_mass -= f_consumed
                        ox_mass -= o_consumed
                else:
                    thrust = 0
                    altitude_m = r - self.R_EARTH
                    dt = min(86400.0, max(1.0, altitude_m / 1000000.0))

                acceleration = (thrust / curr_mass) - g_earth
                velocity += acceleration * dt
                r += velocity * dt
                elapsed_time += dt
                step += 1

                altitude_m = r - self.R_EARTH

                if velocity <= 0 and thrust == 0:
                    running = False

                if step % 20 == 0 or not running:
                    log_t_sec.append(elapsed_time)
                    log_dist_km.append(altitude_m / 1000.0)
                    log_p.append(curr_prop_mass)

            if elapsed_time > max_flight_time_sec:
                max_flight_time_sec = elapsed_time

            max_dist_km = max(log_dist_km) if log_dist_km else 0.0
            max_dist_au = (max_dist_km * 1000.0) / self.AU

            mass_efficiency = dry_mass / (dry_mass + total_prop_mass)
            score = max_dist_km * isp * mass_efficiency

            results.append({
                "name": name,
                "isp": isp,
                "max_dist_km": max_dist_km,
                "max_dist_au": max_dist_au,
                "score": score,
                "elapsed_time_sec": elapsed_time,
                "log_t_sec": log_t_sec,
                "dist_km": log_dist_km,
                "prop": log_p,
            })

            self.logger.info(
                f"推進剤[{name}]: 最高高度 {max_dist_km:,.1f} km, スコア: {score:,.0f}"
            )

        if max_flight_time_sec < 60:
            t_factor = 1.0
            self.x_label_str = "経過時間 (秒)"
        elif max_flight_time_sec < 3600:
            t_factor = 60.0
            self.x_label_str = "経過時間 (分)"
        elif max_flight_time_sec < 172800:
            t_factor = 3600.0
            self.x_label_str = "経過時間 (時間)"
        else:
            t_factor = 86400.0
            self.x_label_str = "経過時間 (日)"

        results.sort(key=lambda x: x["score"], reverse=True)

        self.result_text.delete("1.0", tk.END)

        header = "=" * 42 + "\n"
        header += f"   【 物理計算＆燃費スコア順位 (全{len(results)}種) 】\n"
        header += "=" * 42 + "\n"
        header += f"乾燥質量: {dry_mass}kg | 推進剤: {total_prop_mass}kg\n"
        header += f"推力: {thrust_force}N | 環境: 真空・地球重力\n"
        header += "-" * 42 + "\n"
        self.result_text.insert(tk.END, header)

        num_items = len(results)
        cmap = plt.get_cmap("tab20" if num_items <= 20 else "hsv")

        for rank, res in enumerate(results, 1):
            name = res["name"]
            isp = res["isp"]
            dist_km = res["max_dist_km"]
            dist_au = res["max_dist_au"]
            score = res["score"]
            sec = res["elapsed_time_sec"]
            t_sec = res["log_t_sec"]
            d = res["dist_km"]
            p = res["prop"]

            time_str = self.format_time(sec)
            t_scaled = [ts / t_factor for ts in t_sec]

            if dist_au >= 0.01:
                dist_str = f"{dist_km:,.0f} km ({dist_au:.3f} AU)"
            else:
                dist_str = f"{dist_km:,.1f} km"

            label_text = f"[{rank:>2}位] {name} (Score:{score:,.0f})"

            rank_detail = (
                f"【第 {rank} 位】 {name}\n"
                f"  - 総合スコア: {score:,.0f} pt\n"
                f"  - 最高到達高度: {dist_str}\n"
                f"  - 燃焼・到達時間: {time_str}\n"
                f"  - 比推力 (Isp): {isp} sec\n"
                f"----------------------------------------\n"
            )
            self.result_text.insert(tk.END, rank_detail)
            self.legend_listbox.insert(tk.END, label_text)

            color_val = (
                (rank - 1) / 20.0
                if num_items <= 20
                else (rank - 1) / float(num_items)
            )
            line_color = cmap(color_val)

            self.ax1.plot(t_scaled, d, linewidth=1.4, color=line_color)
            self.ax2.plot(t_scaled, p, color=line_color, linewidth=1.0)

            # 識別テキストラベル注釈
            if rank <= 8 or rank % max(1, num_items // 10) == 0:
                if len(t_scaled) > 0:
                    mid_idx = len(t_scaled) // 2
                    self.ax1.annotate(
                        f"{rank}.{name}",
                        xy=(t_scaled[mid_idx], d[mid_idx]),
                        fontsize=7,
                        color=line_color,
                        fontweight="bold",
                        alpha=0.9,
                    )

        self.ax1.set_ylabel("到達高度 (km)", fontsize=10)
        self.ax1.set_title(
            "【NASA物理モデル】真空・万有引力下でのロケット高度推移",
            fontsize=11,
            fontweight="bold",
        )
        self.ax1.grid(True, linestyle=":", alpha=0.6)

        self.ax2.set_xlabel(self.x_label_str, fontsize=10)
        self.ax2.set_ylabel("残り推進剤 (kg)", fontsize=10)
        self.ax2.grid(True, linestyle=":", alpha=0.6)

        self.fig.tight_layout()
        self.canvas.draw()

        calc_time = time.time() - start_time
        self.lbl_status.config(
            text=f"✅ 全{num_items}素材の物理・燃費スコア計算完了 ({calc_time:.2f}秒)",
            foreground="green",
        )
        self.logger.info("シミュレーション計算および描画処理が正常完了しました")

    # ----- 個別グラフ保存機能 -----
    def save_graph_altitude(self):
        """高度グラフのみ切り出して保存"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="高度グラフのみ保存",
            initialfile="altitude_graph.png",
        )
        if filepath:
            # ax1 (高度) の領域のみ境界ボックス計算して保存
            extent = (
                self.ax1.get_window_extent().transformed(
                    self.fig.dpi_scale_trans.inverted()
                )
            )
            self.fig.savefig(
                filepath, dpi=300, bbox_inches=extent.expanded(1.2, 1.25)
            )
            self.logger.info(f'高度グラフを保存しました: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"高度グラフ画像を保存しました:\n{filepath}"
            )

    def save_graph_propellant(self):
        """残り推進剤グラフのみ切り出して保存"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="残り推進剤グラフのみ保存",
            initialfile="propellant_graph.png",
        )
        if filepath:
            extent = (
                self.ax2.get_window_extent().transformed(
                    self.fig.dpi_scale_trans.inverted()
                )
            )
            self.fig.savefig(
                filepath, dpi=300, bbox_inches=extent.expanded(1.2, 1.25)
            )
            self.logger.info(f'残り推進剤グラフを保存しました: "{filepath}"')
            messagebox.showinfo(
                "保存完了",
                f"残り推進剤グラフ画像を保存しました:\n{filepath}",
            )

    def save_graph_all(self):
        """全体グラフを保存"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="全体グラフ画像を保存",
            initialfile="rocket_full_graph.png",
        )
        if filepath:
            self.fig.savefig(filepath, dpi=300, bbox_inches="tight")
            self.logger.info(f'全体グラフ画像を保存しました: "{filepath}"')
            messagebox.showinfo(
                "保存完了", f"全体グラフ画像を保存しました:\n{filepath}"
            )

    def on_safe_exit(self):
        self.is_running = False
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
        try:
            self.logger.info("アプリケーションを安全に終了します")
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SpaceRocketSimulatorApp(root)
    root.mainloop()
