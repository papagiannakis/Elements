import random

import numpy as np
import torch
from torch_geometric.data import Data

import Elements.pyECSS.utilities as util
from torch_geometric.nn import GAE, VGAE, GCNConv

from GAUtils import matrix_to_motor, matrix_to_angle_axis_translation
from Elements.pyECSS.GA.quaternion import Quaternion


class GCNEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(-1, 2 * out_channels)
        self.conv2 = GCNConv(2 * out_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)


class VariationalGCNEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(-1, 2 * out_channels)
        self.conv_mu = GCNConv(2 * out_channels, out_channels)
        self.conv_logstd = GCNConv(2 * out_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv_mu(x, edge_index), self.conv_logstd(x, edge_index)


class LinearEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = GCNConv(-1, out_channels)

    def forward(self, x, edge_index):
        return self.conv(x, edge_index)


class VariationalLinearEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv_mu = GCNConv(-1, out_channels)
        self.conv_logstd = GCNConv(in_channels, out_channels)

    def forward(self, x, edge_index):
        return self.conv_mu(x, edge_index), self.conv_logstd(x, edge_index)


runLosses = np.zeros((5, 10, 50))
for type in range(5):
    r1 = -5
    r2 = 5
    feats = []
    edges0 = []
    edges1 = []
    for i in range(0, 10000, 2):
        angle = (random.randint(0, 180))
        trans = (r1 - r2) * torch.rand(3) + r2
        trs1 = util.translate(trans[0].item(), trans[1].item(), trans[2].item()) @ util.rotate((0, 1, 0), angle)
        trs2 = util.translate(trans[0].item(), trans[1].item() + 0.5, trans[2].item()) @ util.rotate((0, 1, 0), angle)
        edges0.append(i)
        edges1.append(i + 1)
        if type == 0:
            feats.append(trs1.flatten())
            feats.append(trs2.flatten())
        elif type == 1:
            feats.append(matrix_to_motor(trs1, method='CGA').value)
            feats.append(matrix_to_motor(trs2, method='CGA').value)
        elif type == 2:
            feats.append(matrix_to_motor(trs1, method='PGA').value)
            feats.append(matrix_to_motor(trs2, method='PGA').value)
        elif type == 3:
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                trs1)  # notice theta is in rad
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = extracted_theta
            tempfeats[4] = extracted_axis[0]
            tempfeats[5] = extracted_axis[1]
            tempfeats[6] = extracted_axis[2]
            feats.append(tempfeats)
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                trs2)  # notice theta is in rad
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = extracted_theta
            tempfeats[4] = extracted_axis[0]
            tempfeats[5] = extracted_axis[1]
            tempfeats[6] = extracted_axis[2]
            feats.append(tempfeats)
        else:
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                trs1)  # notice theta is in rad
            q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = q.q[0]
            tempfeats[4] = q.q[1]
            tempfeats[5] = q.q[2]
            tempfeats[6] = q.q[3]
            feats.append(tempfeats)
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                trs2)  # notice theta is in rad
            q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = q.q[0]
            tempfeats[4] = q.q[1]
            tempfeats[5] = q.q[2]
            tempfeats[6] = q.q[3]
            feats.append(tempfeats)

    data = Data()
    data.x = torch.FloatTensor(np.asarray(feats))
    edgesent = torch.LongTensor([edges0, edges1])
    data.edge_index = edgesent


    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    in_channels, out_channels = 16, 16
    data = data.to(device)
    for run in range(10):
        model = GAE(GCNEncoder(in_channels, out_channels))

        model = model.to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)


        def train():
            model.train()
            optimizer.zero_grad()
            z = model.encode(data.x, data.edge_index)
            loss = model.recon_loss(z, data.edge_index)
            loss.backward()
            optimizer.step()
            return float(loss)


        for epoch in range(50):
            loss = train()
            runLosses[type][run][epoch] = loss
            print(f'Epoch: {epoch:03d}, Loss: {loss:.4f}')
