# Main function that calls the sumulator with a set of parameters, and performs maxRuns runs, each for a time of maxTime
import randomFailure as rf
import simpy

# Mapping from failure distributions to failure types (add new failures here)
failureTypes = { 
			"exponential": 		rf.ExponentialFailure,
			"uniform": 		rf.UniformFailure,
			"weibull":		rf.WeibullFailure,
			"n_exponential": 	rf.ParallelExponentialFailure,
			"exponential_fr":	rf.ExponentialFailureRecovery
}	

# Main function for simulation; needs maxRuns and maxTime to be specified in params, as well as failureType
def simulate(params, coll, verbose = False):
	"Simulate the run with params"

	if verbose: print("Starting simulation with parameters", params)

	distribution = params.distribution
	maxRuns = params.maxRuns
	maxTime = params.maxTime

	for i in range(maxRuns):
		if verbose: print("Starting run ", i)
		env = simpy.Environment()

		# print("Distribution: ", distribution)
		try:
			failureType = failureTypes[ distribution ]
		except: 
			raise NameError("Unknown failure distribution " + str(distribution) )			

		# Instantiate a class of the failureType specified
		f = failureType(env, params)

		if verbose: f.setVerbose()

		# Run the simulation until the maximum time and get number of failures
		env.run(until = maxTime)
		
		# Update all the statistics values by collecting this value
		f.collect( coll )

		if verbose: print("Done run ", i, "\n")		
	
	if verbose: print("Done simulation ", params)

#End of simulate
