import matplotlib.pyplot as plt
import numpy as np

def plot_graph(sp, stats, statNames, xlabel, ylabel, verbose = False):
        "Plot the statistics as line graphs over the swept range"

        t = np.arange(sp.start_rate, sp.end_rate + sp.increment_rate, sp.increment_rate)
        
        print("StatNames ", statNames)

        # Get the list of statistics stored in the collector
        for statName in statNames:
                # Extract each of the statistics
                values = stats.extract(statName)
                print(statName, values)

                # Plot the statistics as a line graph
                plt.plot(t, values, label = statName)
        # Done for

        # Label the axes, legend and show the graph
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.show()

# End of plot_graph
