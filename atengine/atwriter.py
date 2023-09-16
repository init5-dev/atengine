'''FUNCIONES QUE FALTAN POR IMPLEMENTAR:

1. KEYWORDS
Escribe un articulo SEO cuyo tema sea "Consejos para comprar una casa". La frase "comprar una casa" debe repetirse en cada párrafo.
'''

import re
from time import sleep
import os
import sys
import openai
import json
import time

try:
	from atcode import *
except:
	from app.packages.atengine.atcode import *

try:
	from atchat import AtChat
except:
	from app.packages.atengine.atchat import AtChat

try:
	from atutils import AtUtils
	from atutils import AnswerFormatException
except:
	from app.packages.atengine.atutils import AtUtils
	from app.packages.atengine.atutils import AnswerFormatException

### GLOBALS ###

EMPTY_ANSWER = {
					'type' : 'answer', 
					'content' : {
									'title' : '',
									'body' : ''
								}
				}

EMPTY_ARTICLE = {
					'type' : 'answer', 
					'content' : ''
				}

### ATWRITER ###

class AtWriter(AtChat):
	
	def __init__(self, apikey = '', autoIntro = True, metadescription = True, verbose=True):

		self.debugMode = False

		super(AtWriter, self).__init__(apikey=apikey)

		self.start(autoIntro, metadescription, verbose)

	def start(self, autoIntro = True, metadescription = True, verbose=True):
		systemInstructions = '''
Quiero que seas un escritor de articulos long-format, y que sigas estrictamente cada una de mis instrucciones. Yo te daré instrucciones siguiendo esta sintaxis:

	#AMBITO: Ámbito temático del texto que vas a escribir.
	#TITULO: Título del texto que vas a escribir o el valor "#ninguno", el cual te indica que el texto que vas a escribir tendrá "<h2></h2>" como titulo.
	#AUTOR: Autor del texto que vas a escribir; deberás escribir como si fueras dicho autor (esta es una regla que debes seguir al pie de la letra).
	#PÚBLICO OBJETIVO: Público objetivo del texto que vas a escribir.
	#FUNCION: Función del texto que vas a escribir. Por ejemplo: texto independiente (valor: "#indep"), introducción de un artículo (valor: #intro) o sección de artículo (valor: #sect)
	#INSTRUCCIONES:
		- Instrucción de redacción 1.
		- Instrucción de redacción 2.
		- Instrucción de redacción 3.
		- ...
		- Instrucción de redacción n.

Como respuesta, siempre me brindarás un texto HTML long-format encapsulado en el siguiente formato estricto:

	#TITULO:
	<h2>Titulo del texto</h2> o <h2></h2> si no te proporcioné un título.

	#CUERPO:
	Cuerpo del texto; cada párrafo encerrado entre etiquetas <p> y </p>.

Siempre debes poner las etiquetas #TITULO: y #CUERPO.

Por ejemplo, te doy las siguientes instrucciones:

	#AMBITO: ChatGPT
	#TITULO: Qué es ChatGPT
	#FUNCION: #sect
	#INSTRUCCIONES:
		- Un solo párrafo.
		- Estilo amigable.
		- Segunda persona.
		- Dirigirse al lector como Ud.
		
Y tú respondes como sigue:

	#TITULO:
	<h2>Que es ChatGPT</h2>

	#CUERPO:
	<p>¿Sabe qué es ChatGPT? ¡Nada menos que la mayor innovación de nuestra época! Se trata de una aplicación de chat que emplea IA generativa para interactuar con seres humanos como si fuera uno de ellos. Así que, si no lo ha probado, ¡es hora de que lo haga! Descubrirá todo un nuevo universo de posibilidades con esta tecnología de última generación. Y es que, con ChatGPT, usted puede desde tener una conversación de sus temas preferidos, hasta escribir una novela. ¿No me cree? Haga la prueba y ya me dirá.</p?
		'''
		

		self.messages = [{'role':'system', 'content':systemInstructions}]
		self.autoIntro = autoIntro
		self.metadescription = metadescription
		self.verbose=verbose
		self.__retries = self.__getConfigValue('retries')
		self.__retriesAfterError = self.__getConfigValue('retries-after-error')
		self.__retriesAfterErrorCount = 0
		self.__errorLatency = self.__getConfigValue('error-latency')
		self.__latency = self.__getConfigValue('latency')
		self.cancel = False
		self.indexProgress = []

		#REGISTRO DE CHUNKS PARA RECUPERAR EN CASO DE NO COMPLETARSE EL ARTICULO
		self.contentChunks = {}
		self.finished = False

		self.frequencyPenalty = 1.6
		self.presencePenalty = 1.9

		#Utilidades
		self.utils = AtUtils(self.apikey)
		self.printQueue = []
		
	def __traceInConsole(self, text):
		if self.debugMode:
			print(text)
	
	def __get_platform(self):

		platforms = {
	        'linux1' : 'Linux',
	        'linux2' : 'Linux',
	        'darwin' : 'OS X',
	        'win32' : 'Windows'
		}

		if sys.platform not in platforms:
			return sys.platform

		return platforms[sys.platform]

	def print(self, message):
		print('\n#######################################################')
		print('')
		print(message)
		print()
		print('#######################################################')
		print('')
		self.printQueue.append(message)

	def getLastPrint(self):
		if len(self.printQueue):
			return self.printQueue[-1]
		else:
			return '<0-PRINTS>'

	def setVerbose(self, value):
		self.verbose = value

	def setRetries(self, value):
		self.__retries = value

	def getRetries(self):
		return self.__retries

	def setRetriesAfterError(self, value):
		self.__retriesAfterError = value

	def getRetriesAfterError(self):
		return self.__retriesAfterError

	def setErrorLatency(self, value):
		self.__errorLatency = value

	def getErrorLatency(self):
		return self.__errorLatency

	def setLatency(self, value):
		self.__latency = value

	def getLatency(self):
		return self.__latency

	def __del__(self):
		self.__traceInConsole('ATWRITER: OBJECT TERMINATED.')

	def __getConfigValue(self, variable):
		slashChar = '/'

		if self.__get_platform() == 'Windows':
			filename = 'atengine.conf'
		else:
			currPath =  os.path.dirname(os.path.realpath(__file__))

			if currPath.find('atengine') > -1:
				filename = currPath + '/' + 'atengine.conf'
			else:
				filename = currPath + '/' + 'atengine/atengine.conf'

		with open(filename, 'r') as file:
			conf = json.load(file)
			self.__traceInConsole('{} = {}'.format(variable, conf[variable]))
			return conf[variable]

	def createContentChunks(self, scope, index):
		#print('!!!!CREATE CONTENT CHUNKS!!!!')
		self.contentChunks = {}
		self.contentChunks['title'] = {'state':'undone'}
		self.contentChunks['index-config'] = {'state':'undone'}
		self.contentChunks['meta'] = {'state':'undone'}
		self.contentChunks['intro'] = {'state':'undone'}

		if len(index) == 0:
			self.contentChunks[scope] = {'state':'undone'}
		else:
			for entry in index:
				self.contentChunks[entry] = {'state':'undone'}

	def completeChunk(self, key):
		self.contentChunks[key]['state'] = 'done'
		#print('CONTENT CHUNKS UPDATED:"%s": %s' % (key, self.contentChunks[key]))

	def isChunkComplete(self, key):
		result = self.contentChunks[key]['state'] == 'done'
		#print('CHUNK "%s is done: %s' % (key, result))
		return result

	def isFinished(self):
		return self.finished

	def cancellate(self):
		self._stop = True
		self.cancel = True

	def reset(self):
		self.start()

	def resetMessages(self, from_message=1):
		self.messages = self.messages[0:from_message]

	def setAutoIntro(self, value):
		self.autoIntro = value

	def setMetadescription(self, value):
		self.metadescription = value

	def __tryUntilCorrect(self, f, *args, **kwargs):

		if self.cancel:
			return EMPTY_ANSWER
		
		answer = None
		correct = False
		i = 0

		while not correct and i < self.__retries:
			dic = {}
			answer = f(*args, **kwargs)

			if self.cancel or not answer:
				return EMPTY_ANSWER
			
			try:

				dic = self.utils.output2Dict(answer)
				correct = True

			except AnswerFormatException:
				self.print('GPT no respondió de manera correcta. Reintentando en %s segundos...' % self.__latency)
				sleep(self.__latency)
				correct = False

			i = i + 1

		if correct:
			return { 
				'type' : 'answer', 
				'content' : { 
								'title' : dic['title'].strip(), 
								'body'  : dic['body'].strip() 
							} 
					}
		else:
			return EMPTY_ANSWER

	def __super_answer(self, command, secure_execution = True):

		#self.print('EJECUTANDO COMANDO:\n%s' % command)
		if secure_execution:
			answer = self.secure_execution(super().answer, command)
		else:
			answer = super().answer(command)

		#self.print('GPT RESPONDE:\n%s' % answer)
		return answer


	def answer(self, command):
		
		if self.cancel:
			return EMPTY_ANSWER

		answer = self.__tryUntilCorrect(self.__super_answer, command)
		sleep(self.__latency) #duerme el tiempo especificado para no sobrecargar a GPT de solicitudes

		return answer

	def meta(self, keyphrase, style, extra):
		
		maxTokens = self.maxTokens
		temperature = self.temperature
		presencePenalty = self.presencePenalty
		frequencyPenalty = self.frequencyPenalty
		topP = self.topP
		self.maxTokens = 100
		self.temperature = 0.6
		self.presencePenalty = 0.25
		self.frequencyPenalty = 0.25
		self.topP = 1

		command = '''
> Sigue estrictamente mis instrucciones. Quiero que escribas una sola, única y breve oración que invite a leer un artículo basado en la siguiente keyphrase: '{}'.
> Tono y estilo de la oración: '{}'.
> Instrucciones adicionales: 

{}
- No saludes al lector ni hagas referencia explícita o literal al público objetivo.

> Formato de tu respuesta (obligatorio):

#TITULO: <h2>Metadescripción</h2>
#CUERPO:
	Oración que te pedí.'''.format(keyphrase, style, extra)

		yield   {
					'type' : 'message', 
					'content': 'Escribiendo metadescripción.'
				}

		answer = self.answer(command)

		self.maxTokens = maxTokens
		self.temperature = temperature
		self.presencePenalty = presencePenalty
		self.frequencyPenalty = frequencyPenalty
		self.topP = topP

		if answer == EMPTY_ANSWER:
			yield answer
		else:
			yield   { 
						'type' : 'answer', 
						'content' : {
										'title' : '',
										'body' : '<p id="meta"><b>Metadescripción:</b> %s</p>' % answer['content']['body']

									} 
					}
	
	def introduction(self, scope, author, reader, style, extraInstructions):
		command='''
#AMBITO: {}.
#TITULO: Introducción.
#AUTOR: {}.
#PÚBLICO OBJETIVO: {}.
#TONO Y ESTILO: {}.
#FUNCION: #intro
#INSTRUCCIONES ADICIONALES:
- Evita dar definiciones.
- No saludes al lector ni hagas referencia explícita o literal al público objetivo. 
{}
		'''.format(scope, author, reader, style, extraInstructions)

		if self.cancel:
			yield EMPTY_ANSWER
		else:
			yield   {
						'type': 'message', 
						'content': 'Escribiendo introducción.'
					}
		
			answer = self.answer(command)

			yield   { 
						'type' : 'answer', 
						'content' : {
										'title' : '',
										'body' : answer['content']['body']

									} 
				    }

	def section(self, scope, title, author, reader, style, extraInstructions):
		
		if len(self.indexProgress) > 10:
			i = 1
			if self.metadescription:
				i += 1
			if self.autoIntro:
				i += 1

			self.resetMessages(from_message = i)
			self.indexProgress = []

		command='''
#AMBITO: {}.
#TITULO: {}.
#AUTOR: {}.
#PÚBLICO OBJETIVO: {}.
#TONO Y ESTILO: {}.
#FUNCION: #sect
#INSTRUCCIONES:
{}
- Esta sección es una continuación del tema; forma parte de un artículo que estás escribiendo. 
- Sigue estrictamente esta instrucción: evita usar las frases "en resumen" o "en conclusión". 
- Sigue estrictamente esta instrucción: no saludes al lector ni introduzcas el tema.
- No saludes al lector ni hagas referencia explícita o literal al público objetivo.
		'''.format(scope, title, author, reader, style, extraInstructions)

		if self.cancel:
			yield EMPTY_ANSWER
		else:
			yield   {
						'type' : 'message', 
						'content' : 'Escribiendo sección "%s".' % title
					}

			'''if len(self.indexProgress):
				prevContent = '#TITULO:\n<h2>%s</h2>\n\n#CUERPO:\n<p>Párrafo sobre "%s"</p>' % (self.indexProgress[-1], self.indexProgress[-1])
			else:
				prevContent = '''

			answer = self.answer(command)
			self.indexProgress.append(title)
			yield answer

	def sections(self, scope, author, reader, style, extraInstructions, index):
	
		if len(index) == 0:

			if not self.isChunkComplete(scope):

				command = '''
#AMBITO: {}.
#TITULO: {}.
#AUTOR: {}.
#PÚBLICO OBJETIVO: {}.
#TONO Y ESTILO: {}.
#FUNCION: #indep
#INSTRUCCIONES:
{}
- Te prohibo que uses las frases "en resumen" o "en conclusión".
				'''.format(scope, scope, author, reader, style, extraInstructions)

				if self.cancel:
					yield EMPTY_ANSWER
				else:
					yield   {
								'type' : 'message', 
								'content' : 'Escribiendo: "%s".' % scope
							}

					answer = self.answer(command)

					if answer == EMPTY_ANSWER:
						yield answer
						self.indexProgress.append(scope)
					else:
						yield   { 
								'type' : 'answer', 
								'content' : {
												'title' : '',
												'body' : answer['content']['body']

											} 
								}

						self.completeChunk(scope)

		else:

			if self.cancel:
				yield EMPTY_ANSWER
			else:

				sections = []

				for indexItem in index:
					if not self.isChunkComplete(indexItem):
						for chunk in self.section(scope, indexItem, author, reader, style, extraInstructions):
							if chunk == EMPTY_ANSWER:
								return chunk
							else:
								yield chunk
						self.completeChunk(indexItem)

	def article(self, scope, author, reader, style, extraInstructions, index, wait=0):

		article = EMPTY_ARTICLE

		if wait and not self.cancel:
			for t in range(wait, 1):

				yield   {
							'type' : 'message', 
							'content' : 'Esperando %s s para no sobrecargar el servidor.' % t
						}

				time.sleep(1)

		if self.finished:
			self.resetMessages()
			
		if not len(self.contentChunks):
			self.createContentChunks(scope, index)

		#GENERAR TITULO

		if not self.isChunkComplete('title'):

			title = '<h1>%s</h1>' % scope

			yield   {
						'type' : 'answer', 
						'content' : {
										'title' : title,
										'body'	: ''
									}
					}

			self.completeChunk('title')

		#CONFIGURAR INDICE

		if not self.isChunkComplete('index-config'):

			if index:
				if len(index) == 1 and not self.autoIntro: #si el indice solo tiene una entrada y el autointro esta desactivado
					self.autoIntro = True

				if len(index) == 0: #si el indice esta vacio y el autointro esta activado
					if self.autoIntro:
						self.autoIntro = False

			self.completeChunk('index-config')
			self.chooseModel(index)

		#GENERAR METADESCRIPCION

		if self.metadescription:

			if not self.isChunkComplete('meta'):

				stopped = False

				for chunk in self.meta(scope, style, extraInstructions):
					if chunk == EMPTY_ANSWER:
						yield chunk
						stopped = True
						break
					else:
						yield chunk

				if not stopped:
					self.completeChunk('meta')

		#GENERAR INTRODUCCION

		if self.autoIntro:

			if not self.isChunkComplete('intro'):

				stopped = False

				for chunk in self.introduction(scope, author, reader, style, extraInstructions):

					if chunk == EMPTY_ANSWER:
						yield chunk
						stopped = True
						break
					else:
						yield chunk
				
				if not stopped:
					self.completeChunk('intro')

		#GENERAR SECCIONES

		for chunk in self.sections(scope, author, reader, style, extraInstructions, index):
			if chunk == EMPTY_ANSWER:
				return chunk
			else:
				yield chunk

		#FINALIZAR
		self.finished = True

	def chooseModel(self, index):
		n = 1
		if self.metadescription:
			n += 1
		if self.autoIntro:
			n += 1

		n += len(index)

		if n > 7:
			if self.model == 'gpt-3.5-turbo':
				self.setModel('gpt-3.5-turbo-16k')
				print('ARTICULO MUY EXTENSO. CAMBIADO EL MODELO A: gpt-3.5-turbo-16k')


	def suggestIndex(self, scope, reader, style, min_index_items=3):
		return self.secure_execution(self.__suggestIndex, scope, reader, style, min_index_items)


	def __suggestIndex(self, scope, reader, style, min_index_items=3):
		command = '''
Completa el siguiente texto:

Escribiré un artículo extenso cuyo tema será '{}', su tono y estilo será '{}' y su lector o público objetivo será '{}'. Su listado de contenidos sin introducción lucirá exactamente como sigue:
		'''.format(scope, reader, style) 

		response = None
		answer = '' 
		rlines = []

		i = 0

		while not len(answer) or (len(rlines) <= min_index_items and not self._fast_testing_mode):
			
			if i >= self.__retries:
				break
				
			if self._fast_testing_mode:
				response = openai.Completion.create(engine='text-curie-001', prompt=command + " ", max_tokens=40, temperature=0, top_p=0.25, frequency_penalty=0, presence_penalty=0)
			else:
				response = openai.Completion.create(engine='text-davinci-003', prompt=command + " ", max_tokens=200, temperature=0.6, top_p=1, frequency_penalty=0.6, presence_penalty=0.6)
				
			answer = response["choices"][0]["text"].strip()

			print('INDICE: %s' % answer)

			if len(answer):
				rlines = []
				lines = answer.splitlines()
				for line in lines:
					if len(line.strip()):
						line = line.replace('\t', ' ')
						rlines.append(line)

			i = i +1

		result = ''
		for rline in rlines:
			result = result + rline.strip() + '\n'
		result = re.sub(r'[\w\d]+\. ', '', result)
		result = re.sub(r'[\w\d]+: ', '', result) 
		result = re.sub(r'[\w\d]+ [-]+ ', '', result)
		result = re.sub(r'[-]+ ', '', result)
		result = result.strip() 		

		return result

	def errorMessage(self, message, title, exc_info=False):
		self.print(title + ': ' + message)
		if exc_info:
			excinfo = sys.exc_info()
			print(title + ': ' + message + ('\nINFORMACION DE LA EXCEPCION:\nTIPO: %s\nVALOR: %s\nTRAZA: %s ' % excinfo))
		else:
			print('ERROR' + title + ': ' + message)
	
	def __intent_times_str(self):
		if self.__retriesAfterErrorCount == 1:
			return '.'

		if self.__retriesAfterErrorCount >= 2:
			return ' por %sª vez.' % self.__retriesAfterErrorCount


	def secure_execution(self, f, *args, **kwargs):
		try:

			return f(*args, **kwargs)

		except openai.error.APIError as e:

			if self._stop:
				return EMPTY_ANSWER

			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="Error de OpenAI. Esperando para reintentar" + self.__intent_times_str(), title="Error de OpenAI", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="Error de OpenAI. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.", title="Error de OpenAI", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e

		except openai.error.Timeout as e:

			if self._stop:
				return EMPTY_ANSWER

			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="Error de OpenAI. Esperando para reintentar" + self.__intent_times_str(), title="Error de OpenAI", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="Tiempo de espera agotado. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.", title="Error de OpenAI", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e

		except openai.error.RateLimitError as e:

			if self._stop:
				return EMPTY_ANSWER
		
			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="Cuota excedida. Esperando para reintentar" + self.__intent_times_str(), title="Error de conexión", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="Cuota excedida. Comprueba tu plan y detalles de facturación en https://platform.openai.com/account/.", title="Cuota excedida", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e
			
		except openai.error.APIConnectionError as e:

			if self._stop:
				return EMPTY_ANSWER
				
			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="¡No hay conexión! Esperando para reintentar" + self.__intent_times_str(), title="Error de conexión", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="Por favor, asegúrate de que tienes conexión a Internet.", title="Error de conexión", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e
					
		except openai.error.InvalidRequestError as e:

			if self._stop:
				return EMPTY_ANSWER
			
			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1

			self.setModel('gpt-3.5-turbo-16k')
			print('ES POSIBLE QUE SE HAYA ALCANZADO EL LIMITE DE TOKENS DEL MODELO. SE HA CAMBIADO EL MODELO A: gpt-3.5-turbo-16k')
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="GPT no entendió bien la orden. Esperando para reintentar" + self.__intent_times_str(), title="Error de conexión", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="¡Atwood falló! Hay algo mal en el código. Por favor, contacta con el desarrollador usando este email: nelson.ochagavia@gmail.com. Enviale este texto:\n ERROR: openai.error.InvalidRequestError\nARGS = %s\nKWARGS = %s" % (args, kwargs), title="¡Atwood falló!", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e
			
		except openai.error.AuthenticationError as e:

			if self._stop:
				return EMPTY_ANSWER
			
			self.errorMessage(message="API key incorrecta. Busca tu API key en https://platform.openai.com/account/api-keys y regístrala aquí en Atwood.", title="API key incorrecta", exc_info=True)
			raise e 
			
		except openai.error.ServiceUnavailableError as e:

			if self._stop:
				return EMPTY_ANSWER

			self.__retriesAfterErrorCount = self.__retriesAfterErrorCount + 1
				
			if self.__retriesAfterErrorCount <= self.__retriesAfterError:
				self.errorMessage(message="Servidor de OpenAI sobrecargado. Esperando para reintentar" + self.__intent_times_str(), title="Servidor sobrecargado", exc_info=True)
				sleep(self.__errorLatency)
				return self.secure_execution(f, *args)
			else:
				self.errorMessage(message="¡El servidor de OpenAI sigue sobrecargado! Inténtalo más tarde. Y, si estás usando la prueba gratuita de GPT, es buena idea adquirir un plan de pago.", title="Servidor sobrecargado.", exc_info=True)
				self.__retriesAfterErrorCount = 0
				raise e
		except Exception as e:

			if self._stop:
				return EMPTY_ANSWER
			
			self.errorMessage(title='Error inesperado', message=str(e), exc_info=True)
			raise e