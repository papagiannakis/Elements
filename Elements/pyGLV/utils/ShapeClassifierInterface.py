import numpy as np
import torch
from matplotlib import pyplot as plt
from torch.nn import Sequential, Linear, ReLU
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing, global_max_pool


class PointNetLayer(MessagePassing):
    def __init__(self, in_channels, out_channels):
        # Message passing with "max" aggregation.
        super().__init__(aggr='max')

        # Initialization of the MLP:
        # Here, the number of input features correspond to the hidden node
        # dimensionality plus point dimensionality (=3).
        self.mlp = Sequential(Linear(in_channels + 3, out_channels),
                              ReLU(),
                              Linear(out_channels, out_channels))

    def forward(self, h, pos, edge_index):
        # Start propagating messages.
        return self.propagate(edge_index, h=h, pos=pos)

    def message(self, h_j, pos_j, pos_i):
        # h_j defines the features of neighboring nodes as shape [num_edges, in_channels]
        # pos_j defines the position of neighboring nodes as shape [num_edges, 3]
        # pos_i defines the position of central nodes as shape [num_edges, 3]
        # print(1)
        # print(h_j)

        input = pos_j - pos_i  # Compute spatial relation.

        if h_j is not None:
            # In the first layer, we may not have any hidden node features,
            # so we only combine them in case they are present.
            input = torch.cat([h_j, input], dim=-1)

        return self.mlp(input)  # Apply our final MLP.


class PointNet(torch.nn.Module):
    def __init__(self):
        super().__init__()

        torch.manual_seed(12345)
        self.conv1 = PointNetLayer(3, 32)
        self.conv2 = PointNetLayer(32, 32)
        self.conv3 = PointNetLayer(32, 64)
        self.classifier = Linear(64, 41)

    def forward(self, pos, batch, face):
        # Compute the kNN graph:
        # Here, we need to pass the batch vector to the function call in order
        # to prevent creating edges between points of different examples.
        # We also add `loop=True` which will add self-loops to the graph in
        # order to preserve central point information.
        # print(2)
        # edge_index = knn_graph(pos, k=3, batch=batch, loop=True)
        edges1 = []
        edges2 = []
        pos2 = torch.zeros([pos.shape[0], pos.shape[1]])
        for i in range(face.shape[1]):
            edges1.append(face[0][i])
            edges2.append(face[1][i])
            edges1.append(face[0][i])
            edges2.append(face[2][i])
            edges1.append(face[1][i])
            edges2.append(face[2][i])

            edges1.append(face[1][i])
            edges2.append(face[0][i])
            edges1.append(face[2][i])
            edges2.append(face[0][i])
            edges1.append(face[2][i])
            edges2.append(face[1][i])
        edge_index = torch.tensor(np.array([edges1, edges2], int), dtype=torch.int64)
        for i in range(pos.shape[0]):
            # print("1:", pos[i])
            pos[i] = torch.nn.functional.normalize(pos[i], p=1.0, dim=0)
            # print("2:", pos[i])
        # 3. Start bipartite message passing.
        h = self.conv1(h=pos, pos=pos, edge_index=edge_index)
        h = h.relu()
        h = self.conv2(h=h, pos=pos, edge_index=edge_index)
        h = h.relu()
        h = self.conv3(h=h, pos=pos, edge_index=edge_index)
        h = h.relu()

        # 4. Global Pooling.
        h = global_max_pool(h, batch)  # [num_examples, hidden_channels]

        # 5. Classifier.
        return self.classifier(h)


def train(model, optimizer, loader, criterion):
    model.train()

    total_loss = 0
    for data in loader:
        optimizer.zero_grad()  # Clear gradients.
        logits = model(data.pos, data.batch, data.face)  # Forward pass.
        loss = criterion(logits, data.y)  # Loss computation.
        loss.backward()  # Backward pass.
        optimizer.step()  # Update model parameters.
        total_loss += loss.item() * data.num_graphs

    return total_loss / len(loader.dataset)


@torch.no_grad()
def test(model, loader):
    model.eval()

    total_correct = 0
    for data in loader:
        logits = model(data.pos, data.batch, data.face)
        pred = logits.argmax(dim=-1)
        total_correct += int((pred == data.y).sum())

    return total_correct / len(loader.dataset)


def visualize_mesh(pos, face):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    ax.axes.zaxis.set_ticklabels([])
    ax.plot_trisurf(pos[:, 0], pos[:, 1], pos[:, 2], triangles=face.t(), antialiased=False)
    plt.show()


def pyECSToGnnFormat(vertices, indices):
    v = vertices[:, 0:3]

    ind = []
    edges1 = []
    edges2 = []
    # print("indices123:", indices[0])
    for i in range(3):
        ind.append([])
    for i in range(0, len(indices), 3):
        # print("myi:", i)
        edges1.append(indices[i])
        edges2.append(indices[i + 1])
        edges1.append(indices[i])
        edges2.append(indices[i + 2])
        edges1.append(indices[i + 1])
        edges2.append(indices[i + 2])

        edges1.append(indices[i + 1])
        edges2.append(indices[i])
        edges1.append(indices[i + 2])
        edges2.append(indices[i])
        edges1.append(indices[i + 2])
        edges2.append(indices[i + 1])
        ind[0].append(indices[i])
        ind[1].append(indices[i + 1])
        ind[2].append(indices[i + 2])

    ind = np.array(ind, dtype=int)

    testdata = Data()
    testdata['pos'] = torch.tensor(v)
    testdata['face'] = torch.tensor(ind)
    return testdata


def visualize_points(pos, edge_index=None, index=None):
    fig = plt.figure(figsize=(4, 4))
    if edge_index is not None:
        for (src, dst) in edge_index.t().tolist():
            src = pos[src].tolist()
            dst = pos[dst].tolist()
            plt.plot([src[0], dst[0]], [src[1], dst[1]], linewidth=1, color='black')
    if index is None:
        plt.scatter(pos[:, 0], pos[:, 1], s=50, zorder=1000)
    else:
        mask = torch.zeros(pos.size(0), dtype=torch.bool)
        mask[index] = True
        plt.scatter(pos[~mask, 0], pos[~mask, 1], s=50, color='lightgray', zorder=1000)
        plt.scatter(pos[mask, 0], pos[mask, 1], s=50, zorder=1000)
    plt.axis('off')
    plt.show()
