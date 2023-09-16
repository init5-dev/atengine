import json

if __name__=='__main__':
	conf = {
	"retries": 3, 
	"retries-after-error": 3, 
	"error-latency": 10, 
	"latency": 1
	}
	with open('atengine.conf', 'w') as file:
		json.dump(conf, file, indent=4)