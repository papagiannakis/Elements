import os

print(os.getcwd())
import sys

sys.path.append("../../../")
import torch
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv
from torch_geometric.nn.norm import GraphNorm
from torch_geometric.utils import negative_sampling

from CreateScenes import objs, CreateSceneFromGNNOutput
from Elements.pyGLV.GL.Scene import Scene
import Converter
import random
import numpy as np
import UsdImporter as SceneLoader
from Elements.pyECSS.Entity import Entity


if not os.path.exists("Training_Scenes"):
    import requests
    import zipfile

    # Dropbox link to the zip file
    dropbox_link = "https://www.dropbox.com/s/nv9lm9jyjwx7tj6/Training_Scenes2.zip?dl=1"

    # Download the zip file
    response = requests.get(dropbox_link, stream=True)
    zip_filename = "file.zip"

    with open(zip_filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=128):
            file.write(chunk)

    # Extract the contents of the zip file
    with zipfile.ZipFile(zip_filename, "r") as zip_ref:
        zip_ref.extractall("Training_Scenes")

    # Clean up the downloaded zip file
    import os

    os.remove(zip_filename)
else:
    print("Skipping download, scenes already exist.")

numscenes = 1000
mydata = []
myy = []
tempobs = objs.copy()
tempobs.remove("root")
label_emb = 8
features = 7
latent_dim = 16


class VariationalGCNEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super(VariationalGCNEncoder, self).__init__()
        self.conv1 = GCNConv(in_channels, 2 * out_channels)  # cached only for transductive learning
        self.conv2 = GCNConv(2 * out_channels, 4 * out_channels)
        self.conv_mu = GCNConv(2 * out_channels, out_channels)
        self.conv_logstd = GCNConv(2 * out_channels, out_channels)
        self.norm = GraphNorm(in_channels)
        self.lRelu = torch.nn.LeakyReLU(0.1)

    def forward(self, x, edge_index, batch=None):
        if self.training:
            x = self.norm(x, batch)
        else:
            x = self.norm(x)
        x = self.lRelu(self.conv1(x, edge_index))
        # x = self.lRelu(self.conv2(x, edge_index))
        mu, logstd = self.conv_mu(x, edge_index), self.conv_logstd(x, edge_index)
        return self.reparametrize(mu, logstd), mu, logstd

    def reparametrize(self, mu, logstd):
        if self.training:
            return mu + torch.randn_like(logstd) * torch.exp(logstd)
        else:
            return mu


class VariationalGCNDecoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super(VariationalGCNDecoder, self).__init__()
        self.lin1 = torch.nn.Linear(in_channels, out_channels)
        self.lin3 = torch.nn.Linear(out_channels, out_channels)
        self.lin2 = torch.nn.Linear(in_channels, in_channels)
        self.lRelu = torch.nn.LeakyReLU(0.1)

    def forward(self, z):
        x = self.lRelu(self.lin1(z))
        x = self.lin3(x)
        # value = (z[edge_index[0]] * z[edge_index[1]]).sum(dim=1)
        return x, z

    def forward_for_loss(self, z, edge_index):
        zhat = self.lin2(z)
        value = (z[edge_index[0]] * zhat[edge_index[1]]).sum(dim=1)
        return torch.sigmoid(value)

    def forward_all(self, z):
        r"""Decodes the latent variables :obj:`z` into a probabilistic dense
        adjacency matrix.

        Args:
            z (torch.Tensor): The latent space :math:`\mathbf{Z}`.
            sigmoid (bool, optional): If set to :obj:`False`, does not apply
                the logistic sigmoid function to the output.
                (default: :obj:`True`)
        """
        zhat = self.lin2(z)
        adj = torch.matmul(z, zhat.t())
        return torch.sigmoid(adj)


class VariationalAE(torch.nn.Module):
    def __init__(self, encoder, decoder, label_emb):
        super(VariationalAE, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.__mu__, self.__logstd__ = None, None
        # self.__logstd__ = self.__logstd__.clamp(max=MAX_LOGSTD)
        self.labelEmb = torch.nn.Embedding(len(objs), label_emb)

    def forward(self, x, edge_index, y, batch=None):
        y = self.labelEmb(y)
        x = torch.cat((x, y), dim=1)
        MAX_LOGSTD = 10
        z, mu, logstd = self.encoder(x, edge_index, batch)
        self.__mu__ = mu
        self.__logstd__ = logstd
        self.__logstd__ = self.__logstd__.clamp(max=MAX_LOGSTD)
        z = torch.cat((z, y), dim=1)
        return self.decoder(z)

    def recon_loss(self, z, pos_edge_index,
                   neg_edge_index=None):
        r"""Given latent variables :obj:`z`, computes the binary cross
        entropy loss for positive edges :obj:`pos_edge_index` and negative
        sampled edges.

        Args:
            z (torch.Tensor): The latent space :math:`\mathbf{Z}`.
            pos_edge_index (torch.Tensor): The positive edges to train against.
            neg_edge_index (torch.Tensor, optional): The negative edges to
                train against. If not given, uses negative sampling to
                calculate negative edges. (default: :obj:`None`)
        """
        EPS = 1e-15
        out = self.decoder.forward_for_loss(z, pos_edge_index)
        pos_loss = -torch.log(out + EPS).mean()

        if neg_edge_index is None:
            neg_edge_index = negative_sampling(pos_edge_index, z.size(0))
        out = self.decoder.forward_for_loss(z, neg_edge_index)
        neg_loss = -torch.log(1 - out + EPS).mean()

        return pos_loss + neg_loss

    def kl_loss(self, mu=None,
                logstd=None):
        r"""Computes the KL loss, either for the passed arguments :obj:`mu`
        and :obj:`logstd`, or based on latent variables from last encoding.

        Args:
            mu (torch.Tensor, optional): The latent space for :math:`\mu`. If
                set to :obj:`None`, uses the last computation of :math:`\mu`.
                (default: :obj:`None`)
            logstd (torch.Tensor, optional): The latent space for
                :math:`\log\sigma`.  If set to :obj:`None`, uses the last
                computation of :math:`\log\sigma^2`. (default: :obj:`None`)
        """
        MAX_LOGSTD = 10
        mu = self.__mu__ if mu is None else mu
        logstd = self.__logstd__ if logstd is None else logstd.clamp(
            max=MAX_LOGSTD)
        return -0.5 * torch.mean(
            torch.sum(1 + 2 * logstd - mu ** 2 - logstd.exp() ** 2, dim=1))

    def add_to_scene(self, additions, data=None, test=False):
        scene = None
        if data is not None and test == False:
            x = data.x
            y = data.y
            edge = data.edge_index
            yInitEmb = self.labelEmb(y)
            xInitEmb = torch.cat((x, yInitEmb), dim=1)
            z, _, _ = self.encoder(xInitEmb, edge)
            z = torch.cat((z, yInitEmb), dim=1)
            additionZ = torch.randn(len(additions), latent_dim).to(device)
            additionsTensor = torch.LongTensor(additions).to(device)
            yAdditionEmb = self.labelEmb(additionsTensor)
            additionZ = torch.cat((additionZ, yAdditionEmb), dim=1)
            newY = torch.cat((y, additionsTensor), dim=0)
            newgraphZ = torch.cat((z, additionZ), dim=0)
            recon = self.decoder(newgraphZ)
            recon = recon[0]
            adj = self.decoder.forward_all(newgraphZ)
            Scene.reset_instance()
            scene = CreateSceneFromGNNOutput(recon, adj, newY, True)
        elif data is not None and test:
            x = data.x
            y = data.y
            allz = None
            for i in range(x.shape[0]):
                tempx = x[i].reshape(1, x.shape[1])
                tempy = y[i].reshape(1, )
                edge = torch.zeros((2, 1)).long().to(device)
                yInitEmb = self.labelEmb(tempy)
                xInitEmb = torch.cat((tempx, yInitEmb), dim=1)
                z, _, _ = self.encoder(xInitEmb, edge)
                z = torch.cat((z, yInitEmb), dim=1)
                if allz is None:
                    allz = z
                else:
                    allz = torch.cat((allz, z), dim=0)
            additionZ = torch.randn(len(additions), latent_dim).to(device)
            additionsTensor = torch.LongTensor(additions).to(device)
            yAdditionEmb = self.labelEmb(additionsTensor)
            additionZ = torch.cat((additionZ, yAdditionEmb), dim=1)
            newY = torch.cat((y, additionsTensor), dim=0)
            newgraphZ = torch.cat((allz, additionZ), dim=0)
            recon = self.decoder(newgraphZ)
            recon = recon[0]
            adj = self.decoder.forward_all(newgraphZ)
            Scene.reset_instance()
            scene = CreateSceneFromGNNOutput(recon, adj, newY, True)
        else:
            additions.append(0)
            additionZ = torch.randn(len(additions), latent_dim).to(device)
            additionsTensor = torch.LongTensor(additions).to(device)
            yAdditionEmb = self.labelEmb(additionsTensor)
            additionZ = torch.cat((additionZ, yAdditionEmb), dim=1)
            newY = additionsTensor
            newgraphZ = additionZ
            recon = self.decoder(newgraphZ)
            recon = recon[0]
            adj = self.decoder.forward_all(newgraphZ)
            Scene.reset_instance()
            scene = CreateSceneFromGNNOutput(recon, adj, newY, True)
        return scene


mydata = []
for i in range(1000):
    Scene.reset_instance()
    scene = Scene()
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    SceneLoader.LoadScene(scene, "Training_Scenes/Training_Scenes2/scene" + str(i) + ".usd")
    # This line can be changed to different GA converting functions, for example TRS, CGA etc.
    data = Converter.ECStoGNNSimpleTransQuat(scene)

eachrun = np.zeros((100, 10))
for run in range(10):
    print("Run:", run)
    random.shuffle(mydata)
    mydata = mydata[:500]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    encoder = VariationalGCNEncoder(features + label_emb, latent_dim)
    decoder = VariationalGCNDecoder(latent_dim + label_emb, features)
    model = VariationalAE(encoder, decoder, label_emb).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    epochs = 100
    batch_size = 8
    train_loader = DataLoader(mydata, batch_size=batch_size, shuffle=True)
    criterion = torch.nn.MSELoss()
    model.train()
    allrows = []
    alllosses = []
    for i in range(epochs):
        losses = []
        for t in train_loader:
            t = t.to(device)
            optimizer.zero_grad()
            x, z = model(t.x, t.edge_index, t.y, t.batch)
            loss1 = model.recon_loss(z, t.edge_index)
            loss2 = criterion(x, t.x)
            loss3 = (1 / t.num_nodes) * model.kl_loss()  # new line
            loss = loss1 + loss2 + loss3
            losses.append(loss.item())
            loss.backward()
            optimizer.step()
        print("Epoch ", i, ": Loss:", np.mean(np.asarray(losses)))
        eachrun[i][run] = np.mean(np.asarray(losses))
        row = ["Epoch " + str(i), str(np.mean(np.asarray(losses)))]
        allrows.append(row)
        alllosses.append(np.mean(np.asarray(losses)))
