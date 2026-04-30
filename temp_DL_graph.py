# multi_dl_graph.py

import numpy as np

def plot_all_dl(ax, arrays, title="Temperature"):

    colors = ['#22D3EE', '#4ADE80', '#F87171', '#FACC15', '#A78BFA', '#FB7185']

    ax.clear()   # IMPORTANT → avoid overlap

    all_x = []

    for i, arr in enumerate(arrays):

        if not arr:
            continue

        y = arr[-20:]
        x = list(range(len(y)))

        all_x.extend(x)

        ax.plot(x, y, color=colors[i % len(colors)], linewidth=2, label=f"DL{i+1}")

    # ───────── AXIS ─────────
    ax.set_title(title)
    ax.set_xlabel("Time Index (Last 20)")
    ax.set_ylabel("Temperature (°C)")

    ax.grid(True)
    ax.legend()

    # 🔥 FIX X-AXIS PROPERLY
    if all_x:
        ax.set_xticks(np.arange(min(all_x), max(all_x) + 1, 1))

    # threshold
    ax.axhline(y=50, color='red', linestyle='--', linewidth=1)