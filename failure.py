# Does a parameter sweep of the different failure rates and observes the results

import simparams as sp
import simulation
import statsim
import collector
import graph
import randomFailure as rf

# Mapping from failure distributions to failure types (add new failures here)
failureTypes = {
                        "exponential":          rf.ExponentialFailure,
                        "uniform":              rf.UniformFailure,
                        "weibull":              rf.WeibullFailure,
                        "n_exponential":        rf.ParallelExponentialFailure,
                        "exponential_fr":       rf.FailureRecovery,
                        "exponential_frr":      rf.FailureTwoStageRecovery,
                        "n_exponential_fr":     rf.ParallelFailureRecovery,
                        "branching":            rf.TwoBranchExponentialFailureRecovery,
                        "":                     None
}

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

def getFailureType(distribution):
	"Get the failure type from the parameter file"
	try:
                failureType = failureTypes[ distribution ]
	except:
                raise NameError("Unknown failure distribution " + str(distribution) )

	return failureType

def sweep_range(sp, stats):
	"Sweep the range of failure rates and simulate each rate many times"
	
	rate = sp.start_rate
	failureType = getFailureType(sp.distribution)

	# Vary the rate incrementally until the end_rate
	while (rate <= sp.end_rate):

		# make a new entry for the rate
		stats.startRow(rate)

		# Call the simulate function for the different runs with the rate parameter
		sp.failure_rate = rate  
		
		try:
			simulation.simulate( sp, failureType, stats )
		except:
			raise NameError("Undefined parameter name")
	
		# Done with the statistics for this entry
		stats.doneRow(rate)

		rate += sp.increment_rate 
	# Done while

#End of function

# Begin main program
if __name__=="__main__":

	# Initialize the parameters and statistics
	stats = collector.Collector( statsim.simpleStats )

	# Sweep the range specifiied
	sweep_range(sp, stats)

	# Print all the gathered statistics
	print(stats)

	# Plot the graph if needed
	if sp.graph: 
		graph.plot_graph(sp, stats, statsim.simpleStats.keys(), "Failure rate", "Availability")

