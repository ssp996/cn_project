import socket

SERVER_IP = '10.0.0.2'
SERVER_PORT = 5000

BUFFER_SIZE = 1024
MESSAGE = "bruh"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    print(f"Sending message to {SERVER_IP}:{SERVER_PORT}")
    client_socket.sendto(MESSAGE.encode('utf-8'), (SERVER_IP, SERVER_PORT))
    
    data, server_address = client_socket.recvfrom(BUFFER_SIZE)
    print(f"Response from server {server_address}: {data.decode('utf-8')}")

finally:
    client_socket.close()
