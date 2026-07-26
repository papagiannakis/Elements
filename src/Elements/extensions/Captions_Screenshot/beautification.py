import numpy as np



def generateElegantFloor(size=4, center_color=[0.8, 0.8, 0.8, 1.0], edge_color=[0.2, 0.2, 0.2, 1.0]):
    """
    edw ftiaxnoume ena aplo tetragwno epipedo(quad), 
    i karta grafikwn den kserei "tetragwna", opote to ftiaxnoume me 2 trigwna(GL_TRIANGLES)
    orizoume 4 vertices: A, B, C ,D stis gwnies
    vazoume diaforetika xrwmata stis gwnies gia na kanei i OpenGL automata "interpolation"
    to xrhsimopoioume gia to Solid patwma

    """
    
    points = [
        [-size, 0.0, -size], 
        [size,  0.0, -size],
        [size,  0.0, size],  
        [-size, 0.0, size]  
    ]
    
    indices = [
        0, 1, 2, 
        0, 2, 3  
    ]

    colorT = [
        edge_color,   
        edge_color,   
        center_color,
        center_color  
    ]
    
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colorT, dtype=np.float32)


def generateSkybox(size=50.0):
    """
    ftiaxnoume enan terastio kyvo pou perivalei oli thn scene
    to megethos einai megalo gia na fainetai sa na einai makria o ouranos
    stis 4 panw korifes vazoume ble xrwma - ouranos
    stis 4 katw korifes vazoume gri xrwma - orizontas
    etsi dimiourgietai i aisthisi tou vathous kai tou ouranou xwris texture

    """
       
    points = [
        [-size, size, -size],  
        [size, size, -size], 
        [size, size, size], 
        [-size, size, size],   
        [-size, -size, -size], 
        [size, -size, -size],
        [size, -size, size], 
        [-size, -size, size]  
    ]
    
    sky_color = [0.0, 0.5, 1.0, 1.0]   
    horizon_color = [0.8, 0.8, 0.9, 1.0] 

    colors = [
        sky_color, sky_color, sky_color, sky_color,      
        horizon_color, horizon_color, horizon_color, horizon_color 
    ]
    
    indices = [
        0, 1, 2, 0, 2, 3, 
        4, 6, 5, 4, 7, 6, 
        0, 3, 7, 0, 7, 4, 
        1, 5, 6, 1, 6, 2, 
        3, 2, 6, 3, 6, 7, 
        0, 4, 5, 0, 5, 1  
    ]
    
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colors, dtype=np.float32)


def generateGrid(size=4, N=20, color=[0.2, 0.2, 0.2, 1.0]):
    """
    ftiaxnoume tis grammes pou bainei panw apo to patwma
    xrhsimopoioume GL_LINES anti gia trigwna gia na einai katheto
    to loop trexei N fores kai ftiaxnei zeugaria arxi-telos
    ftiaxnei mia orizontia kai mia katheti grammi se kathe vima

    """
    
    points = []
    indices = []
    colors = []
    
    # apostasi metaksi twn grammwn
    step = (2.0 * size) / N
    
    # ksekiname apo thn arxi
    current_pos = -size
    
    idx = 0
    
    for i in range(N + 1):
        points.append([current_pos, 0.0, -size]) 
        points.append([current_pos, 0.0, size])  
        points.append([-size, 0.0, current_pos]) 
        points.append([size, 0.0, current_pos])  
        indices.append(idx)
        indices.append(idx + 1)
        indices.append(idx + 2)
        indices.append(idx + 3)

        # prosthetoume to xrwma 4 fores , gia kathe vertex 
        colors.extend([color, color, color, color])
        
        idx += 4
        current_pos += step
        
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colors, dtype=np.float32)



if __name__ == "__main__":
    p, i, c = generateElegantFloor()
    print("Vertices:\n", p)
    print("Indices:\n", i)