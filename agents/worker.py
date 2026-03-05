from core.engine import NandhiEngine
import socket
import json

engine = NandhiEngine()

HOST = "localhost"
PORT = 9000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

while True:
    conn, addr = server.accept()
    data = conn.recv(4096).decode()
    request = json.loads(data)

    response = engine.generate_reply(request["input"])

    conn.send(json.dumps({"output": response}).encode())
    conn.close()