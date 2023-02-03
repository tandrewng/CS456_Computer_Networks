"""
Credit: https://realpython.com/python-sockets/
Client for CS456 A1.
Function is to send message to server and return response from server
"""
import socket
import sys

# Establishes connection to server using TCP socket.
# Return transaction port number
def client_tcp_negotiation(server_address, n_port, req_code):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("SENDING REQ-CODE: " + str(req_code))
        client_socket.connect((server_address, n_port))
        client_socket.send(str(req_code).encode())
        t_port = int((client_socket.recv(1024)).decode())
        print("SERVER_UDP_PORT: " + str(t_port))
        if t_port == -1:
            print("INVALID REQ-CODE")
            sys.exit(4)
        return t_port
    except socket.error as e:
        print("CONNECTION ERROR: " + str(e))
        sys.exit(3)

# Transaction using UDP sockets.
# Sends msg to server and returns reversed message from server.
def client_udp_transaction(server_address, r_port, msg):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("SENDING MESSAGE: '{0}'" .format(msg))
    client_socket.sendto(msg.encode(), (server_address, r_port))
    client_rcv_msg = (client_socket.recv(1024)).decode()
    return client_rcv_msg

# Driver code
def main():
    try:
        server_address = str(sys.argv[1])
        n_port = int(sys.argv[2])
        req_code = int(sys.argv[3])
        msg = str(sys.argv[4])
    except IndexError:
        print("MISSING PARAMETER(S)")
        sys.exit(1)
    except ValueError:
        print("INVALID PARAM TYPE")
        sys.exit(2)
    r_port = client_tcp_negotiation(server_address, n_port, req_code)
    server_msg = client_udp_transaction(server_address, r_port, msg)
    print("SERVER MESSAGE: '{0}'".format(server_msg))


if __name__ == "__main__":
    main()