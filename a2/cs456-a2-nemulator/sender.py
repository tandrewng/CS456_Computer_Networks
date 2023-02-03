from packet import Packet
import argparse
import socket
import threading
import time

# sample call: sender host1 9991 9992 50 <input file>
# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("<host address of the network emulator>")
parser.add_argument("<UDP port number used by the emulator to receive data from the sender>")
parser.add_argument("<UDP port number used by the sender to receive ACKs from the emulator>")
parser.add_argument("<timeout interval in units of millisecond>")
parser.add_argument("<name of the file to be transferred>")
args = parser.parse_args()
# set up sockets to be listening on
args = args.__dict__ # A LAZY FIX
host_addr = str(args["<host address of the network emulator>"])
data_port = int(args["<UDP port number used by the emulator to receive data from the sender>"])
ack_port = int(args["<UDP port number used by the sender to receive ACKs from the emulator>"])
timeout = int(args["<timeout interval in units of millisecond>"]) / 1000.0
file_name = str(args["<name of the file to be transferred>"])

# logs
seqnum_log = open("seqnum.log", "a")
ack_log = open("ack.log", "a")
N_log = open("N.log", "a")

# variables
seqnum = 0
curr_timestamp = 0
N = 1
N_log.write("t=" + str(curr_timestamp) + " "+ str(N) + "\n")
MAX_WINDOW_SIZE = 10
MAX_DATA_LEN = 500
packets = []
expecting = 0
actual_expecting = 0
lock = threading.Lock()
cv = threading.Condition(lock)

# read file data, populate packet array to be sent
file = open(file_name, "r")
while True:
    data = file.read(MAX_DATA_LEN)
    if not data: break
    packets.append(Packet(1, seqnum % 32, len(data), data))
    seqnum += 1
file.close()

# reset seqnum to indicate highest packet sent
seqnum = 0
unsent = len(packets)

# create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', ack_port))    

# time out function: resends expecting packet and reset timer
def is_timed_out():
    global curr_timestamp, host_addr, data_port, N, packets, cv, actual_expecting, timer

    with cv:
        if (actual_expecting >= len(packets)): return
        curr_timestamp += 1
        N = 1
        N_log.write("t=" + str(curr_timestamp) + " " + str(N) + "\n")
        sock.sendto(packets[actual_expecting].encode(), (host_addr, data_port))
        if packets[actual_expecting].typ == 2:
            seqnum_log.write("t=" + str(curr_timestamp) + " EOT\n")
        else:
            seqnum_log.write("t=" + str(curr_timestamp) + " " + str(packets[actual_expecting].seqnum) + "\n")
        # reset timer
        if timer.is_alive():
            timer.cancel()
        timer = threading.Timer(timeout, is_timed_out)
        timer.start()

timer = threading.Timer(timeout, is_timed_out)

# ack and eot receiver: receives timer and if significant will wake up sender and reset timer if applicable
def receive_ack():
    global expecting, N, MAX_WINDOW_SIZE, timeout, curr_timestamp, actual_expecting, timer

    while True:
        recv_pack  = sock.recv(1024)
        recv_type, recv_seqnum, recv_length, recv_data = Packet(recv_pack).decode()
        ack_pack = Packet(recv_type, recv_seqnum, recv_length, recv_data)
        with cv:
            if (ack_pack.typ == 0):
                curr_timestamp += 1
                ack_log.write("t=" + str(curr_timestamp) + " " + str(ack_pack.seqnum) + "\n")
                # if incoming is expected or greater
                if (expecting + 10 > ack_pack.seqnum >= expecting or \
                    (ack_pack.seqnum < (expecting + 10) % 32 < 10)):
                    N = min(N + 1, MAX_WINDOW_SIZE)
                    N_log.write("t=" + str(curr_timestamp) + " " + str(N) + "\n")

                    # updating expecting and actual expecting
                    if (ack_pack.seqnum >= expecting):
                        actual_expecting += 1 + ack_pack.seqnum - expecting
                    else:
                        actual_expecting += 1 + 32 - expecting + ack_pack.seqnum
                    expecting = (ack_pack.seqnum + 1) % 32

                    # cancels timer and if there are still outstanding we reset
                    if timer.is_alive():
                        timer.cancel()
                        if (actual_expecting < seqnum):
                            timer = threading.Timer(timeout, is_timed_out)
                            timer.start()

                    # wake up sender
                    cv.notify_all()
            elif (ack_pack.typ == 2):
                curr_timestamp += 1
                ack_log.write("t=" + str(curr_timestamp) +" EOT\n")
                if timer.is_alive():
                        timer.cancel()
                return
            else:
                return

acks_thread = threading.Thread(target=receive_ack, args=())
acks_thread.start()

# sending packets
while unsent:
    with cv:
        while (expecting <= seqnum % 32 < (expecting + N) or seqnum % 32 < (expecting + N) % 32) \
             and seqnum < len(packets):
            next_packet = packets[seqnum].encode()
            sock.sendto(next_packet, (host_addr, data_port))
            seqnum_log.write("t=" + str(curr_timestamp) + " " + str(seqnum%32) + "\n")
            seqnum += 1
            unsent -= 1
            curr_timestamp += 1
            # set timer
            if not timer.is_alive():
                timer = threading.Timer(timeout, is_timed_out)
                timer.start()
        # waiting on receiver
        cv.wait()
timer.cancel()

# EOT
eot_pack = Packet(2, seqnum % 32, 0, "")
packets.append(eot_pack)
sock.sendto(eot_pack.encode(), (host_addr, data_port))
curr_timestamp += 1
seqnum_log.write("t=" + str(curr_timestamp) + " EOT\n")
# in case eot is delayed, is unneccessary though, idk whether to include this
timer = threading.Timer(timeout, is_timed_out)
timer.start()

# threads need to join before exit
acks_thread.join()
sock.close()
seqnum_log.close()
ack_log.close()
N_log.close()
