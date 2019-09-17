from subprocess import PIPE, STDOUT, Popen, run

class VampireWrapper:
	vampireProcess = None # Process | None
	vampireState = None # "running" | "saturation" | "refutation" | "error" | None
	remainingChoices = None # [clauseIdsToBeActivatedInTheFuture] | None

	# run Vampire fully automatically on the given input file, and return all the output generated by Vampire
	def start(self, inputFile):
		if self.vampireProcess != None:
			self.vampireProcess.kill()
		output = run(["/Users/bernhard/repos/vampire-release/vampire_rel_manualcl_4057", "--input_syntax", "smtlib2", "-av", "off", inputFile, "--manual_cs", "off", "--show_preprocessing", "on", "--show_new", "on", "--show_passive", "on", "--show_active", "on", "--show_reductions", "on", "--proof_extra", "full"], stdout=PIPE, stderr=STDOUT, text=True).stdout
		lines = output.replace('\r\n', '\n').replace('\r', '\n').split('\n')
		state = "none"
		for line in lines:
			if line.startswith("% Refutation found. Thanks to"): # TODO: use SZS status instead?
				state = "refutation"
				break
			elif line.startswith("% SZS status Satisfiable"):
				state = "saturation"
				break
			elif line.startswith("User error: "):
				state = "error"
				break
		if state == "none":
			self.vampireState = "error"
		else:
			self.vampireState = state
		return lines

	# start Vampire with manual clause selection on the given input file, until Vampire asks for a clause to select or finishes execution
	# return the output generated before asking for a clause
	def startManualCS(self, inputFile):
		if self.vampireProcess != None:
			self.vampireProcess.kill()
		self.vampireProcess = Popen(["/Users/bernhard/repos/vampire-release/vampire_rel_manualcl_4057", "--input_syntax", "smtlib2", "-av", "off", inputFile, "--manual_cs", "on", "--show_preprocessing", "on", "--show_new", "on", "--show_passive", "on", "--show_active", "on", "--show_reductions", "on", "--proof_extra", "full", "--time_limit", "0"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		
		newLines = self.collectOutput()
		return newLines

	# perform one clause selection using selectedId
	# return the output generated by that clause selection
	def select(self, selectedId):
		self.vampireProcess.stdin.write(str.encode(str(selectedId) + "\n"))
		self.vampireProcess.stdin.flush()

		newLines = self.collectOutput()
		return newLines

	# helper method
	def collectOutput(self):
		# process lines until a line occurs with either is 1) a commando to enter a number 2) refutation found 3) saturation reached 4) user error
		newLines = []
		line = self.vampireProcess.stdout.readline().decode().rstrip()
		while(True):
			if line.startswith("Pick a clause from:"):
				self.vampireState = "running"
				self.remainingChoices = list(map(lambda id: int(id), line[20:-1].split(","))) # remove "Pick a clause from: " and last comma, then split by commas, then convert to ints
				return newLines
			elif line.startswith("% Refutation found. Thanks to"): # TODO: use SZS status instead?
				self.vampireState = "refutation"
				self.remainingChoices = None
				return newLines
			elif line.startswith("% SZS status Satisfiable"):
				self.vampireState = "saturation"
				self.remainingChoices = []
				return newLines
			elif line.startswith("User error: "):
				self.vampireState = "error"
				self.remainingChoices = None
				return newLines
			else:
				newLines.append(line)
				line = self.vampireProcess.stdout.readline().decode().rstrip()
