from bs4 import BeautifulSoup

try:
	from atchat import AtChat
except:
	from app.packages.atengine.atchat import AtChat

def remove_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

class AnswerFormatException(Exception):
	pass

class AtUtils(AtChat):
	def __init__(self, apikey):
		super().__init__(apikey=apikey)

	def reset(self):
		self.messages = self.messages[:2]

	def makeDeterministic(self, maxTokens = 50):
		self.temperature=0
		self.frequencyPenalty=0
		self.presencePenalty=0
		self.maxTokens=maxTokens
		self.topP=0

	def makeCreative(self):
		self.temperature=0.9
		self.frequencyPenalty=0.6
		self.presencePenalty=0.6
		self.maxTokens=1000
		self.topP=1.0
	
	def isReadable(self, text):
		comando = 'Responde solamente "True#" si el texto que te proporcionaré podria tener sentido; de lo contrario, responde solamente "False#.". El texto es: "{}".'.format(text)
		self.makeDeterministic(maxTokens=10)
		result = self.answer(comando)
		self.makeCreative()
		if result == 'True#':
			return True
		return False

	def inScope(self, term, scope):
		self.reset()
		comando = 'Responde "Sí" si el término "{}" pertenece al tema "{}"; de lo contrario, responde "No"'.format(term, scope)
		self.makeDeterministic(maxTokens=50)
		result = self.answer(comando)
		print(result)
		self.makeCreative()
		if result.find('Sí') > -1:
			return True
		return False

	def getNiche(self, text):
		self.reset()
		comando = '''
Te proporcionaré un texto, y tu responderás con el nombre del ámbito temático al cual pertenece dicho texto. Tu respuesta solo puede contener el nombre del nicho; nada más. El texto es: 

"{}"
'''.format(text)
		self.makeDeterministic(maxTokens=75)
		result = self.answer(comando)
		self.makeCreative()
		return result

	def languageOf(self, text):
		comando = '''
		Sigue estrictamente mis instrucciones.

		Te daré un texto. 

		Si reconoces un solo idioma dentro del texto, responde con la siguiente cadena: "#<idioma del texto>"; el idioma del texto debe estar en perfecto Español.

		Si no estás seguro del idioma, responde con "#NA".

		Si hay más de un idioma, responde con una lista de los idiomas que hayas reconocido, empleando la sintaxis: "#lista: <nombre idioma 1>, <nombre idioma 2>, etc." 

		El texto es: "{}".'''.format(text)
		self.makeDeterministic(maxTokens=1000)
		result = self.answer(comando)
		self.makeCreative()
		result = result.strip()
		ilist = [] 
		startIndex = result.find('#lista:')
		if startIndex > -1:
			startIndex = startIndex + len('#lista:')
			ilist = result[startIndex:].split(',')
			for i in range(len(ilist)):
				ilist[i] = ilist[i].strip()
			return ilist
		else: 	
			return result[1:]

	def formatInstructions(self, instructions):
		#Elimina espacio y tabulaciones al principio y al final, y agrega # para indicar fin de las instrucciones.
		#Luego formatea para que cada oracion aparezca en una linea diferente.
		result = '- ' + (instructions.strip() + '#').replace('.', '.\n-').replace('.\n-#', '.')
		return result

	def _get_title(self, output):
		start = output.find("#TITULO:") + len("#TITULO:")
		end = output.find("#CUERPO:")
		#print("START: {}, END:{}".format(start, end))
		
		if start == len("#TITULO:")-1 or end == -1:
			#print("DEBUG - RESPUESTA DE GPT:\n{}".format(output))
			raise AnswerFormatException('La respuesta de GPT tiene un formato incorrecto. No se identifica el titulo.')

		return output[start:end].strip()

	def _get_body(self, output):
		start = output.find("#CUERPO:") + len("#CUERPO:")
		#print("START: {}".format(start))
		
		if start == len("#CUERPO:")-1:
			raise AnswerFormatException('La respuesta de GPT tiene un formato incorrecto. No se identifica el cuerpo.')

		return output[start:].strip()

	def output2Dict(self, output):
		#print("DEBUG - SALIDA DE GPT:\n{}".format(output))

		title = ''
		body = ''
		
		title = self._get_title(output)
		body = self._get_body(output)
		
		return {'title' : title, 'body' : body}

	def subject(self, sentence):
		self.makeDeterministic()
		command = '''
Te proporcionaré un título, y tú extraerás el sujeto de la oración. Responderás con la siguiente sintaxis: "#AMBITO: sujeto de la oración". El título es el siguiente: "{}"."
'''.format(sentence)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer

	def directComplement(self, sentence):
		self.makeDeterministic()
		command = '''
Te proporcionaré un título, y tú extraerás el complemento directo de la oración. Responderás con la siguiente sintaxis: "#AMBITO: complemento directo de la oración". El título es el siguiente: "{}"."
'''.format(sentence)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer

	def topicFromTitle(self, title):
		self.makeDeterministic()
		command = '''
Te proporcionaré un título, y tú me dirás el nombre de la cosa o persona concreta, no abstracta, a la cual hace referencia el título, basándote en el sujeto de la oración. Responderás con la siguiente sintaxis: "#SUJETO: <cosa o persona>". El título es el siguiente: "{}"."
'''.format(title)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer

	def titleFromSentence(self, sentence):
		self.makeDeterministic()
		command = '''
Te proporcionaré una oración, y tú la convertirás en un título si es necesario. Responderás con la siguiente sintaxis: "#AMBITO: palabra". El título es el siguiente: "{}"."
'''.format(sentence)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer

	def titleFromIntro(self, introduction):
		self.makeDeterministic()
		command = '''
Te proporcionaré la introducción de un artículo, y tú generarás un título apropiado a partir de dicha introducción. Responderás con la siguiente sintaxis: "<h1>Titulo</h1>". 

La introducción es la siguiente: 

{}
'''.format(introduction)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer

	def titleFromText(self, text):
		self.makeDeterministic()
		command = '''
Te proporcionaré un texto, y tú generarás un título apropiado a partir de dicho texto. Responderás con la siguiente sintaxis: "<h1>Titulo</h1>". 

El texto es el siguiente: 

{}
'''.format(text)
		#print(command)
		answer = self.answer(command)
		self.makeCreative()
		return answer


if __name__=="__main__":
	atu = AtUtils('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')
	term = 'Todo sobre la enseñanza de Buda'
	print(atu.getNiche(term))
	term = 'Para que sirve PyQt5'
	print(atu.getNiche(term))
	
