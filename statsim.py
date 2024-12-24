# Module for statistics collection - can use this for multiple simulations
import scipy.stats as scistats
import statistics
import numpy as np
from functools import partial

# Reusable function for confidence interval
def conf_interval(conf,data):
	"Confidence interval computation assuming normal error distribution"
	# conf represents the confidence interval. This returns a tuple.	
	# This calls the sciPystats routine
	return scistats.norm.interval(confidence=conf, 
                 loc=np.mean(data), 
                 scale=scistats.sem(data)) 

# Statistics you want to collect - you can add to this list
simpleStats = { 
		"median" : statistics.median, 
		"average" : statistics.mean,  
#		"stddev" : statistics.stdev,
#		"interval90" : partial(conf_interval,0.90),
		"interval95" : partial(conf_interval,0.95),
#		"interval99" : partial(conf_interval,0.99)
}

