"""
Credit: https://realpython.com/python-sockets/
Server for CS456 A1.
Function is to reverse received strings and return them to sender.
"""
import socket
import sys

# Creates socket of socket_type using a random unoccupied port
def create_socket(port_name, socket_type):
    
    new_socket = socket.socket(socket.AF_INET, socket_type)
    new_socket.bind(("", 0))
    print ("{0}={1}".format(port_name, new_socket.getsockname()[1]))
    return new_socket

# Negotiation using TCP sockets. Returns UDP socket for transaction if reqcode valid
def server_tcp_negotiation(n_socket, req_code):
    while True:
        print("WAITING FOR CLIENT REQ-CODE")
        n_socket.listen(1)
        connection_socket, client_address = n_socket.accept()
        client_req_code = int((connection_socket.recv(1024)).decode())
        print("CLIENT REQ-CODE: " + str(client_req_code))
        if client_req_code == req_code:
            print("VALID CLIENT REQ-CODE")
            t_socket = create_socket("SERVER_UDP_PORT", socket.SOCK_DGRAM)
            connection_socket.send(str(t_socket.getsockname()[1]).encode())
            return t_socket
        else:
            print("INVALID CLIENT REQ-CODE")
            connection_socket.send("-1".encode())

# Transaction using UDP sockets. Reverses message from client and sends it back.
# Closes r_socket
def server_udp_transaction(t_socket):
    print("WAITING FOR CLIENT MESSAGE")
    temp_msg, client_address = t_socket.recvfrom(1024)
    server_msg = temp_msg.decode()
    print("CLIENT MESSAGE='{0}'".format(server_msg))
    rev_msg = server_msg[::-1]
    print("SERVER MESSAGE='{0}'".format(rev_msg))
    t_socket.sendto(rev_msg.encode(), client_address)
    print("SERVER MESSAGE SENT, CLOSING TRANSACTION")
    t_socket.close()

# Driver code
def main():
    try:
        req_code = int(sys.argv[1])
    except IndexError:
        print("MISSING REQ-CODE")
        sys.exit(1)
    except ValueError:
        print("REQ-CODE MUST BE INTEGER")
        sys.exit(2)
    n_socket = create_socket("SERVER_PORT", socket.SOCK_STREAM)
    while True:
        t_socket = server_tcp_negotiation(n_socket, req_code)
        server_udp_transaction(t_socket)


if __name__ == "__main__":
    main()