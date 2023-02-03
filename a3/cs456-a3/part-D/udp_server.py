#!/usr/bin/env python3 

import socket as sock
import logging as log
import argparse

class UdpListener():
    MAX_RECV_SIZE = 1024
    def __init__(self, handler, port = 3333):
        self.handler = handler
        self.port = port
        self.listener = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.listener.bind(("0.0.0.0", port))

    def listen_forever(self):
        print(f"Listening for UDP messages on port {self.port}")
        while True:
            try:
                message, recv_from = self.listener.recvfrom(self.MAX_RECV_SIZE)
            except KeyboardInterrupt as e:
                print("Shutting down!")
                return 

            self.handler(message, recv_from)

    def listen_once(self):
        return listener.recvfrom(MAX_RECV_SIZE)

def print_handler(message, source):
    message = message.decode("utf-8")
    print(f"Received message {message} from {source}")

def main():
    parser = argparse.ArgumentParser(
            description="Listens for UDP packets on the specified port and "
                        "prints the message in the packet payload.")
    parser.add_argument("listen_port", metavar="listen_port", type=int, 
            help="The port the server will listen on")
    args = parser.parse_args()
    the_server = UdpListener(print_handler, port=args.listen_port)
    the_server.listen_forever()

if __name__ == "__main__":
    main()
