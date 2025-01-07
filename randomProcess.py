# Simple random processes - these are the basis for the failure and recovery classes in randomFailure

import random
import randomProcess
from simpy.events import AnyOf, AllOf, Event

# Abstract base class for failure processes
class RandomProcess(object):
	"Simulates random failures according to a distribution (not specified)"

	# We leave the specific parameters to the derived classes as they vary by distribution
	def __init__(self, env, params, name = ""):
		self.env = env
		self.count = 0
		self.waitTime = 0
		self.debug = params.verbose
		self.name = name
		
	def setAction(self):
		"Calls the run method and assigns it to action for simPy"
		# NOTE: We're separating this from the constructor, as each derived class should only call it once
		self.action = self.env.process( self.run() )

	def setVerbose(self):
		self.debug = True

	def setSeed(self, seed):
		# NOTE: Don't specify a seed if you want random values
		random.seed( seed )

	def __str__(self):
		return self.name

	def arrivalTime(self):
		"Abstract method to specify the distribution"
		# You must Override this function if you want to change the distribution
		raise NotImplementedError("Abstract class cannot be instantiated")

	def trigger(self):
		"Emulates an event of the process at the arrivalTime"
		# Generate interarrival times from arrivalTime abstract method and wraps it in a timeout object
		interarrival = self.arrivalTime()
		timeoutEvent = self.env.timeout(interarrival) 
		if self.debug: print("\t", self.name, "Triggering event ", timeoutEvent)
		return timeoutEvent

	def updateStatistics(self, waitTime, count):
		"Update the waitTime and count statistics"
		if self.debug: print("\t", self.name, " Updating stats : ", waitTime, count)
		self.waitTime += waitTime
		self.count += count
	
	def run(self):
		"Main function that is called by env.process"
		prevTime = self.env.now
		if self.debug: print("Starting ", self.name)
		
		while (True):

			# Yield a trigger event by calling the trigger method
			triggerEvent = self.trigger()
			if self.debug: print(self.name, "Yielding from ", self.name)
			yield( triggerEvent )

			# Update the statistics
			if self.debug: print("Updating statistics: ", self.name)
			elapsedTime = self.env.now - prevTime
			self.updateStatistics(elapsedTime, 1)
			prevTime = self.env.now

			if self.debug: print("Done", self.name, " Time = %.2f" % self.env.now)

	def collect(self, stats):
		"Collect the statistics for the simulation run"
		# Collect the statistics for average wait time per arrival
		# This can be overridden by derived classes
		stats.collect( self.waitTime / self.count )

#End of class RandomProcess

class ExponentialProcess(RandomProcess):
	"Abstract class for exponential distribution"
	
	# NOTE: subclasses define the self.rate parameter
	def __init__(self, env, params, name="Exponential"):
		super().__init__(env, params, name)

	def arrivalTime(self):
		return random.expovariate(self.rate)

	def __str__(self):
		return self.name + " rate = " + str(self.rate)	

# End of class Exponential Process

class UniformProcess(RandomProcess):
	"Uses uniform distribution to simulate random arrivals"

	def __init__(self, env, params, name="Uniform"):
		super().__init__(env, params, name)

	def arrivalTime(self):
		return random.uniform(self.a, self.b) 
	
	def __str__(self):
		return self.name + " a = " + str(self.a) + " b = " + str(self.b)	

#End of class UniformProcess
	
class WeibullProcess(RandomProcess):
	"Uses Weibull distribution to simulate random arrivals" 

	def __init__(self, env, params, name="Weibull"):
		super().__init__(env, params)

	def arrivalTime(self): 
		random.weibullvariate(self.alpha, self.beta)

	def __str__(self):
		return self.name + " alpha = " + str(self.alpha) + " beta = " + str(self.beta)	

#End of class WeibullProcess

# Simulates a collection of processes executing in parallel with each other. The processes are independent.
class ParallelProcess(RandomProcess):
	"Simulates a process consisting of multiple parallel processes each independent of the other"

	def __init__(self, env, params, name="Multiple"):
		# Initialize processes based on the params
		self.processes = []
		super().__init__(env, params, name)

	def trigger(self):
		"Emulate triggering of events of any of the parallel processes"
		# Get the failures of each process as timeout events
		events = [ ]
		for process in self.processes:
			events.append( process.trigger() )
		
		# Choose the first of the trigerring events
		if self.debug: print(self.name, "Choosing the first of parallel process's events ", events)	
		firstEvent = AnyOf( self.env, events) 	
		if self.debug: print(self.name, "Triggering event ", firstEvent)
		
		return( firstEvent )

	def __str__(self):
		res = self.name + " parallel [ "
		for process in self.processes:
			res += str(process) + " , "
		res += " ]"
		return res

# End of class ParallelProcess

# Siimulate multiple sequential processes - the processes run one after the other and wrap around in the end
class SequentialProcess(RandomProcess):
	"Simulates multiple sequential processes happening one after another"
	
	def __init__(self, env, params, name="Sequential"):
		super().__init__(env, params, name)
		self.sequence = params.sequence
		self.currentIndex = 0	# current process Index in the sequence
		self.currentProcess = self.sequence[ self.currentIndex ]	

	def trigger(self):
		"Wrap the time to yield in a timeOut object and return it"

		# Iterate over the sequence. Return current process and update currentIndex to next cyclically
		self.currentProcess = self.sequence[ self.currentIndex ]
		self.currentIndex = (self.currentIndex + 1) % len(self.sequence)
		if self.debug: print(self.name, "Choosing process ", self.currentProcess)

		# Call the currentProcesse's trigger method to get the TimeOut object
		currentEvent = self.currentProcess.trigger()
		if self.debug: print(self.name, "Triggerring event ", currentEvent)
		return currentEvent
	
	def __str__(self):
		res = self.name + " sequential [ "
		for process in self.sequence:
			res += str(process)
		res += " ]"
		return res

	def updateStatistics(self, waitTime, count):
		"Function to update statistics for each process"
		# Update the statistics for the current process (as defined inthe  trigger)
		self.currentProcess.updateStatistics(waitTime, count)

# End of class SequentialProcess

# Simulate branching process that takes one path or another with distinct probabilities
# NOTE: The probabilities are specified by the user and are assumed to sum to a total of 1
# We also assume that the branches are sorted in INCREASING order of their probabilities
class BranchingProcess(RandomProcess):
	"Simulates branching processes in a probabilistic manner"
	
	def __init__(self, env, params, name = "Branching"):
		super().__init__(env, params, name)
		self.branches = params.branches
		
		# Calculate the CDF of the branches based on probabilities
		self.cdf = []
		sum = 0
		# We assume the params.probabilities has same length as self.branches
		for i in range( len(self.branches) ):
			sum += params.probabilities[i]
			self.cdf.append( sum )
		# FIXME: Assert that the sum of probabilities is 1

	def trigger(self):
		"Wrap the time to yield in a timeOut object and return it"
		# Generate a random no bet. 0 and 1 and choose a branch based on the CDF 
		n = random.random()
		if self.debug: print("Random no. generated", n)
		self.currentProcess = 0

		# Choose the branch corresponding to the random no. based on the CDF 
		for i in range( len(self.branches) ):
			if n < self.cdf[i]:
				self.currentProcess = self.branches[i]
				break

		# We have chosen the branch process for trigerring in currentProcess
		if self.debug: print(self.name, "Choosing branch ", self.currentProcess)
		
		# Call the currentProcesse's trigger method to get the TimeOut object
		currentEvent = self.currentProcess.trigger()
		if self.debug: print(self.name, "Triggerring event ", currentEvent)
		return currentEvent

	def updateStatistics(self, waitTime, count):
		"Function to update statistics for each process"
		# Update the statistics for the current process (as defined in the trigger)
		self.currentProcess.updateStatistics(waitTime, count)

# End of class BranchingProcess

# TODO: Add a process that requires ALL its subprocesses to finish before it does
