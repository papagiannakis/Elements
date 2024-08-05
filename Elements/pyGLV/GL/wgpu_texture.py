import wgpu 
import numpy as np
from PIL import Image

from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from dataclasses import dataclass  
from assertpy import assert_that

@dataclass
class Texture: 
    """
    A data class to store texture properties and resources.
    """ 

    texture: wgpu.GPUTexture = None
    view: wgpu.GPUTextureView = None 
    sampler: wgpu.GPUSampler = None 
    img_bytes: bytes = None 
    width: int = None 
    height: int = None
    array_level: int = None

class TextureLib():
    """
    Singleton class to manage textures and skyboxes.
    """    

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
    
    def calculate_aligned_bytes_per_row(self, width, bytes_per_pixel):
        """
        Calculates the aligned bytes per row for texture data.

        :param width: Width of the texture.
        :param bytes_per_pixel: Number of bytes per pixel.
        :return: Aligned bytes per row.
        """
    
        bytes_per_row = width * bytes_per_pixel
        aligned_bytes_per_row = ((bytes_per_row + 255) // 256) * 256
        return aligned_bytes_per_row
 
    def make_texture(self, name:str, path=None, format=wgpu.TextureFormat.rgba8unorm):
        """
        Creates and stores a texture from an image file.

        :param name: Name of the texture.
        :param path: Path to the image file.
        :param format: Texture format (default is rgba8unorm).
        """

        if self.textures.get(name) is not None:
            return self.textures.get(name) 

        assert_that((path != None), "Give the path to the texture").is_true() 
        assert_that((format == wgpu.TextureFormat.rgba8unorm) or (format == wgpu.TextureFormat.rgba16float)).is_true()

        img = Image.open(path) 
        img_bytes = img.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

        width = img.width 
        height = img.height 
        size = [width, height, 1] 

        texture: wgpu.GPUTexture = GpuController().device.create_texture(
            size=size,
            usage = wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.RENDER_ATTACHMENT,
            dimension = wgpu.TextureDimension.d2,
            format = format,
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
        """
        Creates and stores a skybox texture from multiple image files.

        :param name: Name of the skybox.
        :param paths: List of paths to the image files.
        """
        
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

    def get_texture(self, name:str) -> Texture:
        """
        Retrieves a texture by name.

        :param name: Name of the texture.
        :return: Texture object.
        """

        return self.textures.get(name)
             
    def get_skybox(self, name:str) -> Texture:
        """
        Retrieves a skybox by name.

        :param name: Name of the skybox.
        :return: Texture object.
        """

        return self.skyBoxes.get(name) 
    
    def append_texture(self, name:str, texture:Texture) -> None:
        """
        Adds a texture to the library.

        :param name: Name of the texture.
        :param texture: Texture object to add.
        """
        
        self.textures.update({name: texture})  

    def create_noise_texture(self, name:str, config): 
        ''' 
        Creating a Rg32Float noise texture and store it in the texture library
        CAUSION: no sampler will be created as the noise texure can
        be used in multiple senarios

        config stracture:

        config = {

            "width": int,\n
            "height": int,\n
            "depth_or_array_layers": int,\n
        }

        texture_format Rg32float
        '''

        # Generate random noise data
        noise_data = np.random.uniform(-1.0, 1.0, (config["height"], config["width"], 2)).astype(np.float32)
        noise_data = noise_data.tobytes()  # Convert to bytes

        # Calculate bytes per row
        bytes_per_row = config["width"] * 2 * np.dtype(np.float32).itemsize

        # Create the texture
        texture: wgpu.GPUTexture = GpuController().device.create_texture(
            size=[config["width"], config["height"], config["depth_or_array_layers"]],
            dimension=wgpu.TextureDimension.d2,
            format=wgpu.TextureFormat.rg32float,
            usage=wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING,
        ) 
        texture_view = texture.create_view()

        # Write the noise data to the texture 
        GpuController().device.queue.write_texture(
            {
                "texture": texture,
                "mip_level": 0,
                "origin": (0, 0, 0)
            },
            noise_data,
            {
                "offset": 0,
                "bytes_per_row": bytes_per_row,
                "rows_per_image": config["height"],
            },
            [config["width"], config["height"], config["depth_or_array_layers"]],
        )

        self.textures.update({name: Texture(texture, texture_view, None, None, config["width"], config["height"], config["depth_or_array_layers"])})

        