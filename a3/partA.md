# Part A
The first add-flow command

`$ofctl add-flow s0 in_port=1,ip,nw_src=10.0.0.2,nw_dst=10.0.1.2,actions=mod_dl_src:0A:00:0A:01:00:02,mod_dl_dst:0A:00:0A:FE:00:02,output=2`

- `ovs-ofctl -O OpenFlow13`: configure flow entries on virtual switches using OpenFlow version 1.3.
- `add-flow`: adds a flow entry to a specified switch's table.
- `s0`: specifies the switch we are adding the flow entry to; in this case it is switch 0.
- `in_port=1`: the ingress port where packets come to switch 0; in this case, switch 0 listens to ingress port 1.
- `ip`: matches IP fields of the packet.
- `nw_src=10.0.0.2`: the source IPV4 address of the packet; in this case 10.0.0.2.
- `nw_dst=10.0.1.2`: the destination IPV4 address of the packet; in this case 10.0.1.2.
- `actions`: actions to be taken when a packet matches the flow entry.
- `mod_dl_src`: modifies the source MAC address; in this case it is set to `0A:00:0A:01:00:02`.
- `mod_dl_dst`: modifies the destination MAC adress; in this case it is set to `0A:00:0A:FE:00:02`.
- `output=<port>`:outputting packets to the output port into the network; in this case the packets are forwarded to output port 2.