import socket

HOST = '0.0.0.0'
PORT = 5000

BUFFER_SIZE = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print(f"server listening on {HOST}, {PORT}")

while True:
    data, client_address = server_socket.recvfrom(BUFFER_SIZE)

    message = data.decode('utf-8')

    print(f"received {message} from {client_address}")
    
    response = f"Echo: {message}"
    server_socket.sendto(response.encode('utf-8'), client_address)

