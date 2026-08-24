import socket
import threading
import time
from Detector import Detector
import json

HOST = '' #Host IP
PORT = 12345
client_list = []
gps_f = Detector()

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    client_list.append(conn)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))
server.listen()

print("Server listening")

#Accept clients in the background
def accept_clients():
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

threading.Thread(target=accept_clients, daemon=True).start()

threading.Thread(target=gps_f.scan).start()

#Send data to all clients
try:
    while True:
        location_data = gps_f.get_locations()
        if location_data:
            data = json.dumps(location_data, indent=4)
            for client in client_list:
                try:
                    client.sendall(data.encode())
                except ConnectionResetError:
                    client_list.remove(client)
        time.sleep(1.5)
except KeyboardInterrupt:
    server.close()
    print("Server closed")

