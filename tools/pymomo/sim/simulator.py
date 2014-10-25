# simulator.py
# Generic interface for controlling PIC microchip simulators
#
# Designed to work with sim30 from Microchip for simulating PIC24
# chips and gpsim to simulate pic12 and pic16 chips.

import simulators
from pymomo.utilities.typedargs.annotate import *
from pymomo.exceptions import *
from multiprocessing import Process, Queue, Pipe
import atexit
import os.path
import os
import tempfile

def _spawn_simulator(sim_type, child_pipe):
	"""
	Spawn a simulator of the given type, attaching child_pipe to it
	so that we can communicate with it.
	"""

	sim = sim_type(child_pipe)
	sim.run()

def _quit_simulator(sim):
	"""
	Quit the simulator process.
	"""
	sim.exit()

@context("Simulator")
class Simulator:
	"""
	Generic interface for simulating embedded microprocessors.
	Subclasses should implement specific methods as a worker
	object that is spawned in a separate process.
	"""

	@param("type", "string", desc="Type of simulator to create (pic24 or pic12)")
	def __init__(self, type):
		"""
		Create a simulator object in a separate process 
		"""

		if not hasattr(simulators, type):
			raise ArgumentError("unknown simulator type '%s'" % str(type))

		self.sim_type = getattr(simulators, type)
		self._pipe, child_pipe = Pipe(duplex=True)

		self.process = Process(target=_spawn_simulator, args=(self.sim_type, child_pipe))
		self.process.start()

		#Make a list of any temporary files generated by this object for deletion
		self.temporaries = []

		#Make sure we always quit the simulator when we exit so that we don't hang the
		#executing proces
		atexit.register(_quit_simulator, self)

	@finalizer
	def exit(self):
		"""
		Tell the simulator to quit and wait for it to exit
		"""
		
		self.finish()

		#Clean up any temporary files
		for i in self.temporaries:
			os.remove(i)

		#If we are called twice, make sure we don't try to clean up again.
		self.temporaries = []

	@annotated
	def finish(self):
		"""
		Close the underlying simulator process, guaranteeing that any files that output
		during the simulation are created and valid after this call returns.
		"""

		if self.process.is_alive():
			self._command("quit")
			self.process.join()

	@param("program", "path", "readable", desc="Path of program object file to load")
	def load(self, program):
		"""
		Load the program object file into the simulator
		"""

		# Try to determine file type
		type = 'unknown'
		ext = os.path.splitext(program)[1]
		if ext == '.coff' or ext == '.cof':
			type = 'coff'
		elif ext == '.elf':
			type = 'elf'
		elif ext == '.hex':
			type = 'hex'

		self._command('load_program', program=program, type=type)

	@param("name", "string", desc="Name of the simulator parameter to set")
	@param("value", "string", desc="Value of the parameter")
	def set_param(self, name, value):
		"""
		Set a simulator specific parameter by name.
		"""

		self._command('set_param', name=name, value=value)

	@annotated
	def attach_log(self):
		"""
		Upon completion of this simulation, generate a log file containing
		the output of the simulated code.  The log file is not guaranteed to be generated
		until finish() is called on the simulator.
		"""

		path = self._build_temp()
		self._command('set_log', file=path)
		self.logfile = path

	@returns_data(desc="log contents")
	def get_log(self):
		"""
		Return the log attached to the simulator in a simulator-dependent manner as a string.
		This method is only guaranteed to return all of the log's contents if finish() has
		been called before the call to get_log.  This is because the simulator subprocesses
		may not flush data to the log file until they are closed and we cannot use a pipe because
		not all of the external simulator programs support it.
		"""

		if not hasattr(self, 'logfile'):
			raise InternalError('You must attach a log using attach_log before calling get_log')

		try:
			with open(self.logfile, 'r') as f:
				contents = f.read()
		except IOError as e:
			raise InternalError('Log file could not be read because: %s' % str(e))

		return contents

	@param("command", "string", desc="Raw command string to execute in simulator")
	def raw_command(self, command):
		"""
		Pass a raw string command to the underlying simulator and execute it.  This
		can be useful if there is not a high level API function for achieving what
		you need to accomplish.
		"""

		self._command('raw_command', command=command)

	@returns_data(desc="reason")
	@param("wait", "integer", desc="maximum number of seconds to wait (-1 is forever)")
	def wait(self, wait):
		"""
		Wait for the simulator to finish executing code and return to being able
		to process commands.
		"""

		return self._command('wait', timeout=wait)

	@returns_data(desc="ready for commands")
	def ready(self):
		"""
		Return if the simulator is ready to accept new commands or if it is running
		code.
		"""

		return self._command('ready')

	@annotated
	def execute(self):
		"""
		Begin or continue program execution
		"""

		self._command('execute')

	#Communication functions to communicate with the simulator worker objects
	def _send_cmd(self, method, **kwargs):
		msg = {'method': method}
		msg.update(kwargs)
		self._pipe.send(msg)

	def _receive_response(self, timeout=3):
		if not self._pipe.poll(timeout):
			self.process.terminate()
			raise TimeoutError("Waiting for a response from child simulator process.")

		response = self._pipe.recv()
		return response

	def _command(self, method, **kwargs):
		self._send_cmd(method, **kwargs)
		resp = self._receive_response()

		if resp['error'] is True:
			params = {x:y for x,y in resp.iteritems() if x != 'message' and x != 'error'}
			raise InternalError(resp['message'], **params)

		return resp.get('result', None)

	def _build_temp(self):
		"""
		Build a temporary file with no spaces in the name for use with simulator subprocesses.
		"""

		outfile = tempfile.NamedTemporaryFile(delete=False)
		outfile.close()

		if " " in outfile.name:
			os.remove(outfile.name)
			raise InternalError("Temporary direction has space in file name, sim30 cannot handle this, check the TMPDIR,TEMP and TMP environment variables.  Path was '%s'" % outfile)
		

		self.temporaries.append(outfile.name)
		return outfile.name
