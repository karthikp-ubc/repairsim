# Main function that calls the sumulator with a set of parameters, and performs maxRuns runs, each for a time of maxTime

import randomFailure
import simpy

def simulate(params, failureType, coll):
	"Simulate the run with params"

	# Initialize the overall simulation parameters first
	verbose = params.verbose 
	maxRuns = params.maxRuns
	maxTime = params.maxTime

	if verbose: print("Starting simulation with parameters", params)

	if verbose: print("\tFailure type = ", failureType)
		
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
