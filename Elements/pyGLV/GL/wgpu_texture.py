import wgpu
from PIL import Image

from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from dataclasses import dataclass  
from assertpy import assert_that

@dataclass
class Texture:
    texture: wgpu.GPUTexture = None
    view: wgpu.GPUTextureView = None 
    sampler: wgpu.GPUSampler = None 
    img_bytes: bytes = None 
    width: int = None 
    height: int = None
    array_level: int = None

class TextureLib():

    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating TextureLib Singleton Object')
            cls._instance = super(TextureLib, cls).__new__(cls) 

            cls.textures = {}   
            cls.skyBoxes = {}

        return cls._instance

    def __init__(self):
        None; 
 
    def make_texture(self, name:str, path=None): 

        if self.textures.get(name) is not None:
            return self.textures.get(name) 

        assert_that((path != None), "Give the path to the texture").is_true()
        img = Image.open(path) 
        img_bytes = img.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

        width = img.width 
        height = img.height 
        size = [width, height, 1] 

        texture: wgpu.GPUTexture = GpuController().device.create_texture(
            size=size,
            usage = wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.RENDER_ATTACHMENT,
            dimension = wgpu.TextureDimension.d2,
            format = wgpu.TextureFormat.rgba8unorm,
            mip_level_count = 1,
            sample_count = 1,
        )

        view = texture.create_view() 

        GpuController().device.queue.write_texture(
            {
                "texture": texture,
                "mip_level": 0,
                "origin": (0, 0, 0)
            },
            img_bytes,
            {
                "offset": 0,
                "bytes_per_row": width * 4,
                "rows_per_image": height,
            },
            size
        )  

        sampler = GpuController().device.create_sampler()

        self.textures.update({name: Texture(texture, view, sampler, img_bytes, width, height, 1)})

    def make_skybox(self, name:str, paths:list=None): 
        
        if self.skyBoxes.get(name) is not None: 
            return self.skyBoxes.get(name)

        assert_that((paths != None), "Give the path to the texture").is_true() 

        width = [] 
        height = [] 
        data = []

        for path in paths:
            img = Image.open(path) 
            img_bytes = img.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

            width.append(img.width)
            height.append(img.height) 
            data.append(img_bytes) 

        bytedata = bytes() 
        for d in data:
            bytedata += d 

        texture: wgpu.GPUTexture = GpuController().device.create_texture(
            size=[width[0], height[0], 6],
            usage = wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.RENDER_ATTACHMENT,
            dimension = wgpu.TextureDimension.d2,
            format = wgpu.TextureFormat.rgba8unorm,
            mip_level_count = 1,
            sample_count = 1,
        )

        view = texture.create_view(
            format=wgpu.TextureFormat.rgba8unorm,
            dimension=wgpu.TextureViewDimension.cube,
            aspect=wgpu.TextureAspect.all,
            base_mip_level=0,
            mip_level_count=1, 
            base_array_layer=0,
            array_layer_count=6
        ) 

        GpuController().device.queue.write_texture(
            {
                "texture": texture,
                "mip_level": 0,
                "origin": (0, 0, 0)
            },
            bytedata,
            {
                "offset": 0,
                "bytes_per_row": width[0] * 4,
                "rows_per_image": height[0],
            }, 
            [width[0], height[0], 6]
        )  

        sampler = GpuController().device.create_sampler()

        self.skyBoxes.update({name: Texture(texture, view, sampler, bytedata, width[0], height[0], 6)}) 

    def get_texture(self, name:str): 
        return self.textures.get(name)
             
    def get_skybox(self, name:str):
        return self.skyBoxes.get(name)
        