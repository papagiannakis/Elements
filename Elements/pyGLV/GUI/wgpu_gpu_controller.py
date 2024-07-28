import wgpu
import glm
import numpy as np   
from enum import Enum
from assertpy import assert_that

class GpuController: 
    """
    Singleton class to manage GPU resources such as devices, adapters, uniform values and textures.
    """

    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print('Creating Gpu cache Singleton Object')
            cls._instance = super(GpuController, cls).__new__(cls) 

            cls.device: wgpu.GPUDevice = None 
            cls.adapter: wgpu.GPUAdapter = None

            cls.present_context = None
            cls.render_texture_format = None

            cls.render_target_size: list[int] = [640, 480]
            
        return cls._instance
    
    def __init__(self):
        None;  

    def set_adapter_device(self, adapter, device):
        """
        Set the adapter and device for the GPU.

        :param adapter: The GPU adapter.
        :param device: The GPU device.
        """        
        
        self.device = device
        self.adapter = adapter 

    def set_uniform_value(
        self, 
        shader_component,  
        buffer_name:str,
        member_name:str,
        uniform_value,  
        mat2x2f=False,
        mat4x4f=False, 
        mat3x3f=False,  
        float1=False,  
        float2=False,
        float3=False,  
        float4=False,
    ): 
        """
        Set the value of a uniform in a shader.

        :param shader_component: The shader component containing the uniform.
        :param buffer_name: The name of the buffer.
        :param member_name: The name of the uniform member.
        :param uniform_value: The value to set.
        :param mat2x2f: True if the value is a 2x2 matrix.
        :param mat4x4f: True if the value is a 4x4 matrix.
        :param mat3x3f: True if the value is a 3x3 matrix.
        :param float1: True if the value is a single float.
        :param float2: True if the value is a 2-component float vector.
        :param float3: True if the value is a 3-component float vector.
        :param float4: True if the value is a 4-component float vector.
        """

        data_size = 0
        value = None

        if mat4x4f is True: 
            data_size = 16 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32)
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true()

        elif mat3x3f is True: 
            data_size = 9 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32) 
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true()

        elif mat2x2f is True:  
            data_size = 4 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32) 
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true() 

        elif float4 is True: 
            data_size = 4 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32) 
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true()

        elif float3 is True: 
            data_size = 3 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32) 
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true() 

        elif float2 is True: 
            data_size = 2 * 4
            value = np.ascontiguousarray(uniform_value, dtype=np.float32) 
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true()

        elif float1 is True:  
            data_size = 4 
            value = np.float32(uniform_value)   
            print(f"value data size:{value.nbytes}, and data size should be {data_size}")
            assert_that((value.nbytes == data_size), f"value data size:{value.nbytes}, and data size should be {data_size}").is_true()

        else: 
            assert_that(data_size != 0).is_true()

        queue:wgpu.GPUQueue = self.device.queue; 
        queue.write_buffer(
            buffer=shader_component.uniform_gpu_buffers[buffer_name],
            buffer_offset=shader_component.uniform_buffers[buffer_name]['members'][member_name]['slot'],
            data=value,
            data_offset=0,
            size=data_size
        ) 

    def set_texture_sampler (
        self,
        shader_component,
        texture_name, 
        sampler_name,
        texture,
        texture_only=False,
        sampler_only=False
    ):  
        """
        Set the texture and sampler for a shader.

        :param shader_component: The shader component containing the texture and sampler.
        :param texture_name: The name of the texture.
        :param sampler_name: The name of the sampler.
        :param texture: The texture object.
        :param texture_only: True if only the texture should be set.
        :param sampler_only: True if only the sampler should be set.
        """        
        
        if texture_only is True:   
            assert_that(texture.view).is_not_none()
            shader_component.other_uniform[texture_name]['other_resource'] = texture.view 
        elif sampler_only is True:
            assert_that(texture.sampler).is_not_none()
            shader_component.other_uniform[sampler_name]['other_resource'] = texture.sampler
        else:
            assert_that(texture.view and texture.sampler).is_not_none()
            shader_component.other_uniform[texture_name]['other_resource'] = texture.view
            shader_component.other_uniform[sampler_name]['other_resource'] = texture.sampler