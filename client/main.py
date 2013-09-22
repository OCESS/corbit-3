from socket import *
import pickle

HOST = 'localhost'    # The remote host
PORT = 31415          # The same port as used by the server

sock = socket(AF_INET, SOCK_STREAM)
sock.connect((HOST, PORT))
sock.sendall(b'quantum spin device calibrated')
data = sock.recv(1024)
ent = pickle.loads(data)
print(ent.name)
sock.close()
print('Received', repr(data))
while True:
    None