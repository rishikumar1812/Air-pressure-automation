def temp_graph(ax, arrays, title):

    for arr in arrays:
        if arr:
            ax.plot(arr)

    ax.set_title(title)