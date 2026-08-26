#!/usr/bin/env python3
"""Control gráfico de dos Pi-Plates RELAYplate2 (addresses 0 y 1)."""

import tkinter as tk
from tkinter import messagebox

try:
    import piplates.RELAYplate2 as RELAY2
except ImportError as exc:
    raise SystemExit(
        "No se encontro la libreria Pi-Plates. Instalala con: "
        "python3 -m pip install Pi-Plates"
    ) from exc


PLATE_ADDRESSES = (0, 1)
RELAYS_PER_PLATE = 8
COLOR_OFF = "#374151"
COLOR_ON = "#16a34a"


class RelayControlApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Control de dos RELAYplate2")
        self.root.configure(bg="#111827")
        self.root.resizable(False, False)

        self.states = {
            (address, relay): False
            for address in PLATE_ADDRESSES
            for relay in range(1, RELAYS_PER_PLATE + 1)
        }
        self.buttons: dict[tuple[int, int], tk.Button] = {}

        self._verify_plates()
        self._build_interface()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _verify_plates(self) -> None:
        for address in PLATE_ADDRESSES:
            board_id = RELAY2.getID(address)
            if "RELAYplate2" not in str(board_id):
                raise RuntimeError(
                    f"No se encontro una RELAYplate2 en address {address}: {board_id!r}"
                )
            state_mask = RELAY2.relaySTATE(address)
            for relay in range(1, RELAYS_PER_PLATE + 1):
                self.states[(address, relay)] = bool(
                    state_mask & (1 << (relay - 1))
                )

    def _build_interface(self) -> None:
        title = tk.Label(
            self.root,
            text="CONTROL DE RELAY PLATES",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#111827",
        )
        title.pack(padx=24, pady=(20, 10))

        plates_frame = tk.Frame(self.root, bg="#111827")
        plates_frame.pack(padx=20, pady=10)

        for column, address in enumerate(PLATE_ADDRESSES):
            plate_frame = tk.LabelFrame(
                plates_frame,
                text=f"RELAYplate2 - Address {address}",
                font=("Arial", 13, "bold"),
                fg="white",
                bg="#1f2937",
                padx=12,
                pady=12,
            )
            plate_frame.grid(row=0, column=column, padx=10, pady=5)

            for relay in range(1, RELAYS_PER_PLATE + 1):
                is_on = self.states[(address, relay)]
                button = tk.Button(
                    plate_frame,
                    text=f"Relé {relay}\n{'ENCENDIDO' if is_on else 'APAGADO'}",
                    width=15,
                    height=3,
                    font=("Arial", 11, "bold"),
                    fg="white",
                    bg=COLOR_ON if is_on else COLOR_OFF,
                    activeforeground="white",
                    activebackground=COLOR_ON if is_on else COLOR_OFF,
                    command=lambda a=address, r=relay: self.toggle_relay(a, r),
                )
                button.grid(row=(relay - 1) // 2, column=(relay - 1) % 2, padx=6, pady=6)
                self.buttons[(address, relay)] = button

        self.status = tk.Label(
            self.root,
            text="Seleccione el relé que desea controlar.",
            font=("Arial", 11),
            fg="#d1d5db",
            bg="#111827",
        )
        self.status.pack(pady=(5, 10))

        all_off_button = tk.Button(
            self.root,
            text="APAGAR TODOS LOS RELÉS",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#dc2626",
            activebackground="#b91c1c",
            activeforeground="white",
            command=self.all_off,
        )
        all_off_button.pack(fill="x", padx=30, pady=(0, 20))

    def toggle_relay(self, address: int, relay: int) -> None:
        key = (address, relay)
        new_state = not self.states[key]

        try:
            if new_state:
                RELAY2.relayON(address, relay)
            else:
                RELAY2.relayOFF(address, relay)
        except Exception as exc:
            messagebox.showerror("Error de comunicación", str(exc))
            return

        self.states[key] = new_state
        self._update_button(address, relay)
        state_text = "encendido" if new_state else "apagado"
        self.status.config(
            text=f"Relé {relay} de address {address}: {state_text}."
        )

    def _update_button(self, address: int, relay: int) -> None:
        state = self.states[(address, relay)]
        self.buttons[(address, relay)].config(
            text=f"Relé {relay}\n{'ENCENDIDO' if state else 'APAGADO'}",
            bg=COLOR_ON if state else COLOR_OFF,
            activebackground=COLOR_ON if state else COLOR_OFF,
        )

    def all_off(self, show_error: bool = True) -> None:
        try:
            for address in PLATE_ADDRESSES:
                RELAY2.relayALL(address, 0)
        except Exception as exc:
            if show_error:
                messagebox.showerror("Error de comunicación", str(exc))
            return

        for key in self.states:
            self.states[key] = False
            self._update_button(*key)
        self.status.config(text="Todos los relés están apagados.")

    def close(self) -> None:
        self.all_off(show_error=False)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        RelayControlApp(root)
    except Exception as exc:
        root.withdraw()
        messagebox.showerror("No se pudo iniciar", str(exc))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
