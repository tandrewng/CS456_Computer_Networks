from mininet.topo import Topo
from mininet.net import Mininet, CLI
from mininet.log import lg, LEVELS


class SimpleTreeTopo(Topo):

    def build(self, depth):
        self.switch_num = 1
        self.add_tree(depth)

    def add_tree(self, depth):
        if depth == 0:
            return None

        s = self.addSwitch("s%d" % self.switch_num)
        h = self.addHost("h%d" % self.switch_num)
        self.addLink(s, h)
        self.switch_num += 1
        left_tree = self.add_tree(depth - 1)
        right_tree = self.add_tree(depth - 1)

        if left_tree != None and right_tree != None:
            self.addLink(s, left_tree)
            self.addLink(s, right_tree)
        
        return s


def main():
    lg.setLogLevel("info")
    topo = SimpleTreeTopo(3)
    net = Mininet(topo)
    CLI(net)
    net.stop()

if __name__ == "__main__":
    pass
    # main()

topos = {"SimpleTreeTopo": lambda x: SimpleTreeTopo(x)}
