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
