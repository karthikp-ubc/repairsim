# This is a simple base class for simulating random failures in simPy
# It can be extended to create more sophisticated failures and recovery

import random

# Abstract base class for failure processes
class RandomFailure(object):
	"Simulates random failures with a specific rate according to a distribution (not specified)"

	# We leave the specific parameters to the derived classes as they vary by distribution
	def __init__(self, env, params):
		self.env = env
		self.count = 0
		self.debug = False
		self.action = env.process( self.run() )

	def setVerbose(self):
		self.debug = True

	def setSeed(self, seed):
		# NOTE: Don't specify a seed if you want random values
		random.seed( seed )

	def arrivalTime(self):
		"Abstract method to specify the distribution"
		# Override this function if you want to change the distribution
		raise NotImplementedError("Abstract class cannot be instantiated")

	def run(self):
		"Main function that is called by env.process"
		while (True):
			# Generate interarrival times from arrivalTime abstract method and yeild the time
			interarrival = self.arrivalTime()
			yield( self.env.timeout(interarrival) )
			self.count += 1
			if self.debug: print("\t", self.name, " Time = %.2f" % self.env.now, "Count = %d" % self.count ) 

	def getCount(self):
		return self.count

#End of class RandomFailure

class ExponentialFailure(RandomFailure):
	"Uses exponential distribution to simulate random failure"

	def __init__(self, env, params):
		self.rate = params.rate
		self.name = "Exponential"
		super().__init__(env, params)

	def arrivalTime(self):
		return random.expovariate(self.rate)

#End of class ExponentialFailure

class UniformFailure(RandomFailure):
	"Uses uniform distribution to simulate random failure"

	def __init__(self, env, params):
		self.a = params.a
		self.b = params.b
		self.name="Uniform"
		super().__init__(env, params)

	def arrivalTime(self):
		return random.uniform(self.a, self.b) 

#End of class UniformFailure
	
class WeibullFailure(RandomFailure):

	def __init__(self, env, params):
		self.name="Weibull"
		self.alpha = params.alpha
		self.beta = params.beta
		super().__init__(env, params)

	def arrivalTime(self): 
		random.weibullvariate(self.alpha, self.beta)

#End of class WeibullFailure


# This is also an abstract base class - the individual processes need to be specified by the user
class MultipleFailure(RandomFailure):
	"Simulates a process consisting of multiple random failure processes each independent of the other"

	def __init__(self, env, params):
		self.n = params.processes
		self.name = "Multiple"
		super().__init__(env, params)

	def run(self):
		# Need to go through the arrival times of all the processes by adding them to the wait queue
		while (True):
			for i in range(1, self.n):
				
				interarrival = self.arrivalTime()
				yield( self.env.process(interarrival) )
				self.count += 1

				if self.debug: print("\t", self.name, " Time = %.2f" % self.env.now, "Process = %d" % i, "Count = %d" % self.count ) 
		
# End of class MultipleFailure

class MultipleExponential(MultipleFailure, ExponentialFailure):
	"Simulates multiple process failures each with an exponential failure distribution"

	def __init__(self, env, params):
		# NOTE: We call super only once here, though it should call both MultipleFailure and ExponentialFailure's init methods (Why?)
		params.verbose=True
		super().__init__(env, params)

# End of class MultipleExponential		

