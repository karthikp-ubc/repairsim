# This is a simple base class for simulating random failures in simPy
# It can be extended to create more sophisticated failures and recovery


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

