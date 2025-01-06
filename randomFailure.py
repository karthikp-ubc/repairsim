# This is a simple base class for simulating random failures in simPy
# It can be extended to create more sophisticated failures and recovery

import random
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
		return self.name + " "

	def arrivalTime(self):
		"Abstract method to specify the distribution"
		# You must Override this function if you want to change the distribution
		raise NotImplementedError("Abstract class cannot be instantiated")

	def trigger(self):
		"Emulates an event of the process at the arrivalTime"
		# Generate interarrival times from arrivalTime abstract method and wraps it in a timeout object
		interarrival = self.arrivalTime()
		return( self.env.timeout(interarrival) )

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
			if self.debug: print("Yielding from ", self.name)
			yield( triggerEvent )

			# Update the statistics
			if self.debug: print("Updating statistics: ", self.name)
			elapsedTime = self.env.now - prevTime
			self.updateStatistics(elapsedTime, 1)
			prevTime = self.env.now

			if self.debug: print("\tDone", self.name, " Time = %.2f" % self.env.now)

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

# Class to model exponential failures
class ExponentialFailure(ExponentialProcess):
	"Uses exponential distribution to simulate random failure"

	def __init__(self, env, params, name="Exponential Failure"):
		super().__init__(env, params, name)
		self.rate = params.failure_rate

#End of class ExponentialFailure

# Class to model uniform failures
class UniformFailure(UniformProcess):
	"Uses uniform distribution to simulate random failure"

	def __init__(self, env, params, name="Uniform Failure"):
		super().__init__(env, params, name)
		self.a = params.failure_a
		self.b = params.failure_b

#End of class UniformFailure

# Class to model Weibull failures
class WeibullFailure(WeibullProcess):
	"Uses weibull distribution to simulate random failure"

	def __init__(self, env, params, name="Weibull Failure"):
		super().__init__(env, params, name)
		self.alpha = params.failure_alpha
		self.beta = params.failure_beta

#End of class WeibullFailure

# Done with simple failure classes. From now on, we'll define composite processes

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
		triggerEvent = AnyOf( self.env, events) 	
		# if self.debug: print(triggerEvent)
		
		return( triggerEvent )

	def __str__(self):
		res = self.name + " parallel [ "
		for process in self.processes:
			res += str(process)
		res += " ]"

# End of class ParallelProcess

# Parallel exponential failure processeses
class ParallelExponentialFailure(ParallelProcess, ExponentialFailure):
	"Simulates multiple parallel process failures each with an exponential failure distribution"

	def __init__(self, env, params, name="N-Exponential"):
		# NOTE: We call super only once here, though it should call both MultipleFailure and ExponentialFailure's init methods (Why?)
		super().__init__(env, params, name)
	
		# Initialize the processes here
		self.n = params.num_process
		for i in range(self.n):
			process = ExponentialFailure(env, params)
			process.name = process.name + " " + str(i)
			self.processes.append( process )
		# End for

# End of class ParallelExponential	

# Abstract Class to simulate multiple sequential processes including recovery
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

		# Call the currentProcesse's trigger method to get the TimeOut object
		return self.currentProcess.trigger()
	
	def __str__(self):
		res = self.name + " sequential [ "
		for process in self.sequence:
			res += str(process)
		res += " ]"

	def updateStatistics(self, waitTime, count):
		"Function to update statistics for each process"
		# Update the statistics for the current process (as defined inthe  trigger)
		self.currentProcess.updateStatistics(waitTime, count)

# End of class SequentialProcess

# Class to model exponential recovery times
class ExponentialRecovery(ExponentialProcess):
	"Simulates exponential recovery times"

	def __init__(self, env, params, name="Exponential Recovery"):
		super().__init__(env, params, name)
		self.rate = params.recovery_rate

#End of class ExponentialRecovery

# Class that simulates a 2-stage failure and recovery process (both of which are exponential)
# This derives from the Sequential Process class above
class TwoStageFailureRecovery(SequentialProcess):
	"Simulates a 2-stage  failure-recovery process with exponentially distributed times"

	def __init__(self, env, params, name="2Exp-Failure-Recovery"):
	
		# Initialize the process sequence before calling the sequential process constructor
		params.sequence = [ ExponentialFailure(env, params, "Fail"), ExponentialRecovery(env, params, "Recover") ]
		super().__init__(env, params, name)

	def collect(self, coll):
		# Collect the fraction uptime (indicates availability)
		# FIXME: We should make this generic so it works on any number of processes
		
		upTime = self.sequence[0].waitTime
		downTime = self.sequence[1].waitTime
		coll.collect( upTime / (upTime + downTime) )

#End of class TwoStageFailureRecovery 

# Class that simulates a 3-stage failure and recovery process (both of which are exponential)
# This derives from the Sequential Process class above
class ThreeStageFailureRecovery(SequentialProcess):
	"Simulates a 3-stage failure-recovery-recovery process with exponentially distributed times"

	def __init__(self, env, params, name="3Exp-Failure-Recovery"):
	
		# Initialize the process sequence before calling the sequential process constructor
		# FIXME: Currently, both recovery processes have the same MTTR - we should make this configurable
		params.sequence = [ ExponentialFailure(env, params, "Fail"), ExponentialRecovery(env, params, "Recover1"), ExponentialRecovery(env, params, "Recover2") ]
		super().__init__(env, params, name)

	def collect(self, coll):
		# Collect the fraction uptime (indicates availability)
		# FIXME: We should make this generic so it works on any number of processes
		
		upTime = self.sequence[0].waitTime
		downTime = self.sequence[1].waitTime + self.sequence[2].waitTime
		coll.collect( upTime / (upTime + downTime) )

#End of class ThreeStageFailureRecovery

# Class for n-stage Failures and m-stage Recovery, where n and m are parameters 
class ThreeStageFailureRecovery(SequentialProcess):
	pass

