# This is a simple base class for simulating random failures in simPy
# It can be extended to create more sophisticated failures and recovery
import randomProcess as rp

# Class to model exponential failures
class ExponentialFailure(rp.ExponentialProcess):
	"Uses exponential distribution to simulate random failure"

	def __init__(self, env, params, name="Exponential Failure"):
		super().__init__(env, params, name)
		self.rate = params.failure_rate

#End of class ExponentialFailure

# Class to model uniform failures
class UniformFailure(rp.UniformProcess):
	"Uses uniform distribution to simulate random failure"

	def __init__(self, env, params, name="Uniform Failure"):
		super().__init__(env, params, name)
		self.a = params.failure_a
		self.b = params.failure_b

#End of class UniformFailure

# Class to model Weibull failures
class WeibullFailure(rp.WeibullProcess):
	"Uses weibull distribution to simulate random failure"

	def __init__(self, env, params, name="Weibull Failure"):
		super().__init__(env, params, name)
		self.alpha = params.failure_alpha
		self.beta = params.failure_beta

#End of class WeibullFailure

# Parallel exponential failure processeses
class ParallelExponentialFailure(rp.ParallelProcess):
	"Simulates multiple parallel process failures each with an exponential failure distribution"

	def __init__(self, env, params, name="N-Exponential"):
		super().__init__(env, params, name)
	
		# Initialize the processes here
		self.n = params.num_process
		for i in range(self.n):
			if self.debug: print(self.name, "Initializing exponential failure ", i)
			process = ExponentialFailure(env, params)
			process.name = process.name + " " + str(i)
			self.processes.append( process )
		if self.debug: print(self.name, "Processes ", self.processes)

# End of class ParallelExponential	

# Class to model exponential recovery times
class ExponentialRecovery(rp.ExponentialProcess):
	"Simulates exponential recovery times"

	def __init__(self, env, params, name="Exponential Recovery"):
		super().__init__(env, params, name)
		self.rate = params.recovery_rate

#End of class ExponentialRecovery

# Class that simulates a 2-stage failure and recovery process (both of which are exponential)
class FailureRecovery(rp.SequentialProcess):
	"Simulates a 2-stage  failure-recovery process with exponentially distributed times"

	def initSequence(self, env, params):
		"Initialize the sequence of stages"
		params.sequence = [ ExponentialFailure(env, params), ExponentialRecovery(env, params) ]

	def __init__(self, env, params, name="Exp-Failure-Recovery"):
	
		# Initialize the process sequence before calling the sequential process constructor
		self.initSequence(env, params)
		super().__init__(env, params, name)

	def collect(self, coll):
		# Collect the fraction uptime (indicates availability)
		# FIXME: We should make this generic so it works on any number of processes
		
		upTime = self.sequence[0].waitTime
		downTime = self.sequence[1].waitTime
		coll.collect( upTime / (upTime + downTime) )

#End of class TwoStageFailureRecovery 

# Class that simulates a 3-stage failure and recovery process (both of which are exponential)
class FailureTwoStageRecovery(FailureRecovery):
	"Simulates a 3-stage failure-recovery-recovery process with exponentially distributed times"

	def initSequence(self, env, params):
		"Initialize the sequence of stages"
		# FIXME: Currently, both recovery processes have the same MTTR - we should make this configurable
		params.sequence = [ ExponentialFailure(env, params, "Fail"), ExponentialRecovery(env, params, "Recover1"), ExponentialRecovery(env, params, "Recover2") ]

	def __init__(self, env, params, name="Exp-Failure-TwoRecovery"):
		super().__init__(env, params, name)

	def collect(self, coll):
		# Collect the fraction uptime (indicates availability)
		# FIXME: We should make this generic so it works on any number of processes
		
		upTime = self.sequence[0].waitTime
		downTime = self.sequence[1].waitTime + self.sequence[2].waitTime
		coll.collect( upTime / (upTime + downTime) )

#End of class ThreeStageFailureRecovery

# Class for n-parallel Failures and Recovery (it has two stages: parallel failure, followed by recovery)
class ParallelFailureRecovery(FailureRecovery):
	"Simulates a multi-process failure and sequential recovery process"

	def initSequence(self, env, params):
		"Initialize the sequence of stages"
		# FIXME: Currently, both recovery processes have the same MTTR - we should make this configurable
		params.sequence = [ ParallelExponentialFailure(env, params), ExponentialRecovery(env, params) ]
	
	def __init__(self, env, params, name="Parallel-Failure-Recovery"):
		super().__init__(env, params, name)

# End of ParallelFailureRecovery

class TwoBranchExponentialFailure(rp.BranchingProcess):
	
	def initBranches(self, env, params):
		params.branches = [ ExponentialFailure(env, params, "Fail-branch1"), ExponentialFailure(env, params, "Fail-branch2") ]
		branchProb = params.branchProb	# We assume the branch probability is specified as a parameter

		# Order the probabilites in ascending order for passing to the BranchingProcess
		if branchProb < 0.5:
			params.probabilities = [ branchProb, 1 - branchProb ]
		else:
			params.probabilities = [ 1 - branchProb, branchProb ]

	def __init__(self, env, params, name="Branching-Exponential-Failure"):
		"Initialize the branches for the process"
		
		self.initBranches(env, params)
		super().__init__(env, params, name)

	#def collect(self, coll):
	#	pass
	
# End of class BranchingExponential	
