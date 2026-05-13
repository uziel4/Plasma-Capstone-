def set_button_state(button, active, colors):
    button.config(
        highlightbackground=colors["red"] if active else colors["white"],
        highlightcolor=colors["red"] if active else colors["white"]
    )