import wgpu
from PIL import Image


class wgpu_material:
    def __init__(self, device:wgpu.GPUDevice=None, filepath:str=None, bindGroupLayout:wgpu.GPUBindGroupLayout=None):
        
        self.loadTextureToGpu(device=device, filepath=filepath)

        self.view = self.context.create_view()
        self.sampler = device.create_sampler()

        self.bindGroup = device.create_bind_group(
            layout=bindGroupLayout,
            entries=[
                {
                    "binding": 0,
                    "resource": self.view
                },
                {
                    "binding": 1,
                    "resource": self.sampler
                }
            ]
        )


    def loadTextureToGpu(self, device:wgpu.GPUDevice, filepath:str):
        if filepath is not None:
            img = Image.open(filepath)
            img_bytes = img.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

        self.data = img_bytes;
        self.width = int(img.width) # Width
        self.height = int(img.height) # Height 
        self.size = [self.width, self.height, 1]

        self.context = device.create_texture(
            size=self.size,
            usage=wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.RENDER_ATTACHMENT,
            dimension=wgpu.TextureDimension.d2,
            format=wgpu.TextureFormat.rgba8unorm,
            mip_level_count=1,
            sample_count=1,
        )

        device.queue.write_texture(
            {
                "texture": self.context,
                "mip_level": 0,
                "origin": (0, 0, 0)
            },
            self.data,
            {
                "offset": 0,
                "bytes_per_row": self.width * 4,
                "rows_per_image": self.height
            },
            self.size
        )