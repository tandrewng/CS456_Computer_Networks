from packet import Packet
import argparse
import socket

# sender host1 9991 9992 50 <input file>
# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("<hostname for the network emulator>")
parser.add_argument("<UDP port number used by the link emulator to receive ACKs from the receiver>")
parser.add_argument("<UDP port number used by the receiver to receive data from the emulator>")
parser.add_argument("<name of the file into which the received data is written>")
args = parser.parse_args()
# set up sockets to be listening on
args = args.__dict__ # A LAZY FIX
host_addr = str(args["<hostname for the network emulator>"])
ack_port = int(args["<UDP port number used by the link emulator to receive ACKs from the receiver>"])
data_port = int(args["<UDP port number used by the receiver to receive data from the emulator>"])
file_name = str(args["<name of the file into which the received data is written>"])

# logs
arrival_log = open("arrival.log", "a")

# variables
file = open(file_name, "a")
expected = 0
confirmed = 0
buffer = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', data_port))

while True:
    pack = sock.recv(1024)
    pack_type, pack_seqnum, pack_length, pack_data = Packet(pack).decode()
    decoded_pack = Packet(pack_type, pack_seqnum, pack_length, pack_data)

    arrival_log.write(str(decoded_pack.seqnum) + "\n")

    if (decoded_pack.seqnum == expected):
        if (decoded_pack.typ == 2):
            # received eot, send back eot and exit
            eot = Packet(2, decoded_pack.seqnum, 0, "").encode()
            sock.sendto(eot, (host_addr, ack_port))
            arrival_log.close()
            exit()
        else:
            # received an expected seqnum, write packet data, update expected to next
            file.write(decoded_pack.data)
            confirmed = decoded_pack.seqnum
            expected = (confirmed + 1) % 32
            # go through buffer to see if we have received packets from before and write
            while expected in buffer:
                expected_pack = buffer[expected]
                if (expected_pack.typ == 2):
                    # EOT in buffer, write and exit
                    eot = Packet(2, decoded_pack.seqnum, 0, "").encode()
                    sock.sendto(eot, (host_addr, ack_port))
                    arrival_log.close()
                    exit()
                file.write(str(expected_pack.data))
                del buffer[expected]
                confirmed = expected
                expected = (confirmed + 1) % 32
    # not expected received, add onto buffer if within 10 packets after
    elif (((decoded_pack.seqnum > expected and decoded_pack.seqnum <= expected + 10) or \
        (decoded_pack.seqnum <= (expected + 10) % 32 < 10))\
        and decoded_pack.seqnum not in buffer):
        buffer[decoded_pack.seqnum] = decoded_pack
    # received data, send back ack for most recent confirmed
    ack = Packet(0, confirmed, 0, "").encode()
    sock.sendto(ack, (host_addr, ack_port))
