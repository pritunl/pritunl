run_nodes: python2 -u tools/vagrant_start_nodes.py node0 node1 node2 node3
node0: tail --retry -f var/node0.output
node1: tail --retry -f var/node1.output
node2: tail --retry -f var/node2.output
node3: tail --retry -f var/node3.output
