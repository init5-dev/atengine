STOP = 1
CORRECT = 2
PAUSE = 3
TRY = 4
OPENAI_ERROR = 5
UNHANDLED = 6
TRIES_EXHAUSTED = 7

def code2str(code):
	events = ''

	if code == STOP:
		event = 'STOP'
	elif code == PAUSE:
		event = 'PAUSE'
	elif code == CORRECT:
		event = 'CORRECT'
	elif code == TRY:
		event = 'TRY'
	elif code == OPENAI_ERROR:
		event = 'OPENAI ERROR'
	elif code == UNHANDLED:
		event = 'UNHANDLED'
	elif code == TRIES_EXHAUSTED:
		event = 'TRIES EXHAUSTED'

def isCode(value):
	if value == STOP or value == CORRECT or value == PAUSE or value == TRY or value == OPENAI_ERROR or value == UNHANDLED or value == TRIES_EXHAUSTED:
		return True
	else:
		return False