class WavefrontObjectFace:
    """
    Helper class to store triange face information retrieved from a wavefront .obj file
    """
    def __init__(self) -> None:
        self.vertex_indices = []
        self.normal_indices = []
        self.texture_coords_indices=[]

    def __str__(self):
        return "Face: vertex_indices:{} normal_indices:{} texture_indices:{}".format(self.vertex_indices , self.normal_indices, self.texture_coords_indices)