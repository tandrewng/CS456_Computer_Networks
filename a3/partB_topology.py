#!/usr/bin/python

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel

class CSLRTopo( Topo ):

        def __init__( self ):
                "Create Topology"

                # Initialize topology
                Topo.__init__( self )

                # Add hosts
                alice = self.addHost( 'alice' )
                bob = self.addHost( 'bob' )
                carol = self.addHost( 'carol' )

                # Add switches
                s0 = self.addSwitch( 's0', listenPort=6634 )
                s1 = self.addSwitch( 's1', listenPort=6635 )
                s2 = self.addSwitch( 's2', listenPort=6636 )

                r1 = self.addSwitch( 'r1', listenPort=6637 )
                r2 = self.addSwitch( 'r2', listenPort=6638 )

                # Add links between hosts and switches
                self.addLink( alice, s0 ) # alice-eth0 <-> s0-eth1
                self.addLink( bob, s1 ) # bob-eth0 <-> s1-eth1
                self.addLink( carol, s2 ) # carol-eth0 <-> s2-eth1

                # Add links between switches
                self.addLink( s0, r1) # s0-eth2 <-> r1-eth1
                self.addLink( r1, s1) # r1-eth2 <-> s1-eth2
                self.addLink( s1, r2) # s1-eth3 <-> r2-eth1
                self.addLink( r2, s2) # r2-eth2 <-> s2-eth2


def run():
        "Create and configure network"
        topo = CSLRTopo()
        net = Mininet( autoStaticArp=True, topo=topo, link=TCLink, controller=None )

        # Set interface IP and MAC addresses for hosts
        alice = net.get( 'alice' )
        alice.intf( 'alice-eth0' ).setIP( '10.1.1.17', 24 )
        alice.intf( 'alice-eth0' ).setMAC( '0A:00:00:02:00:00' )

        bob = net.get( 'bob' )
        bob.intf( 'bob-eth0' ).setIP( '10.4.4.48', 24 )
        bob.intf( 'bob-eth0' ).setMAC( '0A:00:01:02:00:00' )

        carol = net.get( 'carol' )
        carol.intf( 'carol-eth0' ).setIP( '10.6.6.69', 24 )
        carol.intf( 'carol-eth0' ).setMAC( '0A:00:02:02:00:00' )        

        # Set interface MAC address for switches (NOTE: IP
        # addresses are not assigned to switch interfaces)
        s0 = net.get( 's0' )
        s0.intf( 's0-eth1' ).setMAC( '0A:00:00:01:00:01' )
        s0.intf( 's0-eth2' ).setMAC( '0A:00:0A:FE:00:02' )

        s1 = net.get( 's1' )
        s1.intf( 's1-eth1' ).setMAC( '0A:00:01:01:00:01' )
        s1.intf( 's1-eth2' ).setMAC( '0A:00:0B:FE:00:02' )
        s1.intf( 's1-eth3' ).setMAC( '0A:00:0C:01:00:03' )

        s2 = net.get( 's2' )
        s2.intf( 's2-eth1' ).setMAC( '0A:00:02:01:00:01' )
        s2.intf( 's2-eth2' ).setMAC( '0A:00:0C:FE:00:02' )

        r1 = net.get( 'r1' )
        r1.intf( 'r1-eth1' ).setMAC( '0A:00:03:01:00:01' )
        r1.intf( 'r1-eth2' ).setMAC( '0A:00:0D:FE:00:02' )

        r2 = net.get( 'r2' )
        r2.intf( 'r2-eth1' ).setMAC( '0A:00:04:01:00:01' )
        r2.intf( 'r2-eth2' ).setMAC( '0A:00:0E:FE:00:02' )

        net.start()

        # Add routing table entries for hosts (NOTE: The gateway
		# IPs 10.0.X.1 are not assigned to switch interfaces)
        alice.cmd( 'route add default gw 10.1.1.1 dev alice-eth0' )
        bob.cmd( 'route add default gw 10.4.4.1 dev bob-eth0' )
        carol.cmd( 'route add default gw 10.6.6.1 dev carol-eth0' )

        # Add arp cache entries for hosts
        alice.cmd( 'arp -s 10.1.1.1 0A:00:00:01:00:01 -i alice-eth0' )
        bob.cmd( 'arp -s 10.4.4.1 0A:00:01:01:00:01 -i bob-eth0' )
        carol.cmd( 'arp -s 10.6.6.1 0A:00:02:01:00:01 -i carol-eth0' )

        # Open Mininet Command Line Interface
        CLI(net)

        # Teardown and cleanup
        net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
