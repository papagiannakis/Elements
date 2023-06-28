import pickle

import numpy as np
import torch

from Elements.pyECSS.GA.quaternion import Quaternion
from Elements.pyGLV.examples.GAUtils import matrix_to_motor, matrix_to_angle_axis_translation
from atlas.model import MODEL_LIST
from Elements.pyECSS.Component import RenderMesh, BasicTransform
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, Shader
from Elements.pyGLV.GL.VertexArray import VertexArray
import CreateScenes
file = open("atlas/opt.pickle", 'rb')
opt = pickle.load(file)
file.close()
# list of all the methods
MODEL = MODEL_LIST(opt)  # list of all the models
if opt.model not in MODEL.type:
    print("ERROR please select the model from : ")
    for model in sorted(MODEL.type):
        print("   >", model)
    exit()

network = MODEL.load(opt)  # load the loss

network.load_state_dict(torch.load("atlas/network.pth"))
network.eval()


def ECStoGNN(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        if "Cam" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)
    # Find and append all TRS and Mesh components to the graph list and also the TRS component and Mesh Component list
    for comp in scene.world.components:
        # if "Cam" in comp.parent.name or "Entity1" in comp.parent.name:
        #     continue
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                if comp.vertex_attributes[0].shape[0] == 0:
                    continue
                compslistmesh.append(comp)

    # Create the features list of each entity, which is a length 3 vector that holds a counter of the number of children of this
    # entity based on type (entity, trs, mesh). Also create the edges lists between the entities and their children
    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Cam" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    if ch.vertex_attributes[0].shape[0] == 0:
                        continue
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []

    # Create features of each component. For TRS add noise to it and flatten it into a vector. For Mesh, sample 2500 vertices
    # add a small noise and pass it as input to atlasnet's encoder. The output is a 1024 length feature vector which is the
    # feature of our Mesh nodes
    for g in graph:
        if isinstance(g, BasicTransform):
            g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            feats = g.trs.flatten()
            compfeaturestrans.append(feats)
        elif isinstance(g, RenderMesh):
            if g.vertex_attributes[0].shape[0] == 0:
                continue
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            noise = np.random.normal(0, .1, pcdvert.shape)
            pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData
    # Create the pytorch GNN hetero graph
    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def GNNtoECS(graph):
    file = open("atlas/opt.pickle", 'rb')
    opt = pickle.load(file)
    file.close()
    # list of all the methods
    MODEL = MODEL_LIST(opt)  # list of all the models
    if opt.model not in MODEL.type:
        print("ERROR please select the model from : ")
        for model in sorted(MODEL.type):
            print("   >", model)
        exit()

    network = MODEL.load(opt)  # load the loss

    network.load_state_dict(torch.load("atlas/network.pth"))
    network.eval()
    entities = {}
    meshcomp = {}
    trscomp = {}
    j = 0
    scene = Scene()
    # Find all entities in the graph and create an instance for them
    for en in graph['entity'].x:
        if j == 0:
            actualentity = scene.world.createEntity(Entity(name="RooT"))
        else:
            actualentity = scene.world.createEntity(Entity(name="ent" + str(j)))
        entities[j] = actualentity
        # scene.world.createEntity(actualentity)
        j += 1
    j = 0
    # For each mesh, decode through atlasnet its feature vector back to the sampled point cloud and reconstruct the mesh and
    # create a render mesh component
    for mesh in graph['mesh'].x:
        patches = []
        outs = []
        a = mesh
        a = a.reshape(1, a.shape[0])
        for i in range(0, network.npatch):
            # random planar patch
            # ==========================================================================
            rand_grid = network.grid[i].expand(a.size(0), -1, -1)
            patches.append(rand_grid[0].transpose(1, 0))
            # ==========================================================================

            # cat with latent vector and decode
            # ==========================================================================
            y = a.unsqueeze(2).expand(a.size(0), a.size(1), rand_grid.size(2)).contiguous()
            y = torch.cat((rand_grid, y), 1).contiguous()
            outs.append(network.decoder[i](y))
            # ==========================================================================

        myout = torch.cat(outs, 2).transpose(2, 1).contiguous(), patches
        myout = myout[0][0]
        mymeshcomp = RenderMesh(name="mesh" + str(j))
        import pyvista as pv
        import open3d as o3d
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.asarray(myout.detach().cpu()))
        pcd.estimate_normals()
        trimesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd)
        bbox = pcd.get_axis_aligned_bounding_box()
        trimesh = trimesh.crop(bbox)
        v = np.asarray(trimesh.vertices)
        f = np.array(trimesh.triangles)
        f = np.c_[np.full(len(f), 3), f]
        mesh = pv.PolyData(v, f)
        mesh = mesh.clean()
        # mesh.plot()
        shell = mesh
        colors = []
        for i in range(shell.n_points):
            colors.append([1.0, 0.0, 0.0, 1.0])
        mymeshcomp.vertex_attributes.append(np.asarray(shell.points))
        mymeshcomp.vertex_attributes.append(np.asarray(colors))
        mymeshcomp.vertex_index.append(shell.faces)

        meshcomp[j] = mymeshcomp
        j += 1
    j = 0
    # For each trs, create a Basic Transform component
    for trs in graph['trs'].x:
        trscomp[j] = BasicTransform(name="trs" + str(j), trs=np.asarray(trs.detach().cpu().reshape(4, 4)))
        # trscomp[j].trs = util.scale(5, 5, 5)
        # print(trscomp[j].trs)

        j += 1

    # Based on the edges list and the edges types, create the parent-children relationships
    for i in range(graph['entity', 'entparent', 'entity'].edge_index.shape[1]):
        scene.world.addEntityChild(entities[graph['entity', 'entparent', 'entity'].edge_index[0][i].item()],
                                   entities[graph['entity', 'entparent', 'entity'].edge_index[1][i].item()])

    for i in range(graph['entity', 'trsparent', 'trs'].edge_index.shape[1]):
        scene.world.addComponent(entities[graph['entity', 'trsparent', 'trs'].edge_index[0][i].item()],
                                 trscomp[graph['entity', 'trsparent', 'trs'].edge_index[1][i].item()])

    for i in range(graph['entity', 'meshparent', 'mesh'].edge_index.shape[1]):
        scene.world.addComponent(entities[graph['entity', 'meshparent', 'mesh'].edge_index[0][i].item()],
                                 meshcomp[graph['entity', 'meshparent', 'mesh'].edge_index[1][i].item()])
        scene.world.addComponent(entities[graph['entity', 'meshparent', 'mesh'].edge_index[0][i].item()],
                                 VertexArray())
        scene.world.addComponent(entities[graph['entity', 'meshparent', 'mesh'].edge_index[0][i].item()],
                                 ShaderGLDecorator(
                                     Shader(vertex_source=Shader.COLOR_VERT_MVP,
                                            fragment_source=Shader.COLOR_FRAG)))

    return scene


def ECStoGNNNoNoise(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    for ent in scene.world.entities:
        if "Camera" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)

    for comp in scene.world.components:
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                if comp.vertex_attributes[0].shape[0] == 0:
                    continue
                compslistmesh.append(comp)

    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Camera" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    if ch.vertex_attributes[0].shape[0] == 0:
                        continue
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []
    file = open("atlas/opt.pickle", 'rb')
    opt = pickle.load(file)
    file.close()
    # list of all the methods
    MODEL = MODEL_LIST(opt)  # list of all the models
    if opt.model not in MODEL.type:
        print("ERROR please select the model from : ")
        for model in sorted(MODEL.type):
            print("   >", model)
        exit()

    network = MODEL.load(opt)  # load the loss

    network.load_state_dict(torch.load("atlas/network.pth"))
    network.eval()
    for g in graph:
        if isinstance(g, BasicTransform):
            # g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            feats = g.trs.flatten()
            compfeaturestrans.append(feats)
        elif isinstance(g, RenderMesh):
            if g.vertex_attributes[0].shape[0] == 0:
                continue
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            # noise = np.random.normal(0, .1, pcdvert.shape)
            # pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData

    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data

def ECStoGNNSimple(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    entslist = []
    entsfeats = []
    y = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        exists = False
        index = -1
        for i in range(len(CreateScenes.objs)):
            if CreateScenes.objs[i] in ent.name.lower():
                exists = True
                index = i
                break
        if exists:
            entslist.append(ent)
            y.append(index)
    for i in range(len(entslist)):
        if entslist[i].name.lower() in "root":
            entsfeats.append(np.zeros(16, ))
        for ch in entslist[i]._children:
            if isinstance(ch, BasicTransform):
                entsfeats.append(ch.trs.flatten())
            elif isinstance(ch, Entity) and ch in entslist:
                edges0ent.append(i)
                edges1ent.append(entslist.index(ch))

    from torch_geometric.data import Data
    # Create the pytorch GNN hetero graph
    data = Data()

    data.x = torch.FloatTensor(np.asarray(entsfeats))
    data.y = torch.LongTensor(np.asarray(y))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data.edge_index = edgesent
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNSimpleCGA(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    entslist = []
    entsfeats = []
    y = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        exists = False
        index = -1
        for i in range(len(CreateScenes.objs)):
            if CreateScenes.objs[i] in ent.name.lower():
                exists = True
                index = i
                break
        if exists:
            entslist.append(ent)
            y.append(index)
    for i in range(len(entslist)):
        if entslist[i].name.lower() in "root":
            entsfeats.append(np.zeros(32, ))
        for ch in entslist[i]._children:
            if isinstance(ch, BasicTransform):
                entsfeats.append(matrix_to_motor(ch.trs, method='CGA').value)
            elif isinstance(ch, Entity) and ch in entslist:
                edges0ent.append(i)
                edges1ent.append(entslist.index(ch))

    from torch_geometric.data import Data
    # Create the pytorch GNN hetero graph
    data = Data()

    data.x = torch.FloatTensor(np.asarray(entsfeats))
    data.y = torch.LongTensor(np.asarray(y))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data.edge_index = edgesent
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNSimplePGA(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    entslist = []
    entsfeats = []
    y = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        exists = False
        index = -1
        for i in range(len(CreateScenes.objs)):
            if CreateScenes.objs[i] in ent.name.lower():
                exists = True
                index = i
                break
        if exists:
            entslist.append(ent)
            y.append(index)
    for i in range(len(entslist)):
        if entslist[i].name.lower() in "root":
            entsfeats.append(np.zeros(16, ))
        for ch in entslist[i]._children:
            if isinstance(ch, BasicTransform):
                entsfeats.append(matrix_to_motor(ch.trs, method='PGA').value)
            elif isinstance(ch, Entity) and ch in entslist:
                edges0ent.append(i)
                edges1ent.append(entslist.index(ch))

    from torch_geometric.data import Data
    # Create the pytorch GNN hetero graph
    data = Data()

    data.x = torch.FloatTensor(np.asarray(entsfeats))
    data.y = torch.LongTensor(np.asarray(y))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data.edge_index = edgesent
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNSimpleTransAngleAxis(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    entslist = []
    entsfeats = []
    y = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        exists = False
        index = -1
        for i in range(len(CreateScenes.objs)):
            if CreateScenes.objs[i] in ent.name.lower():
                exists = True
                index = i
                break
        if exists:
            entslist.append(ent)
            y.append(index)
    for i in range(len(entslist)):
        if entslist[i].name.lower() in "root":
            entsfeats.append(np.zeros(7, ))
        for ch in entslist[i]._children:
            if isinstance(ch, BasicTransform):
                tempfeats = np.zeros(7, )
                extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                    ch.trs)  # notice theta is in rad
                tempfeats[0] = extracted_translation_vector[0]
                tempfeats[1] = extracted_translation_vector[1]
                tempfeats[2] = extracted_translation_vector[2]
                tempfeats[3] = extracted_theta
                tempfeats[4] = extracted_axis[0]
                tempfeats[5] = extracted_axis[1]
                tempfeats[6] = extracted_axis[2]
                entsfeats.append(tempfeats)
            elif isinstance(ch, Entity) and ch in entslist:
                edges0ent.append(i)
                edges1ent.append(entslist.index(ch))

    from torch_geometric.data import Data
    # Create the pytorch GNN hetero graph
    data = Data()

    data.x = torch.FloatTensor(np.asarray(entsfeats))
    data.y = torch.LongTensor(np.asarray(y))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data.edge_index = edgesent
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNSimpleTransQuat(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    entslist = []
    entsfeats = []
    y = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        exists = False
        index = -1
        for i in range(len(CreateScenes.objs)):
            if CreateScenes.objs[i] in ent.name.lower():
                exists = True
                index = i
                break
        if exists:
            entslist.append(ent)
            y.append(index)
    for i in range(len(entslist)):
        if entslist[i].name.lower() in "root":
            entsfeats.append(np.zeros(7, ))
        for ch in entslist[i]._children:
            if isinstance(ch, BasicTransform):
                tempfeats = np.zeros(7, )
                extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                    ch.trs)  # notice theta is in rad
                q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
                tempfeats[0] = extracted_translation_vector[0]
                tempfeats[1] = extracted_translation_vector[1]
                tempfeats[2] = extracted_translation_vector[2]
                tempfeats[3] = q.q[0]
                tempfeats[4] = q.q[1]
                tempfeats[5] = q.q[2]
                tempfeats[6] = q.q[3]
                entsfeats.append(tempfeats)
            elif isinstance(ch, Entity) and ch in entslist:
                edges0ent.append(i)
                edges1ent.append(entslist.index(ch))

    from torch_geometric.data import Data
    # Create the pytorch GNN hetero graph
    data = Data()

    data.x = torch.FloatTensor(np.asarray(entsfeats))
    data.y = torch.LongTensor(np.asarray(y))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data.edge_index = edgesent
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNCGA(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        if "Cam" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)
    # Find and append all TRS and Mesh components to the graph list and also the TRS component and Mesh Component list
    for comp in scene.world.components:
        # if "Cam" in comp.parent.name or "Entity1" in comp.parent.name:
        #     continue
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                compslistmesh.append(comp)

    # Create the features list of each entity, which is a length 3 vector that holds a counter of the number of children of this
    # entity based on type (entity, trs, mesh). Also create the edges lists between the entities and their children
    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Cam" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []

    # Create features of each component. For TRS add noise to it and flatten it into a vector. For Mesh, sample 2500 vertices
    # add a small noise and pass it as input to atlasnet's encoder. The output is a 1024 length feature vector which is the
    # feature of our Mesh nodes
    for g in graph:
        if isinstance(g, BasicTransform):
            g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            # feats = g.trs.flatten()
            compfeaturestrans.append(matrix_to_motor(g.trs, method='CGA').value)
        elif isinstance(g, RenderMesh):
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            noise = np.random.normal(0, .1, pcdvert.shape)
            pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData
    # Create the pytorch GNN hetero graph
    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNPGA(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        if "Cam" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)
    # Find and append all TRS and Mesh components to the graph list and also the TRS component and Mesh Component list
    for comp in scene.world.components:
        # if "Cam" in comp.parent.name or "Entity1" in comp.parent.name:
        #     continue
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                compslistmesh.append(comp)

    # Create the features list of each entity, which is a length 3 vector that holds a counter of the number of children of this
    # entity based on type (entity, trs, mesh). Also create the edges lists between the entities and their children
    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Cam" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []

    # Create features of each component. For TRS add noise to it and flatten it into a vector. For Mesh, sample 2500 vertices
    # add a small noise and pass it as input to atlasnet's encoder. The output is a 1024 length feature vector which is the
    # feature of our Mesh nodes
    for g in graph:
        if isinstance(g, BasicTransform):
            g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            # feats = g.trs.flatten()
            compfeaturestrans.append(matrix_to_motor(g.trs, method='PGA').value)
        elif isinstance(g, RenderMesh):
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            noise = np.random.normal(0, .1, pcdvert.shape)
            pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData
    # Create the pytorch GNN hetero graph
    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNTransAngle(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        if "Cam" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)
    # Find and append all TRS and Mesh components to the graph list and also the TRS component and Mesh Component list
    for comp in scene.world.components:
        # if "Cam" in comp.parent.name or "Entity1" in comp.parent.name:
        #     continue
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                compslistmesh.append(comp)

    # Create the features list of each entity, which is a length 3 vector that holds a counter of the number of children of this
    # entity based on type (entity, trs, mesh). Also create the edges lists between the entities and their children
    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Cam" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []

    # Create features of each component. For TRS add noise to it and flatten it into a vector. For Mesh, sample 2500 vertices
    # add a small noise and pass it as input to atlasnet's encoder. The output is a 1024 length feature vector which is the
    # feature of our Mesh nodes
    for g in graph:
        if isinstance(g, BasicTransform):
            g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                g.trs)  # notice theta is in rad
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = extracted_theta
            tempfeats[4] = extracted_axis[0]
            tempfeats[5] = extracted_axis[1]
            tempfeats[6] = extracted_axis[2]
            compfeaturestrans.append(tempfeats)
        elif isinstance(g, RenderMesh):
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            noise = np.random.normal(0, .1, pcdvert.shape)
            pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData
    # Create the pytorch GNN hetero graph
    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data


def ECStoGNNTransQuat(scene):
    graph = []
    edges0ent = []
    edges1ent = []
    edges0enttrans = []
    edges1enttrans = []
    edges0entmesh = []
    edges1entmesh = []
    entslist = []
    compslistmesh = []
    compslisttrans = []
    # Find and append all entities to the graph list and also the entity list
    for ent in scene.world.entities:
        if "Cam" in ent.name or "Entity1" in ent.name:
            continue
        graph.append(ent)
        entslist.append(ent)
    # Find and append all TRS and Mesh components to the graph list and also the TRS component and Mesh Component list
    for comp in scene.world.components:
        # if "Cam" in comp.parent.name or "Entity1" in comp.parent.name:
        #     continue
        if isinstance(comp, BasicTransform) or isinstance(comp, RenderMesh):
            graph.append(comp)
            if isinstance(comp, BasicTransform):
                compslisttrans.append(comp)
            else:
                compslistmesh.append(comp)

    # Create the features list of each entity, which is a length 3 vector that holds a counter of the number of children of this
    # entity based on type (entity, trs, mesh). Also create the edges lists between the entities and their children
    entfeatures = []
    for g in graph:
        feats = np.zeros((3,))
        if isinstance(g, Entity):
            for ch in g._children:
                if isinstance(ch, Entity) and not ("Cam" in ch.name or "Entity1" in ch.name):
                    edges0ent.append(entslist.index(g))
                    edges1ent.append(entslist.index(ch))
                    feats[0] += 1
                elif isinstance(ch, BasicTransform):
                    edges0enttrans.append(entslist.index(g))
                    edges1enttrans.append(compslisttrans.index(ch))
                    feats[1] += 1
                elif isinstance(ch, RenderMesh):
                    edges0entmesh.append(entslist.index(g))
                    edges1entmesh.append(compslistmesh.index(ch))
                    feats[2] += 1
            entfeatures.append(feats)

    compfeaturestrans = []
    compfeaturesmesh = []

    # Create features of each component. For TRS add noise to it and flatten it into a vector. For Mesh, sample 2500 vertices
    # add a small noise and pass it as input to atlasnet's encoder. The output is a 1024 length feature vector which is the
    # feature of our Mesh nodes
    for g in graph:
        if isinstance(g, BasicTransform):
            g.trs = g.trs + np.random.uniform(0, 0.2, (4, 4))
            tempfeats = np.zeros(7, )
            extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
                g.trs)  # notice theta is in rad
            q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
            tempfeats[0] = extracted_translation_vector[0]
            tempfeats[1] = extracted_translation_vector[1]
            tempfeats[2] = extracted_translation_vector[2]
            tempfeats[3] = q.q[0]
            tempfeats[4] = q.q[1]
            tempfeats[5] = q.q[2]
            tempfeats[6] = q.q[3]
            compfeaturestrans.append(tempfeats)
        elif isinstance(g, RenderMesh):
            choice = np.random.choice(len(np.asarray(g.vertex_attributes[0])), 2500, replace=True)
            pcdvert = np.asarray(g.vertex_attributes[0])[choice, :3].transpose()
            noise = np.random.normal(0, .1, pcdvert.shape)
            pcdvert += noise
            pcdvert = np.reshape(pcdvert, (1, pcdvert.shape[0], pcdvert.shape[1]))
            feats = network.encoder(torch.tensor(pcdvert).float().cuda())
            feats = np.array(feats.detach().cpu())
            feats = feats.reshape((feats.shape[1],))
            compfeaturesmesh.append(feats)

    from torch_geometric.data import HeteroData
    # Create the pytorch GNN hetero graph
    data = HeteroData()

    data['entity'].x = torch.FloatTensor(np.asarray(entfeatures))
    data['trs'].x = torch.FloatTensor(np.asarray(compfeaturestrans))
    data['mesh'].x = torch.FloatTensor(np.asarray(compfeaturesmesh))
    edgesent = torch.LongTensor([edges0ent, edges1ent])
    data['entity', 'entparent', 'entity'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0enttrans, edges1enttrans])
    data['entity', 'trsparent', 'trs'].edge_index = edgesent
    edgesent = torch.LongTensor([edges0entmesh, edges1entmesh])
    data['entity', 'meshparent', 'mesh'].edge_index = edgesent
    # data.y = y[len(y) - 1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = data.to(device)
    return data
