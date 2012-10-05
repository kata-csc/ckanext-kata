def generate_pid():
	""" Generates dummy pid """
	
	import datetime
	return "urn:nbn:fi:csc-kata%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")