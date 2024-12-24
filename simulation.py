# Main function that calls the sumulator with a set of parameters, and performs maxRuns runs, each for a time of maxTime
import randomFailure as rf
import simpy

# Mapping from failure distributions to failure types (add new failures here)
failureTypes = { 
			"exponential": 		rf.ExponentialFailure,
			"uniform": 		rf.UniformFailure,
			"weibull":		rf.WeibullFailure,
			"n_exponential": 	rf.MultipleExponential
}	


def simulate(params, coll, verbose = False):
	print("Starting simulation with parameters", params)

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
		count = f.getCount()

		# Update all the statistics values by collecting this value
		coll.collect(count) 

		if verbose: print("\tFailure count = %d" %count ) 
		if verbose: print("Done run ", i, "\n")		
	
	print("Done simulation")

#End of simulate
