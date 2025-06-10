#For raspberry pi pico 2W w/ micropython
import network
import socket
import ujson
import time

# Connect to network
ssid = ''
password = ''

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(0.001)

print('IP: ', wlan.ifconfig()[0])

# Tcp client
HOST = '' #Host IP
PORT = 12345
id_no = '0'  # id of the corresponding marker

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
print('Connected to server')

while True:
    try:
        # Receive the data
        raw_data = client_socket.recv(1024)
        if raw_data:
            location_data = raw_data.decode()
            data = ujson.loads(location_data)
            if id_no in data:
                print(data[id_no])  # Do something with data
    except KeyboardInterrupt:
        client_socket.close()
        print('Connection closed')

