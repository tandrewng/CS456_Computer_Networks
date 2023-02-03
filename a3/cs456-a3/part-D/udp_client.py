#!/usr/bin/env python3

import socket as sock
import argparse

class UdpClient:

    def __init__(self, dest_port, dest_addr, src_port):
        self.dest_port = dest_port
        self.dest_addr = dest_addr
        self.addr_tuple = (dest_addr, dest_port)
        self.src_port = src_port
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", self.src_port))
    
    def send(self, message):
        print(f"Sending message \"{message}\" to {self.addr_tuple}")
        self.socket.sendto(bytes(message, "utf-8"), self.addr_tuple) 

def main():
    parser = argparse.ArgumentParser(
            description="Send UDP packets containing a UTF-8 enconded message")
    parser.add_argument("src_port", metavar="src_port", type=int,
            help="The source port to bind to")
    parser.add_argument("dst_port", metavar="dst_port", type=int,
            help="The destination port to send to")
    parser.add_argument("dst_ip", metavar="dst_ip", type=str,
            help="The destination IP to send to")
    parser.add_argument("message", metavar="message", type=str,
            help="The message to send.")
    args = parser.parse_args()

    udpc = UdpClient(args.dst_port, args.dst_ip, args.src_port)
    udpc.send(args.message)

if __name__ == "__main__":
    main()
