class WavefrontObjectMesh:
    """
    Helper class to store information of a mesh contained in a Wavefront .obj file
    """
    def __init__(self, name: str)-> None:
        self.name = name
        self.material = ""
        self.faces = []