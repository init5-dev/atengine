from cryptography.fernet import Fernet
import os

def generate_key(keyfilename):
    if not os.path.exists(keyfilename):
        key = Fernet.generate_key()
        with open(keyfilename, 'wb') as file:
            file.write(key)

def read_key(keyfilename):
    with open(keyfilename, 'rb') as file:
        return file.read()

def write_file(key, filename, content):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(content.encode())
    with open(filename, 'wb') as file:
        file.write(encrypted)

def read_file(key, filename):
    fernet = Fernet(key)
    with open(filename, 'rb') as file:
        decrypted = fernet.decrypt(file.read())
    return decrypted.decode()


if __name__=='__main__':
    text = 'Hola, amigo.'
    #generate_key('atwood-secret.key')
    #key = read_key('atwood-secret.key')
    key = 'ep-k9CZ0JPRWKgiz1xil0jZNkls5SIuR87XgNN6ZuN4='
    write_file(key, 'encrypted.txt', text)
    print(read_file(key, 'encrypted.txt'))