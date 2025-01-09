import matplotlib.pyplot as plt
import numpy as np

def plot_graph(sp, stats, xlabel, ylabel):
        "Plot the statistics as line graphs over the swept range"

        t = np.arange(sp.start_rate, sp.end_rate + sp.increment_rate, sp.increment_rate)

        statNames = stats.getRows()
        for statName in statNames:

                # Extract each of the statistics
                values = stats.extract(statName)

                # Plot the statistics as a line graph
                plt.plot(t, values, label = statName)
        # Done for

        # Label the axes, legend and show the graph
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.show()

# End of plot_graph
