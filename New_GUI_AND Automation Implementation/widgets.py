def set_button_state(button, active, colors):
    button.config(
        highlightbackground=colors["red"] if active else colors["grid"],
        highlightcolor=colors["red"] if active else colors["grid"]
    )