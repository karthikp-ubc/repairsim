# Main function that calls the sumulator with a set of parameters, and performs maxRuns runs, each for a time of maxTime
import randomFailure as rf
import simpy

# Mapping from failure distributions to failure types (add new failures here)
failureTypes = { 
			"exponential": 		rf.ExponentialFailure,
			"uniform": 		rf.UniformFailure,
			"weibull":		rf.WeibullFailure,
			"n_exponential": 	rf.ParallelExponentialFailure,
			"exponential_fr":	rf.TwoStageFailureRecovery,
			"exponential_frr":	rf.ThreeStageFailureRecovery,
			"n_exponential_fr":	rf.ParallelFailureRecovery
}	

# Main function for simulation; needs maxRuns and maxTime to be specified in params, as well as failureType
def simulate(params, coll):
	"Simulate the run with params"

	# Initialize the overall simulation parameters first
	verbose = params.verbose 
	distribution = params.distribution
	maxRuns = params.maxRuns
	maxTime = params.maxTime

	if verbose: print("Starting simulation with parameters", params)

	# Get the failure type for the simulation	
	try:
		failureType = failureTypes[ distribution ]
	except: 
		raise NameError("Unknown failure distribution " + str(distribution) )			
	
	if verbose: print("Simulating Failure type = ", failureType)
		
	# Run the simulations each for a total of maxRun times 
	# FIXME: Make this configurable based on the confidence intervals
	for i in range(maxRuns):
		if verbose: print("Starting run ", i)
		env = simpy.Environment()

		# Instantiate a class of the failureType specified and initialize its run method
		f = failureType(env, params)
		
		# NOTE: We need to do this explicitly before calling the env.run method
		f.setAction()

		# Run the simulation until the maximum time specified
		if verbose: print("Running simulation for : ", maxTime)
		env.run(until = maxTime)
		
		# Update all the statistics values by collecting its value from the run
		f.collect( coll )

		if verbose: print("Done run ", i, "\n")		
	
	if verbose: print("Done simulation ", params)

#End of simulate
