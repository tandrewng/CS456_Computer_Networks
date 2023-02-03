
from pox.core import core
import pox.openflow.libopenflow_01 as of
import networkx as nx

from networkx.algorithms.shortest_paths.generic import shortest_path
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

log = core.getLogger()

def get_networkx_topology_graph():
    """
    get_networkx_topology_graph: nx.Graph

    Returns a NetworkX graph of the current topology formed by the switches
    connected to the controller.
    """
    g = nx.Graph()
    nodes = {l_i.dpid1 for l_i in core.openflow_discovery.adjacency.keys()}
    g.add_nodes_from(nodes)
    for link in core.openflow_discovery.adjacency.keys():
        g.add_edge(link.dpid1, link.dpid2)
    return g 

def get_shortest_path_between(nx_graph, source_dpid, target_dpid):
    """
    get_shortest_path_between: nx.Graph -> int -> int -> List[int]

    Gets the shortest path between <source_node> and <target_node> in
    <nx_graph>. Returns the path as a list of switch DPIDs

    Parameters:
        - nx_graph: A NetworkX graph obtained by calling
          get_networkx_topology_graph.
        - source_dpid: The first DPID in the path.
        - target_dpid: The last DPID in the path.
    """
    return shortest_path(nx_graph, source_dpid, target_dpid)

def get_ports_connecting(source_dpid, target_dpid):
    """
    get_ports_connecting: int -> int -> int

    Returns a tuple containing two port numbers. The first is the port on
    <source_dpid> that connects <source_dpid> to <target_dpid>, the second is
    the port on <target_dpid> that connects <target_dpid> to <source_dpid>. In
    the case that <source_dpid> and <target_dpid> are not _directly_ connected,
    the function returns None.

    Parameters:
        - source_dpid: The DPID of the source node.
        - target_dpid: The DPID of the target node
    """
    links = list(core.openflow_discovery.adjacency.keys())
    print(links)
    the_link = [l_i for l_i in links 
            if l_i.dpid1 == source_dpid
            and l_i.dpid2 == target_dpid]
    if len(the_link) == 0:
        return None
    
    return the_link[0].port1, the_link[0].port2

def get_input_port(path, dpid):
    """
    get_input_port: List[int] -> int -> int

    Given a path, this function returns the port on <dpid> that connects <dpid>
    to the previous hop in the path. Suppose you have the following network
    topology (numbers are port numbers on the switches):

                            2     2  3     2
                          s1 ----- s2 ----- s3
                          |1       |1       | 1
                          |        |        |
                          h1       h2       h3

    And the path is s1 -> s2 -> s3, then calling get_input_port(path, s2) will
    return 2 since the previous hop in the path from s2 is s1 and the port on
    s2 that connects to s1 is 2. Note that if you call get_input_port(path, s1)
    the function will return 1 since it implicitly assumes that the first hop
    in the path is actually the host connected to s1 and the hosts are always
    connected to port 1 of the switch.

    Parameters:
        - path: A list of switch DPIDs representing the path from the source
          dpid to the destination dpid.
        - dpid: A single DPID that is part of the path.
    """
    hop_number = path.index(dpid)
    if hop_number == 0:
        return 1 # The default host port

    local_port, remote_port = \
            get_ports_connecting(path[hop_number - 1], path[hop_number])
    return remote_port

def build_match_for( source_mac
                   , destination_mac
                   , source_ip
                   , destination_ip
                   , source_port
                   , destination_port
                   , in_port):
    """
    build_match_for: str -> str -> str -> str -> int -> int -> int -> ofp_match

    Builds an OpenFlow match structure that matches on the specified inputs,
    when you are implementing install_udp_middlebox_flow you should always use
    this function to build the matches as you are expected to filter on all of
    the criteria specified in this function. The function always creates
    matches that look for UDP packets encapsulated in an IP datagram
    encapslated in an Ethernet frame.

    Parameters:
        - source_mac: A string representing the source MAC address to filter
          on.
        - destination_mac: A string representing the destination MAC address to
          filter on.
        - source_ip: A string representing the source IP address to filter on.
        - destination_ip: A string representing the destination IP address to
          filter on.
        - source_port: An integer representing the source UDP port to filter
          on.
        - destination_port: An integer representing the destination UDP port to
          filter on. 
        - in_port: An integer representing the input switch port to filter on.
    """
    the_match = of.ofp_match()
    the_match.in_port = in_port
    the_match.dl_src = EthAddr(source_mac)
    the_match.dl_dst = EthAddr(destination_mac)
    the_match.dl_type = 0x0800
    the_match.nw_src = IPAddr(source_ip)
    the_match.nw_dst = IPAddr(destination_ip)
    the_match.nw_proto = 17
    the_match.tp_src = source_port
    the_match.tp_dst = destination_port
    return the_match

def build_openflow_flowmod(match, output_port):
    """
    build_openflow_flowmod: ofp_match -> int -> ofp_flowmod
    
    Creates a flowmod that will match on packets specified by <match> and
    output them on <output_port>. Much like build_match_for, you should always
    use this function when creating your Flowmods.

    Paramaters:
        - match: The match specifying the traffic that will match this flow
          rule. Remember that you should always create the match objects using
          the build_match_for function.
        - output_port: The port that matching traffic will be forwarded out of.
    """
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.actions.append(of.ofp_action_output(port=output_port))
    msg.priority = 65534
    return msg

def install_flowmod_on_switch_with_dpid(flowmod, dpid):
    """
    install_flowmod_on_switch_with_dpid: ofp_flowmod -> dpid -> None

    Installs the flowmod on the specified switch. Again, you should be able to
    complete the assignment using only this method to install your flowmods.

    Parameters:
        - flowmod: The flowmod (created with build_openflow_flowmod) to install
          on the switch.
        - dpid: The DPID of the switch to install the flowmod on.
    """
    core.l2_learning.switch_connections[dpid].send(flowmod)

def get_host_entry(dpid):
    """
    get_host_entry: int -> host_tracker.MacEntry

    Gets the host entry for the host connected to the switch with DPID <dpid>.
    To initialize the host entries you need to run pingall from the Mininet
    console! 

    Since we assume that there is only one host connected to each switch this
    method returns the first host entry it finds.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = [e for e in core.host_tracker.entryByMAC.values()
            if e.dpid == dpid]
    if len(host_entry) == 0:
        raise ValueError("Couldn't find host entry! Did you remember to pingall"
                         " before you started?")
    host_entry = host_entry[0]
    return host_entry

def get_host_ip_from_dpid(dpid):
    """
    get_host_ip_from_dpid: int -> str

    Returns the IP address of the host connected to the switch with DPID <dpid>

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return next(iter(host_entry.ipAddrs.keys()))


def get_host_mac_from_dpid(dpid):
    """
    get_host_mac_from_dpid: int -> str

    Returns the MAC address of the host connected to the switch with DPID
    <dpid>.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return host_entry.macaddr

def get_host_port(dpid):
    """
    get_host_port: int -> int

    Returns the port on the switch with DPID <dpid> that connects to the host.
    Remember we always assume that there is exactly one host connected to every
    switch.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return host_entry.port

def install_udp_middlebox_flow( source_dpid
                              , destination_dpid
                              , middlebox_dpid
                              , source_port
                              , destination_port):
    # This is the function you will complete for part D of assignment 3.
    #
    # If you're confused or don't know how to get started think about a simple
    # linear topology that you can create with mininet using the following
    # command:
    #   sudo mn --topo=linear,3 --controller=remote,ip=127.0.0.1,port=6633 --mac
    # The topology will look like this:
    #
    #             2         2  3         2
    #           s1 --------- s2 --------- s3
    #          1|           1|           1|
    #           |            |            |
    #           h1           h2           h3
    # 
    # Where the numbers on the figures are the openflow port numbers. The
    # switches will have the following DPIDs:
    #   - s1: 1
    #   - s2: 2
    #   - s3: 3
    # h1 will be our client, h2 will be the middlebox and h3 will be the
    # server. Anytime you need to know the MAC or IP addresses of a host
    # connected to a particular switch, you can get it using the
    # get_host_mac_from_dpid and get_host_ip_from_dpid functions.
    #
    # Now that you have a simple test case you should think about what flow
    # rules you need to steer the traffic along the path from h1 -> s1 -> s2 ->
    # h2. Similar, but not identical, flow rules will be needed to steer the
    # traffic from h2 -> s2 -> s3 -> h3 after it has been modified by the
    # middlebox.
    #
    # Remember to use the helper functions that are provided in this file to do
    # things like:
    #   * Get paths from h1 to h2 and from h2 to h3
    #   * Build a flow rule that matches on the right type of traffic
    #   * Install your flow rules.
    #   * Get information about links and port numbers.
    # 
    # But remember that your code had to work for _any loopfree_ topology so
    # don't make it specific to this example!
    # print("Hello CS456 Student! You need to add code to this function "
    #       "to complete part D of assignment 3!")

    # Get shortest path between source and middlebox, and middlebox and destination
    topology_graph = get_networkx_topology_graph()
    switch_dpid_list_source_middlebox = get_shortest_path_between(topology_graph, source_dpid, middlebox_dpid)
    switch_dpid_list_middlebox_destination = get_shortest_path_between(topology_graph, middlebox_dpid, destination_dpid)

    # Get MAC and IP addresses of source and destination host connected to switch
    source_mac = get_host_mac_from_dpid(source_dpid)
    source_ip = get_host_ip_from_dpid(source_dpid)
    destination_mac = get_host_mac_from_dpid(destination_dpid)
    destination_ip = get_host_ip_from_dpid(destination_dpid)

    # Loop through switches between client and middlebox
    for index in range(len(switch_dpid_list_source_middlebox)):
        match = build_match_for(source_mac, destination_mac, source_ip, destination_ip, source_port, destination_port, get_input_port(switch_dpid_list_source_middlebox, switch_dpid_list_source_middlebox[index]))

        if (index == len(switch_dpid_list_source_middlebox) - 1):
            # Build flowmod that matches on packets and outputs them on port of switch that is connected to middlebox
            flowmod = build_openflow_flowmod(match, get_host_port(switch_dpid_list_source_middlebox[index]))
        else:
            # Build flowmod that matches on packets and outputs them on output port
            flowmod = build_openflow_flowmod(match, get_ports_connecting(switch_dpid_list_source_middlebox[index], switch_dpid_list_source_middlebox[index + 1])[0])

        install_flowmod_on_switch_with_dpid(flowmod, switch_dpid_list_source_middlebox[index]) 

    # Loop through switches between middlebox and destination
    for index in range(len(switch_dpid_list_middlebox_destination)):
        match = build_match_for(source_mac, destination_mac, source_ip, destination_ip, source_port, destination_port, get_input_port(switch_dpid_list_middlebox_destination, switch_dpid_list_middlebox_destination[index]))

        if (index == len(switch_dpid_list_middlebox_destination) - 1):
            # Build flowmod that matches on packets and outputs them on port of switch that is connected to destination 
            flowmod = build_openflow_flowmod(match, get_host_port(switch_dpid_list_middlebox_destination[index]))
        else:
            # Build flowmod that matches on packets and outputs them on output port
            flowmod = build_openflow_flowmod(match, get_ports_connecting(switch_dpid_list_middlebox_destination[index], switch_dpid_list_middlebox_destination[index + 1])[0])

        install_flowmod_on_switch_with_dpid( flowmod, switch_dpid_list_middlebox_destination[index])

def do_install():
    """
    do_install: None

    This method is just to save you typing at the Pox command line. Rather than
    having to type install_udp_middlebox_flow and providing the arguments every
    time you run your program, you can specify default arguments that you use
    for testing and then just type "do_install()" on the Pox command line to
    run your program.
    """

    source_dpid = 1
    destination_dpid = 3
    middlebox_dpid = 2
    source_port = 9234
    destination_port = 9235
    install_udp_middlebox_flow(source_dpid, destination_dpid, middlebox_dpid,
            source_port, destination_port)
