import wgpu 
import numpy as np
from Elements.pyGLV.GL.wgpu_texture import Texture

class Uniform:
    name:str
    size:int
    data:any
    usage:any
    type:any
    dirty:bool
    offset:int
    isSet:bool
    dirty:bool

class TextureUniform:
    name:str
    texture:Texture
    usage:any
    sampleType:any
    dimension:any 

class SamplerUniform:
    name:str
    sampler:any
    usage:any
    compare:bool 

class UniformGroup:
    def __init__(self, groupName:str, groupIndex:int):
        self.groupName = groupName 
        self.groupIndex = groupIndex

        self.uniforms = {} 
        self.storages = {}
        self.isStorageDirty:bool = True;
        self.isUniformsDirty:bool = True;
        self.textureUniforms = {}
        self.sampleUniforms = {}

        self.uniformBuffer = any 
        self.storageBuffers = {} 

        self.bindGroupLayout:wgpu.GPUBindGroupLayout 
        self.bindGroup:wgpu.GPUBindGroup

    def addUniform(self,
                   name:str, 
                   data:any, 
                   size:int,
                   offset:int,
                   usage:any=(wgpu.BufferUsage.VERTEX | wgpu.ShaderStage.FRAGMENT), 
                   type:any=wgpu.BufferBindingType.uniform,
    ): 
        b = Uniform() 
        b.data = data
        b.name = name
        b.size = size  
        b.usage = usage
        b.type = type  
        b.isSet = False
        b.dirty = True 
        b.offset = offset

        # self.uniforms[b.name] = b   
        self.uniforms.update({b.name: b})

    def addStorage(self,
                   name:str, 
                   data:any, 
                   size:int,
                   usage:any=wgpu.BufferUsage.VERTEX | wgpu.ShaderStage.FRAGMENT, 
                   type:any=wgpu.BufferBindingType.read_only_storage,
    ): 
        b = Uniform() 
        b.data = data
        b.name = name
        b.size = size  
        b.usage = usage
        b.type = type  
        b.isSet = False
        b.dirty = True 

        # self.storages[b.name] = b  
        self.storages.update({b.name: b})

    def addTexture(self,
                    name:str,
                    value:Texture=None,
                    usage:any=wgpu.ShaderStage.FRAGMENT,
                    sampleType:any=wgpu.TextureSampleType.float,
                    dimension:any=wgpu.TextureViewDimension.d2,
    ):
        t = TextureUniform() 
        t.name = name
        t.texture = value
        t.usage = usage
        t.sampleType = sampleType
        t.dimension = dimension 

        self.textureUniforms.update({t.name: t})

    def addSampler(self,
                  name:str,  
                  sampler:any,
                  usage:any=wgpu.ShaderStage.FRAGMENT,
                  compare=False
    ): 
        s = SamplerUniform()
        s.name = name
        s.usage = usage
        s.sampler = sampler 
        s.compare = compare

        self.sampleUniforms[s.name] = s

    def setUniform(self,
                    name:str,
                    value:any
    ): 
        # if self.uniforms[name] in None:
        #     exit("Buffer not in buffergroup") 

        self.isUniformsDirty = True  
        self.uniforms[name].data = value  
        self.uniforms[name].isSet = True 

    def setStorage(self,
                    name:str,
                    value:any
    ): 
        # if self.storages[name] in None:
        #     exit("Buffer not in buffergroup") 

        self.isStorageDirty= True 
        self.storages[name].data = value 
        self.storages[name].isSet = True 

    def setTexture(self, name:str, value:Texture):
        # if self.textureUniforms.get(name) in None:
        #     exit("Texture not in buffergroup")

        self.textureUniforms.get(name).texture = value  

    def makeUniformBuffer(self, device:wgpu.GPUDevice): 
        # buffer = []
        # for key, data in self.uniforms:
        #     buffer.append(data.data)  

        # sbuffer = sorted(buffer, key=lambda x:x.offset) 
        # ndbuffer = np.asarray(sbuffer)
        size = 0;
        for key, data in self.uniforms.items():
            size += data.size 

        self.uniformBuffer = device.create_buffer(
            size=size, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        )
 

    def makeStorageBuffers(self, device:wgpu.GPUDevice): 
        for key, data in self.storages.items(): 
            self.storageBuffers[key] = device.create_buffer(
                size=data.size, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
            )  
        

    def updateUniformBuffer(self, device:wgpu.GPUDevice, command_encoder:wgpu.GPUCommandEncoder):  
        buffer = [] 
        for key, data in self.uniforms.items():
            buffer.append(data) 
        sbuffer = sorted(buffer, key=lambda x:x.offset)

        extract = []
        for data in sbuffer:
            extract.append(np.array(data.data, dtype=np.float32)) 

        ndbuffer = np.asarray(extract, dtype=np.float32)  

        tempBuffer = device.create_buffer_with_data(
            data=ndbuffer, usage=wgpu.BufferUsage.COPY_SRC
        ) 

        command_encoder.copy_buffer_to_buffer(
            tempBuffer, 0, self.uniformBuffer, 0, ndbuffer.nbytes
        )  

    def updateStorageBuffers(self, device:wgpu.GPUDevice, command_encoder:wgpu.GPUCommandEncoder):  
        for key, data in self.storages.items(): 
            tempBuffer = device.create_buffer_with_data(
                data=data.data, usage=wgpu.BufferUsage.COPY_SRC
            ) 
            command_encoder.copy_buffer_to_buffer(
                tempBuffer, 0, self.storageBuffers[key], 0, tempBuffer.size 
            )  

    def makeBindGroupLayout(self, device:wgpu.GPUDevice):
        bindingCount = 0; 
        entries = [] 

        if len(self.uniforms) > 0:
            entries.append({ 
                "binding": bindingCount,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {
                    "type": wgpu.BufferBindingType.uniform
                }
            }) 
            bindingCount += 1

        if len(self.storages) > 0: 
            for key, data in self.storages.items():
                entries.append({
                    "binding": bindingCount,
                    "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                    "buffer": {
                        "type": wgpu.BufferBindingType.read_only_storage,
                    }
                }) 
                bindingCount += 1

        if len(self.textureUniforms) > 0:
            for key, data in self.textureUniforms.items():
                entries.append({ 
                    "binding": bindingCount,
                    "visibility": data.usage,
                    "texture": {  
                        "sample_type": data.sampleType,
                        "view_dimension": data.dimension,
                    }
                }) 
                bindingCount += 1

        if len(self.sampleUniforms) > 0:
            for key, data in self.sampleUniforms.items():
                stype = any
                if data.compare:
                    stype = {"type": wgpu.SamplerBindingType.comparison} 
                else:
                    stype = {"type": wgpu.SamplerBindingType.filtering}

                entries.append({ 
                    "binding": bindingCount,
                    "visibility": data.usage,
                    "sampler": stype,
                }) 

                bindingCount += 1  

        self.bindGroupLayout = device.create_bind_group_layout(
            entries=entries
        ) 

    def makeBindGroup(self, device:wgpu.GPUDevice):
        entries = [] 
        bindingCount = 0

        if len(self.uniforms) > 0:
            entries.append({
                "binding": bindingCount,
                "resource": {
                    "buffer": self.uniformBuffer,
                    "offset": 0,
                    "size": self.uniformBuffer.size,
                },
            })  
            bindingCount += 1

        if len(self.storages) > 0: 
            for key, data in self.storageBuffers.items(): 
                entries.append({ 
                    "binding": bindingCount,
                    "resource": {
                        "buffer": data, 
                        "offset": 0,
                        "size": data.size,
                    },
                }) 
                bindingCount += 1 

        if len(self.textureUniforms) > 0: 
            for key, value in self.textureUniforms.items():
                entries.append({ 
                    "binding": bindingCount,
                    "resource": value.texture.getView()
                }) 
                bindingCount += 1 

        if len(self.sampleUniforms) > 0: 
            for key, value in self.sampleUniforms.items():
                entries.append({ 
                    "binding": bindingCount,
                    "resource": value.sampler 
                }) 

        self.bindGroup = device.create_bind_group(
            layout=self.bindGroupLayout,
            entries=entries
        )

    def update(self, device:wgpu.GPUDevice, command_encoder:wgpu.GPUCommandEncoder):
        if self.uniformBuffer:
            self.updateUniformBuffer(device=device, command_encoder=command_encoder)  
        if len(self.storageBuffers):
            self.updateStorageBuffers(device=device, command_encoder=command_encoder)