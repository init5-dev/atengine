import openai
import re

class AtChat:

	def __init__(self, apikey, memory=10, systemContent='Eres un chatbot.', userContent1='Hola, ¿cómo estás?', assistantContent='Hola, ¿cómo te puedo ayudar?'):
		self.messages = [{'role':'system', 'content':systemContent}, {'role':'user', 'content': userContent1}, {'role':'assistant', 'content':assistantContent}]
		self.prompt_tokens = 0
		self.completion_tokens = 0
		self.total_tokens = 0
		self.price = 0
		self.model='gpt-3.5-turbo'
		self.temperature=0.9
		self.frequencyPenalty=0.6
		self.presencePenalty=0.6
		self.maxTokens=750
		self.topP=1.0
		self.apikey=apikey
		self._fast_testing_mode = False
		self._stop = False

		#evito que se vuelva a llamar a API cuando ya se ha hecho
		if openai.api_key != apikey:
			openai.api_key=apikey

	def stop(self):
		"""_summary_ dsfsdfsdfsfsfsd
		"""		
		self._stop = True

	def fast_testing_mode(self, value):
		if value:
			self._fast_testing_mode = True
			self.temperature=0
			self.frequencyPenalty=0
			self.presencePenalty=0
			self.maxTokens=50
			self.topP=0
		else:
			self._fast_testing_mode = False
			self.temperature=0.9
			self.frequencyPenalty=0.6
			self.presencePenalty=0.6
			self.maxTokens=750
			self.topP=1.0

	def completion(self):

		answer = ''

		for chunk in openai.ChatCompletion.create(
				model=self.model,
				messages=self.messages,
				temperature=self.temperature,
				top_p=self.topP,
				frequency_penalty=self.frequencyPenalty,
				presence_penalty=self.presencePenalty,
				max_tokens=self.maxTokens,
				request_timeout = 15,
				stream = True,
			):
				if self._stop:
					print('COMPLETION STOPED!')
					answer = None
					break

				token = chunk['choices'][0].get('delta', {}).get('content')

				if token is not None:
					answer = answer + token

		return answer

	def answer(self, input):
		output = '''
FAST_TESTING_MODE={}
TEMPERATURE={}
FRECUENCY_PENALTY={}
PRESENCE_PENALTY={}
MAX_TOKENS={}
TOP_P={}
		'''.format(self._fast_testing_mode, self.temperature, self.frequencyPenalty, self.presencePenalty, self.maxTokens, self.topP)
		#print(output)

		self.messages = self.messages + [{'role':'user', 'content':input}]
		self._stop = False

		answer = self.completion()

		if answer:
			self.messages = self.messages + [{'role':'assistant', 'content':answer}]
		
		return answer

	def setAPIKey(self, apikey):
		self.apikey=apikey
		openai.api_key = apikey

	def setModel(self, model):
		self.model = model

	def tokenUsage(self):
		return {'prompt_tokens':self.prompt_tokens, 'completion_tokens':self.completion_tokens, 'total_tokens': self.total_tokens}




if __name__ == '__main__':
	chat = AtChat("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")

	while True:
		prompt = input('Yo: ')
		print('ChatGPT:', end=' ')
		if prompt.strip().lower() == 'salir':
			break
		ans = chat.answer(prompt)
		print(ans)