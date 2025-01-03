# This is a simple base class for simulating random failures in simPy
# It can be extended to create more sophisticated failures and recovery

import random
from simpy.events import AnyOf, AllOf, Event

# Abstract base class for failure processes
class RandomProcess(object):
	"Simulates random failures according to a distribution (not specified)"

	# We leave the specific parameters to the derived classes as they vary by distribution
	def __init__(self, env, params):
		self.env = env
		self.count = 0
		self.waitTime = 0
		self.debug = False
		self.action = env.process( self.run() )

	def setVerbose(self):
		self.debug = True

	def setSeed(self, seed):
		# NOTE: Don't specify a seed if you want random values
		random.seed( seed )

	def __str__(self):
		return self.name + " "

	def arrivalTime(self):
		"Abstract method to specify the distribution"
		# Override this function if you want to change the distribution
		raise NotImplementedError("Abstract class cannot be instantiated")

	def trigger(self):
		"Emulates an event of the process at the arrivalTime"
		# Generate interarrival times from arrivalTime abstract method and wraps it in a timeout object
		interarrival = self.arrivalTime()
		return( self.env.timeout(interarrival) )
	
	def run(self):
		"Main function that is called by env.process"
		prevTime = 0
		while (True):
			elapsedTime = self.env.now - prevTime
			self.waitTime += elapsedTime
			self.count += 1
			prevTime = self.env.now
			yield( self.trigger() )
			if self.debug: print("\t", self.name, " Time = %.2f" % self.env.now, "Count = %d" % self.count ) 

	def collect(self, stats):
		# Collect the statistics for average wait time per arrival
		stats.collect( self.waitTime / self.count )
		#stats.collect( self.count )

#End of class RandomProcess

class ExponentialProcess(RandomProcess):
	"Abstract class for exponential distribution"
	
	# NOTE: subclasses define the self.rate parameter
	def __init__(self, env, params):
		super().__init__(env, params)
		self.name = "Exponential"

	def arrivalTime(self):
		return random.expovariate(self.rate)

	def __str__(self):
		return self.name + " rate = " + str(self.rate)	

# End of class Exponential Process

class UniformProcess(RandomProcess):
	"Uses uniform distribution to simulate random arrivals"

	def __init__(self, env, params):
		super().__init__(env, params)
		self.name= "Uniform"

	def arrivalTime(self):
		return random.uniform(self.a, self.b) 
	
	def __str__(self):
		return self.name + " a = " + str(self.a) + " b = " + str(self.b)	

#End of class UniformProcess
	
class WeibullProcess(RandomProcess):
	"Uses Weibull distribution to simulate random arrivals" 

	def __init__(self, env, params):
		super().__init__(env, params)
		self.name="Weibull"

	def arrivalTime(self): 
		random.weibullvariate(self.alpha, self.beta)

	def __str__(self):
		return self.name + " alpha = " + str(self.alpha) + " beta = " + str(self.beta)	

#End of class WeibullProcess

# Class to model exponential failures
class ExponentialFailure(ExponentialProcess):
	"Uses exponential distribution to simulate random failure"

	def __init__(self, env, params):
		super().__init__(env, params)
		self.rate = params.failure_rate
		self.name = "Exponential Failure"

#End of class ExponentialFailure

# Class to model uniform failures
class UniformFailure(UniformProcess):
	"Uses uniform distribution to simulate random failure"

	def __init__(self, env, params):
		super().__init__(env, params)
		self.a = params.failure_a
		self.b = params.failure_b
		self.name = "Uniform Failure"

#End of class UniformFailure

# Class to model Weibull failures
class WeibullFailure(WeibullProcess):
	"Uses weibull distribution to simulate random failure"

	def __init__(self, env, params):
		super().__init__(env, params)
		self.alpha = params.failure_alpha
		self.beta = params.failure_beta
		self.name = "Weibull Failure"

#End of class WeibullFailure

# Done with simple failure classes. From now on, we'll define composite processes

# Simulates a collection of processes executing in parallel with each other. The processes are independent.
class ParallelProcess(RandomProcess):
	"Simulates a process consisting of multiple parallel processes each independent of the other"

	def __init__(self, env, params):
		# Initialize processes based on the params
		self.processes = []
		super().__init__(env, params)
		self.name = "Multiple"

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

	def __init__(self, env, params):
		# NOTE: We call super only once here, though it should call both MultipleFailure and ExponentialFailure's init methods (Why?)
		super().__init__(env, params)
	
		# Initialize the processes here
		self.n = params.num_process
		for i in range(self.n):
			process = ExponentialFailure(env, params)
			process.name = "Exponential " + str(i)
			self.processes.append( process )
		# End for
		self.name = "Multiple exponential"

# End of class ParallelExponential	

# Abstract Class to simulate multiple sequential processes including recovery
class SequentialProcess(RandomProcess):
	"Simulates multiple sequential processes happening one after another"
	
	def __init__(self, env, params):
		super().__init__(env, params)
		self.sequence = params.sequence
		self.num_stages = len(params.sequence)
		self.name = "Sequential"

	def run(self):
		"Main function that is called by env.process"
		
		while (True):
			# Trigger each process in succession, yield its value and continue
			for process in self.sequence:	
				
				# Trigger the event from each process and yield it
				event = process.trigger()

				# Update the statistics of elapsed time and count for the process
				self.waitTime += process.waitTime
				self.count += process.count
	
				if self.debug: print("Yielding from ", process, event)
				yield( event )
			# end for

		# End of while

	def __str__(self):
		res = self.name + " sequential [ "
		for process in self.processes:
			res += str(process)
		res += " ]"

# End of class SequentialProcess

# Class to model exponential recovery times
class ExponentialRecovery(ExponentialProcess):
	"Simulates exponential recovery times"

	def __init__(self, env, params):
		super().__init__(env, params)
		self.rate = params.recovery_rate
		self.name = "Exponential Recovery"

#End of class ExponentialRecovery

# Class that simulates a 2-stage failure and recovery process (both of which are exponential)
# This derives from the Sequential Process class above
class ExponentialFailureRecovery(SequentialProcess):
	"Simulates a simple failure-recovery process with exponentially distributed times"

	def __init__(self, env, params):
	
		# Initialize the process sequence before calling the sequential process constructor
		params.sequence = [ ExponentialFailure(env, params), ExponentialRecovery(env, params) ]
		super().__init__(env, params)  							
		self.name = "Exp-Failure-Recovery"

	# def updateStats(self, process, elapsedTime, count):
		# TODO: Only update the elapsed time for the failure process
				
			
#End of class ExponentialFailureRecovery 
