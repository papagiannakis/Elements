import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()
layers = {'Input': ['in_1', 'in_2'], 'Linear1': ['l1_1', 'l1_2', 'l1_3'], 'ReLU1': ['r1', 'r2', 'r3'], 'Linear2': ['out']}
pos = {}
for i, (layer, nodes) in enumerate(layers.items()):
    for j, node in enumerate(nodes):
        pos[node] = (i * 2, len(nodes) / 2.0 - j)
        G.add_node(node)

for u in layers['Input']:
    for v in layers['Linear1']: G.add_edge(u, v)
for u, v in zip(layers['Linear1'], layers['ReLU1']):
    G.add_edge(u, v)
for u in layers['ReLU1']:
    for v in layers['Linear2']: G.add_edge(u, v)

plt.figure(figsize=(10, 4))
nx.draw(G, pos, with_labels=True, node_color='plum', node_size=1200, arrowsize=15)
plt.title("PyTorch Sequential Network Graph")
plt.savefig('test_w2_01_network_arch.png', dpi=100, bbox_inches='tight')
