# Module to collect statistics for different simulation runs

class Collector:
	"Collects statistics about the simulation for visualization or aggregation"

	def __init__(self, statTable, verbose=False):
		self.stats = { }
		self.statTable = statTable
		self.debug = verbose

	def startRow(self, name):
		"This is called at the start of a row"
		self.stats[name] = { }
		self.tempList = [ ]

	def collect(self, x):
		self.tempList.append( x )

	def doneRow(self, name):
		"This is called when you're done with a row"	
		for (statName, func) in self.statTable.items():
			statValue = func(self.tempList)
			self.stats[ name ][ statName ] = statValue	
		
	def print(self):
		# For now, this just prints everything; TODO: make it __str__
		for (name, stat) in self.stats.items():
			print(name)
			for (statName, statValue) in stat.items():
				print("\t", statName, " = ", statValue) 

	def extract(self,stat_name):
		# Extract all the statistics corresponding to statname
		res = []
		for (name, stat) in self.stats.items():
			for (statName, statValue) in stat.items():
				if (statName==stat_name):
					res.append(statValue)
		return res		
			
