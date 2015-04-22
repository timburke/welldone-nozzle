#Define well-known exception types
class BusyException (Exception):
	pass

class EndpointNotFoundException (Exception):
	pass

class ChecksumMismatchException (Exception):
	pass

def handle_mib_endpoint(command, sender, params):
	"""
	Always return that we're busy
	"""
	
	return (0x00, [0x0a])