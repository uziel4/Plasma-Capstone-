import matplotlib
matplotlib.use("TkAgg")

import tkinter as tk
from tkinter import ttk
import time
import math
import customtkinter as ctk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import COLORS, APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from simulation import ReactorSimulation

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PlasmaReactorGUI:
    def __init__(self, root):
        self.root = root
        self.colors = COLORS
        self.sim = ReactorSimulation()

        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=self.colors["background"])

        self.auto_active = False
        self.hv_active = False
        self.hold_mode = False

        self.roughing_active = False
        self.turbo_active = False
        self.mass_flow_active = False

        self.hv_start_time = None
        self.hv_total_seconds = 30

        self.graph_time = 0.0
        self.x_data = []
        self.y_data = []

        self.build_ui()
        self.update_loop()

    def panel(self, parent, bg=None, border=None, thickness=1):
        return ctk.CTkFrame(
            parent,
            fg_color=bg or self.colors["panel"],
            border_color=border or self.colors["grid"],
            border_width=thickness,
            corner_radius=12
        )

    def label(self, parent, text, size=18, bg=None, weight="bold", color=None):
        return ctk.CTkLabel(
            parent,
            text=text,
            text_color=color or self.colors["white"],
            font=("Arial", size, weight)
        )

    def readout(self, parent, variable, size=22):
        return ctk.CTkLabel(
            parent,
            textvariable=variable,
            text_color=self.colors["black"],
            font=("Arial", size, "bold"),
            fg_color=self.colors["input"],
            corner_radius=8,
            padx=10,
            pady=10
        )

    def entry_box(self, parent, variable, size=22):
        return ctk.CTkEntry(
            parent,
            textvariable=variable,
            text_color=self.colors["black"],
            fg_color=self.colors["input"],
            border_color=self.colors["grid"],
            border_width=1,
            font=("Arial", size, "bold"),
            justify="center",
            corner_radius=8
        )

    def action_button(self, parent, text, command, size=22):
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            text_color=self.colors["white"],
            font=("Arial", size, "bold"),
            corner_radius=10,
            height=44,
            border_width=2,
            border_color=self.colors["grid"]
        )
        
        return button

    def set_button_active(self, button, active):
        if active:
            button.configure(
                fg_color=self.colors["button_active"],
                border_color=self.colors["red"]
            )
        else:
            button.configure(
                fg_color=self.colors["button"],
                border_color=self.colors["grid"]
            )

    def build_ui(self):
        self.main = ctk.CTkFrame(
            self.root,
            fg_color=self.colors["background"],
            border_color=self.colors["grid"],
            border_width=1,
            corner_radius=15
        )
        self.main.pack(fill="both", expand=True, padx=14, pady=14)

        self.main.grid_columnconfigure(0, weight=0, minsize=470)
        self.main.grid_columnconfigure(1, weight=1, minsize=520)
        self.main.grid_columnconfigure(2, weight=1, minsize=520)

        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=0)
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(
            self.main,
            text=APP_TITLE,
            text_color=self.colors["white"],
            font=("Arial", 27, "bold")
        )
        title.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(10, 18))

        self.build_auto_panel()
        self.build_hv_panel()
        self.build_timer_panel()
        self.build_manual_panel()
        self.build_chamber_panel()
        self.build_roughing_panel()
        self.build_environment_panel()

    def build_auto_panel(self):
        panel = self.panel(self.main, thickness=1)
        panel.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        self.label(panel, "AUTO", 28).pack(pady=(10, 10))

        button_frame = ctk.CTkFrame(panel, fg_color=self.colors["panel"], corner_radius=10)
        button_frame.pack(fill="x", padx=18)

        self.auto_start_btn = self.action_button(button_frame, "START", self.start_auto, size=21)
        self.auto_start_btn.pack(side="left", expand=True, fill="x", padx=6)

        self.auto_stop_btn = self.action_button(button_frame, "STOP", self.stop_auto, size=21)
        self.auto_stop_btn.pack(side="left", expand=True, fill="x", padx=6)

        self.reset_btn = self.action_button(panel, "RESET", self.reset_system, size=20)
        self.reset_btn.pack(fill="x", padx=24, pady=(14, 10))

        self.label(panel, "TARGET VACUUM (mTorr)", 17, color=self.colors["muted"]).pack(pady=(8, 4))

        self.target_vacuum_var = tk.StringVar(value="1.000")

        self.entry_box(panel, self.target_vacuum_var, size=24).pack(
            fill="x",
            padx=20,
            pady=(0, 18),
            ipady=8
        )

    def build_hv_panel(self):
        panel = self.panel(self.main)
        panel.grid(row=1, column=1, sticky="nsew", padx=12, pady=8)

        self.label(panel, "HIGH VOLTAGE SOURCE", 20).pack(
            fill="x",
            pady=(10, 10)
        )

        self.label(panel, "VOLTAGE (V)", 15, color=self.colors["muted"]).pack(
            pady=(8, 4)
        )

        self.hv_voltage_var = tk.StringVar(value="0.00")
        self.hv_voltage_applied = False

        self.entry_box(panel, self.hv_voltage_var, size=25).pack(
            fill="x",
            padx=14,
            pady=(0, 14),
            ipady=10
        )

        button_frame = ctk.CTkFrame(panel, fg_color=self.colors["panel"], corner_radius=10)
        button_frame.pack(fill="x", padx=14, pady=(0, 14))

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.hv_apply_btn = self.action_button(button_frame, "APPLY", self.apply_hv_voltage, size=21)
        self.hv_apply_btn.grid(row=0, column=0, padx=6, sticky="ew")

        self.hv_voltage_reset_btn = self.action_button(button_frame, "RESET", self.reset_hv_voltage, size=21)
        self.hv_voltage_reset_btn.grid(row=0, column=1, padx=6, sticky="ew")

    def build_timer_panel(self):
        panel = self.panel(self.main)
        panel.grid(row=1, column=2, sticky="nsew", padx=12, pady=8)

        self.label(panel, "HIGH VOLTAGE TIMER", 20).pack(
            fill="x",
            pady=(10, 10)
        )

        self.label(panel, "TIMER (HH:MM:SS)", 15, color=self.colors["muted"]).pack(
            pady=(8, 4)
        )

        self.timer_var = tk.StringVar(value="00:00:30")

        self.entry_box(panel, self.timer_var, size=25).pack(
            fill="x",
            padx=14,
            pady=(0, 14),
            ipady=10
        )

        button_frame = ctk.CTkFrame(panel, fg_color=self.colors["panel"], corner_radius=10)
        button_frame.pack(fill="x", padx=14, pady=(0, 14))

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.hv_toggle_btn = self.action_button(button_frame, "START", self.toggle_hv, size=21)
        self.hv_toggle_btn.grid(row=0, column=0, padx=6, sticky="ew")

        self.hv_reset_btn = self.action_button(button_frame, "RESET", self.reset_hv_timer, size=21)
        self.hv_reset_btn.grid(row=0, column=1, padx=6, sticky="ew")

    def build_manual_panel(self):
        panel = ctk.CTkFrame(self.main, fg_color=self.colors["background"], corner_radius=0)
        panel.grid(row=2, column=0, rowspan=2, sticky="nsew", padx=16, pady=(30, 16))

        title = ctk.CTkLabel(
            panel,
            text="MANUAL CONTROL",
            text_color=self.colors["white"],
            font=("Arial", 25, "bold")
        )
        title.pack(fill="x", pady=(0, 24))

        self.roughing_btn = self.manual_button(panel, "⚙", "Roughing\nPump", self.toggle_roughing)
        self.turbo_btn = self.manual_button(panel, "◉", "Turbomolecular\nPump", self.toggle_turbo)
        self.mass_flow_btn = self.manual_button(panel, "≋", "Mass Flow", self.toggle_mass_flow)

    def manual_button(self, parent, icon, text, command):
        frame = ctk.CTkFrame(
            parent,
            fg_color=self.colors["panel_light"],
            border_color=self.colors["grid"],
            border_width=1,
            corner_radius=12,
            cursor="hand2"
        )
        frame.pack(fill="x", pady=10)

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=0)

        icon_label = ctk.CTkLabel(
            frame,
            text=icon,
            text_color=self.colors["graph_line"],
            font=("Arial", 42, "bold"),
            width=4
        )
        icon_label.grid(row=0, column=0, padx=(16, 6), pady=14)

        text_label = ctk.CTkLabel(
            frame,
            text=text,
            text_color=self.colors["white"],
            font=("Arial", 21, "bold"),
            justify="center"
        )
        text_label.grid(row=0, column=1, sticky="ew")

        status = tk.Canvas(
            frame,
            width=50,
            height=50,
            bg=self.colors["panel_light"],
            highlightthickness=0
        )
        status.grid(row=0, column=2, padx=(6, 26))

        light = status.create_oval(
            8,
            8,
            42,
            42,
            fill=self.colors["gray"],
            outline=self.colors["background"],
            width=3
        )

        frame.status = status
        frame.light = light
        frame.icon_label = icon_label
        frame.text_label = text_label

        def click(event=None):
            command()

        for widget in [frame, icon_label, text_label, status]:
            widget.bind("<Button-1>", click)

        return frame

    def build_chamber_panel(self):
        panel = self.panel(self.main)
        panel.grid(row=2, column=1, rowspan=2, sticky="nsew", padx=12, pady=(8, 16))

        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        self.label(panel, "CHAMBER VACUUM", 19).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 10)
        )

        self.chamber_var = tk.StringVar(value="1.450 × 10⁻¹ Torr")
        self.window_var = tk.StringVar(value="LIVE 60s")

        ctk.CTkLabel(
            panel,
            textvariable=self.chamber_var,
            text_color=self.colors["white"],
            font=("Arial", 18, "bold"),
            fg_color=self.colors["panel_light"],
            corner_radius=8,
            padx=6,
            pady=12
        ).grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=4)

        self.readout(panel, self.window_var, size=18).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(6, 14),
            pady=4
        )

        self.build_graph(panel)

    def build_graph(self, parent):
        self.fig = Figure(
            figsize=(5.4, 3.7),
            dpi=100,
            facecolor=self.colors["panel"]
        )

        self.ax = self.fig.add_subplot(111)

        self.ax.set_facecolor(self.colors["background"])
        self.ax.set_yscale("log")
        self.ax.set_xlim(0, 60)
        self.ax.set_ylim(1e-6, 2e-1)

        self.ax.grid(True, color=self.colors["grid"], linewidth=0.8, alpha=0.85)
        self.ax.tick_params(colors=self.colors["white"], labelsize=11)

        for spine in self.ax.spines.values():
            spine.set_color(self.colors["grid"])

        self.ax.set_xticks([0, 15, 30, 45, 60])
        self.ax.set_xticklabels(["0s", "15s", "30s", "45s", "60s"])

        self.ax.set_yticks([1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6])
        self.ax.set_yticklabels([
            "1×10⁻¹",
            "1×10⁻²",
            "1×10⁻³",
            "1×10⁻⁴",
            "1×10⁻⁵",
            "1×10⁻⁶"
        ])

        self.ax.set_xlabel("Time", color=self.colors["muted"], fontsize=11)
        self.ax.set_ylabel("Pressure (Torr)", color=self.colors["muted"], fontsize=11)

        self.line, = self.ax.plot(
            [],
            [],
            color=self.colors["graph_line"],
            linewidth=2.8,
            marker="o",
            markersize=3.5,
            markerfacecolor=self.colors["graph_marker"],
            markeredgewidth=0
        )

        self.fig.tight_layout(pad=1.4)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=16,
            pady=(16, 18)
        )

    def build_roughing_panel(self):
        panel = self.panel(self.main)
        panel.grid(row=2, column=2, sticky="nsew", padx=12, pady=(8, 8))

        panel.grid_columnconfigure(0, weight=1)

        self.label(panel, "ROUGHING LINE VACUUM", 19).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(14, 12)
        )

        self.roughing_var = tk.StringVar(value="1.450 × 10⁻¹ Torr")

        self.readout(panel, self.roughing_var, size=20).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=14,
            pady=(0, 12)
        )

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Vacuum.Horizontal.TProgressbar",
            background=self.colors["graph_line"],
            troughcolor=self.colors["background"],
            bordercolor=self.colors["grid"],
            lightcolor=self.colors["graph_line"],
            darkcolor=self.colors["graph_line"]
        )

        self.bar = ttk.Progressbar(
            panel,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            style="Vacuum.Horizontal.TProgressbar"
        )
        self.bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 8), ipady=16)

        self.bar_text_var = tk.StringVar(value="0% TO TARGET")

        bar_label = ctk.CTkLabel(
            panel,
            textvariable=self.bar_text_var,
            fg_color=self.colors["panel_light"],
            text_color=self.colors["white"],
            font=("Arial", 23, "bold"),
            corner_radius=8,
            pady=10
        )
        bar_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))

        self.status_var = tk.StringVar(value="SYSTEM READY")

        status_label = ctk.CTkLabel(
            panel,
            textvariable=self.status_var,
            fg_color=self.colors["panel"],
            text_color=self.colors["white"],
            font=("Arial", 16, "bold"),
            pady=8
        )
        status_label.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 14))

    def build_environment_panel(self):
        panel = self.panel(self.main)
        panel.grid(row=3, column=2, sticky="nsew", padx=12, pady=(8, 16))

        panel.grid_columnconfigure(0, weight=1)

        self.label(panel, "ENVIRONMENTAL DATA", 15).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(12, 6)
        )

        ctk.CTkFrame(panel, fg_color=self.colors["grid"], height=1, corner_radius=0).grid(row=1, column=0, sticky="ew")

        self.env_var = tk.StringVar()

        ctk.CTkLabel(
            panel,
            textvariable=self.env_var,
            fg_color=self.colors["panel"],
            text_color=self.colors["white"],
            font=("Arial", 17, "bold"),
            justify="left"
        ).grid(row=2, column=0, sticky="nsew", padx=24, pady=18)

    def start_auto(self):
        self.auto_active = True
        self.hold_mode = False

        self.roughing_active = True
        self.mass_flow_active = False

        # Turbo only starts if target is 0.100 mTorr (1×10⁻⁴ Torr) or lower
        target_value = self.target_vacuum_var.get()
        target_torr = self.sim.parse_target_mtorr(target_value)
        self.turbo_active = target_torr <= 1e-4

        self.status_var.set("AUTO PUMPDOWN ACTIVE")

        self.set_button_active(self.auto_start_btn, True)
        self.update_manual_indicators()

    def stop_auto(self):
        self.auto_active = False
        self.hold_mode = False

        self.roughing_active = False
        self.turbo_active = False
        self.mass_flow_active = False

        self.status_var.set("SYSTEM STOPPED")

        self.set_button_active(self.auto_start_btn, False)
        self.set_button_active(self.auto_stop_btn, True)

        self.update_manual_indicators()

        self.root.after(
            250,
            lambda: self.set_button_active(self.auto_stop_btn, False)
        )

    def reset_system(self):
        self.auto_active = False
        self.hv_active = False
        self.hold_mode = False

        self.roughing_active = False
        self.turbo_active = False
        self.mass_flow_active = False

        self.sim.reset()

        self.graph_time = 0.0
        self.x_data.clear()
        self.y_data.clear()

        self.target_vacuum_var.set("1.000")
        self.timer_var.set("00:00:30")

        self.status_var.set("SYSTEM RESET")

        self.set_button_active(self.auto_start_btn, False)
        self.set_button_active(self.hv_toggle_btn, False)
        self.hv_toggle_btn.configure(text="START")
        self.hv_voltage_var.set("0.00")
        self.hv_voltage_applied = False
        self.hv_apply_btn.configure(text="APPLY")
        self.set_button_active(self.hv_apply_btn, False)

        self.update_manual_indicators()

    def start_hv(self):
        self.hv_active = True
        self.hv_start_time = time.time()
        self.hv_total_seconds = self.parse_time(self.timer_var.get())

        self.set_button_active(self.hv_toggle_btn, True)
        self.hv_toggle_btn.configure(text="STOP")

    def stop_hv(self):
        self.hv_active = False

        self.set_button_active(self.hv_toggle_btn, False)
        self.hv_toggle_btn.configure(text="START")

    def toggle_hv(self):
        if self.hv_active:
            self.stop_hv()
        else:
            self.start_hv()

    def reset_hv_timer(self):
        self.hv_active = False
        self.hv_start_time = None
        self.hv_total_seconds = 30

        self.timer_var.set("00:00:30")
        self.set_button_active(self.hv_toggle_btn, False)
        self.hv_toggle_btn.configure(text="START")

    def apply_hv_voltage(self):
        try:
            voltage = float(self.hv_voltage_var.get())
            if voltage >= 0:
                self.hv_voltage_applied = True
                self.hv_apply_btn.configure(text="APPLIED")
                self.set_button_active(self.hv_apply_btn, True)
        except ValueError:
            pass

    def reset_hv_voltage(self):
        self.hv_voltage_var.set("0.00")
        self.hv_voltage_applied = False
        self.hv_apply_btn.configure(text="APPLY")
        self.set_button_active(self.hv_apply_btn, False)

    def toggle_roughing(self):
        self.roughing_active = not self.roughing_active
        self.update_manual_indicators()

    def toggle_turbo(self):
        self.turbo_active = not self.turbo_active
        self.update_manual_indicators()

    def toggle_mass_flow(self):
        self.mass_flow_active = not self.mass_flow_active
        self.update_manual_indicators()

    def update_manual_indicators(self):
        self.set_manual_state(self.roughing_btn, self.roughing_active)
        self.set_manual_state(self.turbo_btn, self.turbo_active)
        self.set_manual_state(self.mass_flow_btn, self.mass_flow_active)

    def set_manual_state(self, frame, active):
        fg_color = self.colors["button_active"] if active else self.colors["panel_light"]
        border_color = self.colors["red"] if active else self.colors["grid"]

        frame.configure(
            fg_color=fg_color,
            border_color=border_color
        )

        frame.status.config(bg=fg_color)

        frame.status.itemconfig(
            frame.light,
            fill=self.colors["green"] if active else self.colors["gray"]
        )

    def parse_time(self, value):
        try:
            h, m, s = value.split(":")
            total = int(h) * 3600 + int(m) * 60 + int(s)
            return max(1, total)
        except Exception:
            return 30

    def format_time(self, seconds):
        seconds = max(0, int(seconds))

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60

        return f"{h:02d}:{m:02d}:{s:02d}"

    def superscript_number(self, number):
        normal = "0123456789-+"
        super_chars = "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺"

        table = str.maketrans(normal, super_chars)
        return str(number).translate(table)

    def format_pressure(self, value):
        if value <= 0:
            return "0 Torr"

        exponent = int(math.floor(math.log10(abs(value))))
        coefficient = value / (10 ** exponent)

        exponent_text = self.superscript_number(exponent)

        return f"{coefficient:0.3f} × 10{exponent_text} Torr"

    def simulate_pressure_voltage(self):
        pressure = max(self.sim.chamber_torr, 1e-6)
        voltage = min(10.0, max(0.0, 10.0 + 1.25 * math.log10(pressure)))
        return voltage

    def update_loop(self):
        target_value = self.target_vacuum_var.get()
        target_torr = self.sim.parse_target_mtorr(target_value)
        current_torr = self.sim.chamber_torr

        if self.auto_active:
            if not self.hold_mode:
                if self.sim.target_reached(target_value):
                    self.hold_mode = True

                    self.roughing_active = False
                    self.turbo_active = False
                    self.mass_flow_active = False

                    self.status_var.set("TARGET REACHED - HOLD MODE")
                else:
                    # Roughing always active during pumpdown
                    self.roughing_active = True
                    
                    # Turbo stays active if target requires it (≤0.100 mTorr)
                    if target_torr <= 1e-4:
                        self.turbo_active = True
                        self.status_var.set("TURBO + ROUGHING ACTIVE - FINE VACUUM")
                    else:
                        self.turbo_active = False
                        self.status_var.set("ROUGHING PUMP - PUMPDOWN ACTIVE")

            else:
                # Hold mode: maintain target vacuum
                self.turbo_active = False  # Turbo off during hold mode

                # Mass flow only activates if vacuum dropped below target (vacuum is better/lower)
                if current_torr < target_torr:
                    self.mass_flow_active = True
                    self.roughing_active = False
                    self.status_var.set("MASS FLOW ACTIVE - REGULATING VACUUM")
                else:
                    # Vacuum is worse than target, need to pump more
                    self.mass_flow_active = False
                    self.roughing_active = True
                    self.status_var.set("VACUUM LOSS - ROUGHING ACTIVE")

            self.update_manual_indicators()

        self.sim.update(
            roughing=self.roughing_active,
            turbo=self.turbo_active,
            hold=self.hold_mode,
            target_mtorr=target_value
        )

        self.chamber_var.set(self.format_pressure(self.sim.chamber_torr))
        self.roughing_var.set(self.format_pressure(self.sim.roughing_torr))

        progress = self.sim.target_progress_percent(target_value)
        self.bar["value"] = progress

        if self.hold_mode:
            self.bar_text_var.set("HOLDING TARGET")
        else:
            self.bar_text_var.set(f"{progress:0.0f}% TO TARGET")

        self.env_var.set(
            f"TEMPERATURE  : {self.sim.temperature:0.1f} C\n"
            f"PRESSURE        : {self.sim.pressure_mbar:0.0f} mbar\n"
            f"TORR            : {self.sim.torr_from_mbar():0.3f} Torr\n"
            f"HUMIDITY        : {self.sim.humidity:0.0f}%"
        )

        self.update_hv_timer()
        self.update_graph()

        self.root.after(250, self.update_loop)

    def update_hv_timer(self):
        if self.hv_active and self.hv_start_time is not None:
            elapsed = int(time.time() - self.hv_start_time)
            remaining = self.hv_total_seconds - elapsed

            self.timer_var.set(self.format_time(remaining))

            if remaining <= 0:
                self.stop_hv()

    def update_graph(self):
        self.graph_time += 0.25

        self.x_data.append(self.graph_time)
        self.y_data.append(max(self.sim.chamber_torr, 1e-6))

        max_points = 240

        if len(self.x_data) > max_points:
            self.x_data = self.x_data[-max_points:]
            self.y_data = self.y_data[-max_points:]

        xmin = max(0, self.graph_time - 60)
        display_x = [x - xmin for x in self.x_data]

        self.line.set_data(display_x, self.y_data)

        self.ax.set_xlim(0, 60)

        current_min = min(self.y_data)
        current_max = max(self.y_data)

        y_low = max(1e-6, current_min * 0.55)
        y_high = min(2e-1, current_max * 1.45)

        if y_high <= y_low:
            y_high = y_low * 10

        self.ax.set_ylim(y_low, y_high)

        self.canvas.draw_idle()