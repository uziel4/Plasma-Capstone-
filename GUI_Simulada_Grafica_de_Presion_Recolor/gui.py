import tkinter as tk
from collections import deque

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from simulation import VacuumSimulator
from utils import pressure_to_voltage_972b, format_pressure


class VacuumGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("972B Vacuum Monitor")
        self.root.geometry("1500x720")
        self.root.configure(bg="#06111F")

        self.time_counter = 0
        self.max_points = 80

        self.time_data = deque(maxlen=self.max_points)
        self.pressure_data = deque(maxlen=self.max_points)

        self.simulator = VacuumSimulator()

        self.build_ui()
        self.update_data()

    def build_ui(self):
        self.main = tk.Frame(self.root, bg="#06111F")
        self.main.pack(fill="both", expand=True)

        self.cards_frame = tk.Frame(self.main, bg="#06111F")
        self.cards_frame.pack(fill="x", padx=12, pady=(8, 10))

        self.voltage_value = self.create_card(
            self.cards_frame,
            "972B Analog Voltage",
            "6.9404 V",
            "Voltage acquired from DAQC2plate A0"
        )

        self.pressure_value = self.create_card(
            self.cards_frame,
            "Calculated Pressure",
            "760.00 Torr",
            "P(Torr) = 10^(2V - 11)"
        )

        self.runtime_value = self.create_card(
            self.cards_frame,
            "Runtime",
            "0 s",
            "Acquisition runtime"
        )

        graph_outer = tk.Frame(
            self.main,
            bg="#0B1528",
            highlightbackground="#123B5A",
            highlightthickness=1
        )
        graph_outer.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tk.Label(
            graph_outer,
            text="Vacuum Pressure vs Time",
            font=("Arial", 11, "bold"),
            fg="#C4B5FD",
            bg="#0B1528"
        ).pack(anchor="w", padx=10, pady=(10, 4))

        graph_frame = tk.Frame(graph_outer, bg="#020817")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        self.fig = Figure(figsize=(14, 4.5), dpi=100)
        self.fig.patch.set_facecolor("#020817")

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#020817")

        self.ax.set_title(
            "Vacuum Pressure vs Time",
            color="#E0F2FE",
            fontsize=8,
            fontweight="bold"
        )

        self.ax.set_xlabel("Time (s)", color="#BFEFFF", fontsize=8)
        self.ax.set_ylabel("Pressure (Torr)", color="#BFEFFF", fontsize=8)

        self.ax.set_yscale("log")
        self.ax.set_ylim(1e-8, 1000)
        self.ax.set_xlim(0, self.max_points)

        self.ax.grid(True, which="both", color="#1F2A44", alpha=0.7)
        self.ax.tick_params(axis="x", colors="#9CA3AF", labelsize=7)
        self.ax.tick_params(axis="y", colors="#9CA3AF", labelsize=7)

        for spine in self.ax.spines.values():
            spine.set_color("#CBD5E1")

        self.line, = self.ax.plot(
            [],
            [],
            color="#22D3EE",
            linewidth=2.5,
            marker="o",
            markersize=3
        )

        self.current_point, = self.ax.plot(
            [],
            [],
            marker="o",
            color="#FFFFFF",
            markersize=5
        )

        self.annotation = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(8, 8),
            textcoords="offset points",
            color="#67E8F9",
            fontsize=7,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.25",
                fc="#083344",
                ec="#22D3EE",
                alpha=0.85
            )
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_card(self, parent, title, value, subtitle):
        card = tk.Frame(
            parent,
            bg="#0B1020",
            height=115,
            highlightbackground="#164E63",
            highlightthickness=1
        )
        card.pack(side="left", expand=True, fill="x", padx=6)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Arial", 11, "bold"),
            fg="#C4B5FD",
            bg="#0B1020"
        ).pack(anchor="w", padx=14, pady=(14, 6))

        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 18, "bold"),
            fg="#22D3EE",
            bg="#0B1020"
        )
        value_label.pack(anchor="w", padx=14)

        tk.Label(
            card,
            text=subtitle,
            font=("Arial", 8),
            fg="#67E8F9",
            bg="#0B1020"
        ).pack(anchor="w", padx=14, pady=(8, 0))

        return value_label

    def update_data(self):
        self.time_counter += 1

        pressure = self.simulator.simulate_vacuum_process()
        voltage = pressure_to_voltage_972b(pressure)

        self.time_data.append(self.time_counter)
        self.pressure_data.append(pressure)

        self.voltage_value.config(text=f"{voltage:.4f} V")
        self.pressure_value.config(text=format_pressure(pressure))
        self.runtime_value.config(text=f"{self.time_counter} s")

        x_data = list(self.time_data)
        y_data = list(self.pressure_data)

        self.line.set_data(x_data, y_data)

        if x_data and y_data:
            self.current_point.set_data([x_data[-1]], [y_data[-1]])

            self.annotation.xy = (x_data[-1], y_data[-1])
            self.annotation.set_text(
                f"X: {x_data[-1]} s\nY: {format_pressure(y_data[-1])}"
            )

        if self.time_counter > self.max_points:
            self.ax.set_xlim(
                self.time_counter - self.max_points,
                self.time_counter
            )

        self.canvas.draw_idle()
        self.root.after(1000, self.update_data)