import matplotlib.pyplot as plt

plt.ion()

fig, axs = plt.subplots(2, 2, figsize=(14, 8))

def Temp_graph(front_start, front_end, rear_start, rear_end):

    for ax in axs.flat:
        ax.clear()

    colors = plt.cm.tab10.colors

    # FRONT START
    for i, arr in enumerate(front_start):
        if arr:
            axs[0, 0].plot(arr, label=f"Rack {i+1}", color=colors[i])
    axs[0, 0].set_title("Front Start Temp")
    axs[0, 0].legend()

    # REAR START
    for i, arr in enumerate(rear_start):
        if arr:
            axs[0, 1].plot(arr, label=f"Rack {i+1}", color=colors[i])
    axs[0, 1].set_title("Rear Start Temp")
    axs[0, 1].legend()

    # FRONT END
    for i, arr in enumerate(front_end):
        if arr:
            axs[1, 0].plot(arr, label=f"Rack {i+1}", color=colors[i])
    axs[1, 0].set_title("Front End Temp")
    axs[1, 0].legend()

    # REAR END
    for i, arr in enumerate(rear_end):
        if arr:
            axs[1, 1].plot(arr, label=f"Rack {i+1}", color=colors[i])
    axs[1, 1].set_title("Rear End Temp")
    axs[1, 1].legend()

    plt.tight_layout()
    plt.pause(0.01)