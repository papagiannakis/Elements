import wgpu
from PIL import Image

def load_image(path):
    img = Image.open(path) 
    data = img.convert("RGBA").tobytes("raw", "RGBA", 0, -1)
    width = int(img.width) 
    height = int(img.height) 

    return data, width, height

class TextureDescriptor:
    def __init__(
        self,  
        width:int = 1, 
        height:int = 1, 
        depthOrArrayLayers:int = 1, 
        format:any = wgpu.TextureFormat.rgba8unorm,
        usage:any = wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.RENDER_ATTACHMENT,
        sampleCount:int = 1, 
        mipLevelCount:int = 1,
        dimension:any = wgpu.TextureDimension.d2
    ):
        self.width = width  
        self.height = height 
        self.depthOrArrayLayers = depthOrArrayLayers
        self.format = format
        self.usage = usage
        self.sampleCount = sampleCount
        self.mipLevelCount = mipLevelCount
        self.dimension = dimension


class Texture:
    def __init__(self, device:wgpu.GPUDevice, label:str, textureDescriptor:TextureDescriptor=None, context=None, view=None): 
        self.descriptor = textureDescriptor
        self.context = any  
        self.view = view 
        self.device = device 
        self.label = label 
        self.context = context

    def init(self): 
        if self.context is None: 
            self.context = self.device.create_texture(
                label=self.label,
                size=[self.descriptor.width, self.descriptor.height, self.descriptor.depthOrArrayLayers],
                sample_count=self.descriptor.sampleCount,
                format=self.descriptor.format,
                usage=self.descriptor.usage,
                mip_level_count=self.descriptor.mipLevelCount,
                dimension=self.descriptor.dimension
            ) 

    def getView(self):
        if self.view is None:
            self.view = self.context.create_view() 
        return self.view 
    
    def writeTexture(self, data:any, width:int, height:int, bytesPerRow:int, depthOrArrayLater:int=1):
        self.device.queue.write_texture(
            {
                "texture": self.context,
            },
            data, 
            { 
                "bytes_per_row": bytesPerRow,
            }, 
            [width, height, depthOrArrayLater]
        )


class ImprotTexture(Texture): 
    def __init__(self, tag:str, path:str, desc: TextureDescriptor = None): 
        super().__init__(device=None, label=tag, textureDescriptor=desc)
        self.tag = tag
        self.path = path
        self.descriptor = desc 

    def make(self, device:wgpu.GPUDevice): 
        self.device = device;  

        if self.descriptor is None: 
            self.descriptor = TextureDescriptor() 

        self.data, self.width, self.height = load_image(self.path) 

        self.descriptor.width = self.width
        self.descriptor.height = self.height 

        self.init() 
        self.writeTexture(self.data, self.width, self.height, self.width * 4)