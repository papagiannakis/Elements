from __future__ import annotations
import wgpu 
import glm   
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_texture import TextureLib, Texture


FXAA_SHADER_CODE = """  
    struct Uniforms { 
        inverse_screen_size: vec2f
    };

    @group(0) @binding(0) var<uniform> ubuffer: Uniforms;
    @group(0) @binding(1) var screenTexture: texture_2d<f32>;
    @group(0) @binding(2) var screenSampler: sampler; 

    struct VertexOutput { 
        @builtin(position) Position: vec4<f32>,
        @location(0) uv: vec2<f32>
    }

    @vertex
    fn vs_main(
        @builtin(vertex_index) vertex_index: u32
    ) -> VertexOutput {  

        var POSITIONS = array<vec2<f32>, 6>(
            vec2<f32>(-1.0, -1.0), // bottom-left
            vec2<f32>( 1.0, -1.0), // bottom-right
            vec2<f32>(-1.0,  1.0), // top-left
            vec2<f32>(-1.0,  1.0), // top-left
            vec2<f32>( 1.0, -1.0), // bottom-right
            vec2<f32>( 1.0,  1.0)  // top-right
        );

        var UVS = array<vec2<f32>, 6>(
            vec2<f32>(0.0, 1.0), // bottom-left
            vec2<f32>(1.0, 1.0), // bottom-right
            vec2<f32>(0.0, 0.0), // top-left
            vec2<f32>(0.0, 0.0), // top-left
            vec2<f32>(1.0, 1.0), // bottom-right
            vec2<f32>(1.0, 0.0)  // top-right
        );

        var out: VertexOutput;
        let pos = POSITIONS[vertex_index];
        let vUV = UVS[vertex_index]; 

        out.uv = vUV;
        out.Position = vec4f(pos, 0.0, 1.0);
        return out;
    } 

    // FXAA settings
    const EDGE_THRESHOLD_MIN: f32 = 0.0312;
    const EDGE_THRESHOLD_MAX: f32 = 0.125;
    const ITERATIONS: i32 = 12;
    const SUBPIXEL_QUALITY: f32 = 0.75; 

    fn rgb2luma(color: vec3f) -> f32 {
        return sqrt(dot(color, vec3f(0.299, 0.587, 0.114)));
    }

    fn quality(q: f32) -> f32 {
        return select(1.0, select(1.5, select(2.0, select(4.0, 8.0, q > 10.0), q > 5.0 && q < 10.0), q == 5.0), q < 5.0);
    } 

    // Fragment shader
    @fragment
    fn fs_main(
        in: VertexOutput 
    ) -> @location(0) vec4f {   
        var uv = in.uv;
        var inverseScreenSize = ubuffer.inverse_screen_size;

        let colorCenter: vec3f = textureSample(screenTexture, screenSampler, uv).rgb;
        
        let lumaCenter: f32 = rgb2luma(colorCenter);

        let lumaDown: f32   = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i( 0,-1)).rgb);
        let lumaUp: f32     = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i( 0, 1)).rgb);
        let lumaLeft: f32   = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i(-1, 0)).rgb);
        let lumaRight: f32  = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i( 1, 0)).rgb);

        let lumaMin: f32 = min(lumaCenter, min(min(lumaDown, lumaUp), min(lumaLeft, lumaRight)));
        let lumaMax: f32 = max(lumaCenter, max(max(lumaDown, lumaUp), max(lumaLeft, lumaRight)));
        
        let lumaRange: f32 = lumaMax - lumaMin;
        
        if (lumaRange < max(EDGE_THRESHOLD_MIN, lumaMax * EDGE_THRESHOLD_MAX)) {
            return vec4f(colorCenter, 1.0);
        }

        let lumaDownLeft: f32   = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i(-1,-1)).rgb);
        let lumaUpRight: f32    = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i( 1, 1)).rgb);
        let lumaUpLeft: f32     = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i(-1, 1)).rgb);
        let lumaDownRight: f32  = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv, 0.0, vec2i( 1,-1)).rgb);

        let lumaDownUp: f32 = lumaDown + lumaUp;
        let lumaLeftRight: f32 = lumaLeft + lumaRight;

        let lumaLeftCorners: f32 = lumaDownLeft + lumaUpLeft;
        let lumaDownCorners: f32 = lumaDownLeft + lumaDownRight;
        let lumaRightCorners: f32 = lumaDownRight + lumaUpRight;
        let lumaUpCorners: f32 = lumaUpRight + lumaUpLeft;

        let edgeHorizontal: f32 = abs(-2.0 * lumaLeft + lumaLeftCorners) + abs(-2.0 * lumaCenter + lumaDownUp) * 2.0 + abs(-2.0 * lumaRight + lumaRightCorners);
        let edgeVertical: f32 = abs(-2.0 * lumaUp + lumaUpCorners) + abs(-2.0 * lumaCenter + lumaLeftRight) * 2.0 + abs(-2.0 * lumaDown + lumaDownCorners);

        let isHorizontal: bool = edgeHorizontal >= edgeVertical;

        var stepLength: f32 = select(inverseScreenSize.x, inverseScreenSize.y, isHorizontal);

        let luma1: f32 = select(lumaLeft, lumaDown, isHorizontal);
        let luma2: f32 = select(lumaRight, lumaUp, isHorizontal);
        let gradient1: f32 = luma1 - lumaCenter;
        let gradient2: f32 = luma2 - lumaCenter;

        let is1Steepest: bool = abs(gradient1) >= abs(gradient2);

        let gradientScaled: f32 = 0.25 * max(abs(gradient1), abs(gradient2));

        var lumaLocalAverage: f32 = 0.0;
        if (is1Steepest) {
            stepLength = -stepLength;
            lumaLocalAverage = 0.5 * (luma1 + lumaCenter);
        } else {
            lumaLocalAverage = 0.5 * (luma2 + lumaCenter);
        }

        var currentUv: vec2f = uv;
        if (isHorizontal) {
            currentUv.y += stepLength * 0.5;
        } else {
            currentUv.x += stepLength * 0.5;
        }

        let offset: vec2f = select(vec2f(inverseScreenSize.x, 0.0), vec2f(0.0, inverseScreenSize.y), isHorizontal);

        var uv1: vec2f = currentUv - offset * quality(0.0);
        var uv2: vec2f = currentUv + offset * quality(0.0);

        var lumaEnd1: f32 = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv1, 0.0).rgb);
        var lumaEnd2: f32 = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv2, 0.0).rgb);
        lumaEnd1 -= lumaLocalAverage;
        lumaEnd2 -= lumaLocalAverage;

        var reached1: bool = abs(lumaEnd1) >= gradientScaled;
        var reached2: bool = abs(lumaEnd2) >= gradientScaled;
        var reachedBoth: bool = reached1 && reached2;

        if (!reached1) {
            uv1 -= offset * quality(1.0);
        }
        if (!reached2) {
            uv2 += offset * quality(1.0);
        }

        if (!reachedBoth) {
            for (var i: i32 = 2; i < ITERATIONS; i++) {
                if (!reached1) {
                    lumaEnd1 = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv1, 0.0).rgb);
                    lumaEnd1 = lumaEnd1 - lumaLocalAverage;
                }
                if (!reached2) {
                    lumaEnd2 = rgb2luma(textureSampleLevel(screenTexture, screenSampler, uv2, 0.0).rgb);
                    lumaEnd2 = lumaEnd2 - lumaLocalAverage;
                }
                reached1 = abs(lumaEnd1) >= gradientScaled;
                reached2 = abs(lumaEnd2) >= gradientScaled;
                reachedBoth = reached1 && reached2;

                if (!reached1) {
                    uv1 -= offset * quality(1.0);
                }
                if (!reached2) {
                    uv2 += offset * quality(1.0);
                }

                if (reachedBoth) {
                    break;
                }
            }
        }

        let distance1: f32 = select(uv.x - uv1.x, uv.y - uv1.y, isHorizontal);
        let distance2: f32 = select(uv2.x - uv.x, uv2.y - uv.y, isHorizontal);

        let isDirection1: bool = distance1 < distance2;
        let distanceFinal: f32 = min(distance1, distance2);

        let edgeThickness: f32 = distance1 + distance2;

        let isLumaCenterSmaller: bool = lumaCenter < lumaLocalAverage;

        let correctVariation1: bool = (lumaEnd1 < 0.0) != isLumaCenterSmaller;
        let correctVariation2: bool = (lumaEnd2 < 0.0) != isLumaCenterSmaller;

        let correctVariation: bool = select(correctVariation2, correctVariation1, isDirection1);

        let pixelOffset: f32 = -distanceFinal / edgeThickness + 0.5;
        var finalOffset: f32 = select(0.0, pixelOffset, correctVariation);

        let lumaAverage: f32 = (1.0 / 12.0) * (2.0 * (lumaDownUp + lumaLeftRight) + lumaLeftCorners + lumaRightCorners);
        let subPixelOffset1: f32 = clamp(abs(lumaAverage - lumaCenter) / lumaRange, 0.0, 1.0);
        let subPixelOffset2: f32 = (-2.0 * subPixelOffset1 + 3.0) * subPixelOffset1 * subPixelOffset1;
        let subPixelOffsetFinal: f32 = subPixelOffset2 * subPixelOffset2 * SUBPIXEL_QUALITY;

        finalOffset = max(finalOffset, subPixelOffsetFinal);

        var finalUv: vec2f = uv;
        if (isHorizontal) {
            finalUv.y += finalOffset * stepLength;
        } else {
            finalUv.x += finalOffset * stepLength;
        }

        let finalColor: vec3f = textureSampleLevel(screenTexture, screenSampler, finalUv, 0.0).rgb;
        return vec4f(finalColor, 1.0);
    }
"""

class FXAAPass(RenderSystem): 

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        self.shader = GpuController().device.create_shader_module(code=FXAA_SHADER_CODE);  

        self.uniform_buffer: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=4 * 4, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        ) 
        
        bind_groups_layout_entries = [[]]   
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {"type": wgpu.BufferBindingType.uniform},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {"type": wgpu.SamplerBindingType.filtering},
            }
        ) 
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        mesh_gfx = TextureLib().get_texture(name="mesh_gfx") 
        inverse_width = 1 / mesh_gfx.width
        inverse_height = 1 / mesh_gfx.height
        inverse_render_resolution = glm.vec2(inverse_width, inverse_height)   
        inverse_render_resolution_data = np.ascontiguousarray(inverse_render_resolution, dtype=np.float32)  

        GpuController().device.queue.write_buffer(
            buffer=self.uniform_buffer,
            buffer_offset=0,
            data=inverse_render_resolution_data,
            data_offset=0,
            size=inverse_render_resolution_data.nbytes
        )

        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": self.uniform_buffer,
                    "offset": 0,
                    "size": self.uniform_buffer.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 1,
                "resource": mesh_gfx.view
            } 
        ) 

        bind_groups_entries[0].append(
            {
                "binding": 2, 
                "resource": mesh_gfx.sampler
            }
        )

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        self.bind_groups = bind_groups

        self.render_pipeline = GpuController().device.create_render_pipeline(
            layout=self.pipeline_layout,
            vertex={
                "module": self.shader,
                "entry_point": "vs_main", 
                "buffers": [], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil=None,            
            multisample=None,
            fragment={
                "module": self.shader,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba8unorm,
                        "blend": {
                            "alpha": (
                                wgpu.BlendFactor.one,
                                wgpu.BlendFactor.zero,
                                wgpu.BlendOperation.add,
                            ),
                            "color": (
                                wgpu.BlendFactor.one,
                                wgpu.BlendFactor.zero,
                                wgpu.BlendOperation.add,
                            ),
                        },
                    }
                ],
            },
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder):   
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw(6, 1, 0, 0) 

