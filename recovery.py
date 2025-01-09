# Simulates a simple process with multiple recovery pathways to understand tradeoffs of the different parameters
import simparams as sp 
import numpy as np
import simulation
import statsim
import collector

def sweep_range(sp, stats):
        "Sweep the range of recovery rates and simulate each rate many times"

        rate = sp.start_rate
        while (rate <= sp.end_rate):

                # make a new entry for the rate
                stats.startRow(rate)

                # Call the simulate function for the different runs with the rate parameter
                sp.recovery_rate = rate

                try:
                        simulation.simulate( sp, stats )
                except:
                        raise NameError("Undefined parameter name")

                # Done with the statistics for this entry
                stats.doneRow(rate)

                rate += sp.increment_rate
        # Done while

#End of sweep_range


# Begin main program
if __name__=="__main__":

	# Initialize the parameters and statistics
	stats = collector.Collector( statsim.simpleStats )

	# Sweep the range specifiied
	sweep_range(sp, stats)

	# Print all the gathered statistics
	print(stats)
