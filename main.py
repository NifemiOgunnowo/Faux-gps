#For raspberry pi pico 2W w/ micropython
import network
import socket
import ujson
import time
import machine

# Uart output set up
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

# Network info
ssid = '???'
password = '12345678'

# Tcp client
HOST = '172.20.10.10' #Host IP
PORT = 12345

id_no = '0'  # id of the corresponding marker

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    for i in range(100):
        if wlan.isconnected():
            print('Connection successful ;IP: ', wlan.ifconfig()[0])
            return True
        time.sleep(0.5)

    return False

def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print('Connected to server')

    while True:
            # Receive the data
            raw_data = client_socket.recv(1024)
            if raw_data:
                location_data = raw_data.decode()
                data = ujson.loads(location_data)
                if id_no in data:
                    # Do something with data
                    print(data[id_no])
                    uart.write(data[id_no])

def main():
    if connect_wifi():
        try:
            run_client()
        except Exception as e:
            print('Client connection failed ', e)
    else:
        print('Wifi connection failed, retrying in 10 seconds')
        time.sleep(10)
        machine.reset()

main()