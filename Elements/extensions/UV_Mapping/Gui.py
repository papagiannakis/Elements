'''
    @Authors: MANOS DIMITRIS csd5188, STAUROS MANESIS csd5266
    @Date: December 2025
    @Description:
   
'''
import Elements.pyECSS.math_utilities as util
from Elements.extensions.UV_Mapping.ObjectGenerator import UVObjectGenerator
import OpenGL.GL as gl





class UVGui:
    def __init__(self):
        #======== Transform controls ========
        self.pos = [0.0, 0.0, 0.0]

        # UV Offset  
        self.offset_u = 0.0
        self.offset_v = 0.0

        # UV Scale 
        self.scale_u = 1.0
        self.scale_v = 1.0

        # UV flip. 
        self.flip_u = False
        self.flip_v = False

        self.projection = 0  # 0 = Sphere, 1 = Cylinder
        self.manual_override = False  
        self.locked_projection = None
        
        # Visualization controls
        self.show_projection_guide = False
        self.projection_guide = None
        self.show_sphere_gizmo = False
        self.sphere_gizmo = None
        self.original_normals = None
       
        self.objects = {}
        self.current_object_name = None
 
    def draw(self, imgui, obj_trans, vertices, mesh, varray=None):
        imgui.begin("UV Projection Inspector")

        # --- Object picker ---
        if self.objects:
            names = list(self.objects.keys())
            if self.current_object_name not in names:
                self.current_object_name = names[0]

            try:
                current_idx = names.index(self.current_object_name)
            except ValueError:
                current_idx = 0

        
            combo_a, combo_b = imgui.combo("Object", current_idx, names)
            
            if isinstance(combo_a, bool) and isinstance(combo_b, int):
                changed_idx, new_idx = combo_a, combo_b
            elif isinstance(combo_a, int) and isinstance(combo_b, bool):
                changed_idx, new_idx = combo_b, combo_a
            else:
                changed_idx, new_idx = combo_a, combo_b

            if changed_idx:

                if 0 <= new_idx < len(names):
                    self.current_object_name = names[new_idx]
                else:
                    self.current_object_name = names[0]
                sel = self.objects[self.current_object_name]
                
                
                if 'trans' in sel and sel['trans'] is not None:
                    try:
                        obj_trans.trs = sel['trans'].trs if hasattr(sel['trans'], 'trs') else sel['trans']
                    except Exception:
                        obj_trans.trs = sel['trans']

                if 'vertices' in sel and sel['vertices'] is not None:
                    if len(mesh.vertex_attributes) > 0:
                        mesh.vertex_attributes[0] = sel['vertices']
                    else:
                        mesh.vertex_attributes.append(sel['vertices'])

                if 'normals' in sel and sel['normals'] is not None:
                    if len(mesh.vertex_attributes) > 1:
                        mesh.vertex_attributes[1] = sel['normals']
                    else:
                        
                        while len(mesh.vertex_attributes) < 1:
                            mesh.vertex_attributes.append([])
                        mesh.vertex_attributes.append(sel['normals'])

                if 'uvs' in sel and sel['uvs'] is not None:
                    if len(mesh.vertex_attributes) > 2:
                        mesh.vertex_attributes[2] = sel['uvs']
                    else:
                        while len(mesh.vertex_attributes) < 2:
                            mesh.vertex_attributes.append([])
                        mesh.vertex_attributes.append(sel['uvs'])

                if 'indices' in sel and sel['indices'] is not None:
                    
                    if hasattr(mesh, 'vertex_index') and len(mesh.vertex_index) > 0:
                        mesh.vertex_index[0] = sel['indices']
                    else:
                        mesh.vertex_index.append(sel['indices'])

            
                target_varray = varray if varray is not None else sel.get('varray', None)
                if target_varray is not None:
                    if getattr(target_varray, 'glid', None) is not None:
                        try:
                            gl.glDeleteVertexArrays(1, [target_varray.glid])
                        except Exception:
                            pass
                        try:
                            gl.glDeleteBuffers(len(target_varray._buffers), target_varray._buffers)
                        except Exception:
                            pass
                        target_varray._glid = None
                        target_varray._buffers = []
                    try:
                        target_varray.init()
                    except Exception:
                        pass

            imgui.separator()

        # THIS PART THE TRANSFORM
        imgui.text("Object Transform")
        changed, self.pos = imgui.drag_float3(
            "Position", *self.pos, 0.01
        )

        if changed:
            obj_trans.trs = util.translate(*self.pos)

        imgui.separator()

        #Selected Projection Type
        imgui.text("Projection Type")
        
        if not self.manual_override:
            if self.projection == 0:
                imgui.text(f"Object Automatically detected as type: 'Sphere'")
                self.locked_projection = 'Sphere'
            else:
                imgui.text(f"Object Automatically detected as type: 'Cylinder'")
                self.locked_projection = 'Cylinder'
        else:
            # Manual override: show locked type
            imgui.text(f"Manually locked to: '{self.locked_projection}'")

        if imgui.radio_button("Sphere", self.projection == 0):
            self.manual_override = True  # User made manual selection
            self.projection = 0
            self.locked_projection = 'Sphere'
            select1 = True
        else:
            select1 = False
            
        if imgui.radio_button("Cylinder", self.projection == 1):
            self.manual_override = True  # User made manual selection
            self.projection = 1
            self.locked_projection = 'Cylinder'
            select2 = True
        else:
            select2 = False

        imgui.separator()

        #THIS PART THE OFFSET
        imgui.text("UV Offset (Move Texture)")
        changed_offset_u, self.offset_u = imgui.slider_float(
            "Offset U (Horizontal)", self.offset_u, -1.0, 1.0
        )
        changed_offset_v, self.offset_v = imgui.slider_float(
            "Offset V (Vertical)", self.offset_v, -1.0, 1.0
        )

        imgui.separator()

        #THIS PART THE SCALE
        imgui.text("UV Scale (Stretch Texture)")
        changed_scale_u, self.scale_u = imgui.slider_float(
            "Scale U", self.scale_u, 0.1, 5.0
        )
        changed_scale_v, self.scale_v = imgui.slider_float(
            "Scale V", self.scale_v, 0.1, 5.0
        )

        imgui.separator()

        #THIS PART THE FLIP
        imgui.text("UV Flip")
        changed_flip_u, self.flip_u = imgui.checkbox("Flip U", self.flip_u)
        changed_flip_v, self.flip_v = imgui.checkbox("Flip V", self.flip_v)

        if (select1 or select2 or changed_offset_u or changed_offset_v or 
            changed_scale_u or changed_scale_v or changed_flip_u or changed_flip_v):
            
            if self.projection == 0:
                uvs = UVObjectGenerator.ProjectUV_Sphere(
                    vertices,
                    offset_u=self.offset_u,
                    offset_v=self.offset_v,
                    scale_u=self.scale_u,
                    scale_v=self.scale_v,
                    flip_u=self.flip_u,
                    flip_v=self.flip_v
                )
            else:
                uvs = UVObjectGenerator.ProjectUV_Cylinder(
                    vertices,
                    offset_u=self.offset_u,
                    offset_v=self.offset_v,
                    scale_u=self.scale_u,
                    scale_v=self.scale_v,
                    flip_u=self.flip_u,
                    flip_v=self.flip_v
                )

            mesh.vertex_attributes[2] = uvs  # overwrite UVs
            
            # WE NEED TO DELETE THE OLD VARRAY TO INSERT THE NEW UVS INTO THE GPU AGAIN
            if varray is not None:
                if varray.glid is not None:
                    gl.glDeleteVertexArrays(1, [varray.glid])
                    gl.glDeleteBuffers(len(varray._buffers), varray._buffers)
                    varray._glid = None
                    varray._buffers = []
                varray.init()#iINIT THEM AND DONE!

        imgui.end()