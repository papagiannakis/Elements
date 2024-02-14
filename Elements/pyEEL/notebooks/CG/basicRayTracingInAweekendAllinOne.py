# File: basicRayTracingInAweekendAllinOne.py
# Author: Prof. George Papagiannakis
# Date: 2024
# Description: python conversion of the C++ code from the book "Ray Tracing in a Weekend" by Peter Shirley
# based on : https://raytracing.github.io/books/RayTracingInOneWeekend.html 
# and https://github.com/alfiopuglisi/raytrace_weekend_numpy
# a Python and numpy implementation of the ray tracing algorithm described in the book 
# "Ray Tracing in a Weekend" by Peter Shirley.

import time
import numpy as np
from PIL import Image
np.seterr(invalid='ignore')   # Do not warn about NaNs

class Vec3:
    """
    A class representing a 3D vector.

    Attributes:
        x (np.ndarray): The x-component of the vector.
        y (np.ndarray): The y-component of the vector.
        z (np.ndarray): The z-component of the vector.

    The x,y,z attributes in the Vec3 class are arrays instead of a single value
    This allowa the Vec3 class to represent a collection of 3D vectors, not just a single 3D vector. 
    This can be useful in many contexts, such as graphics programming or physics simulations, 
    where you often need to work with large collections of vectors at once.
    By storing x, y, and z as arrays, each instance of Vec3 can represent multiple vectors. 
    For example, the x array could hold the x-coordinates of all vectors, the y array could hold the y-coordinates, 
    and the z array could hold the z-coordinates. 
    This design can make it easier to perform operations on all vectors at once, 
    leveraging the power of NumPy's array operations for efficient computation.
    """

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x if type(x) == np.ndarray else np.array(x, dtype=np.float32)
        self.y = y if type(y) == np.ndarray else np.array(y, dtype=np.float32)
        self.z = z if type(z) == np.ndarray else np.array(z, dtype=np.float32)

    @staticmethod
    def empty(size):
        x = np.empty(size, dtype=np.float32)
        y = np.empty(size, dtype=np.float32)
        z = np.empty(size, dtype=np.float32)
        return Vec3(x,y,z)

    @staticmethod
    def zeros(size):
        x = np.zeros(size, dtype=np.float32)
        y = np.zeros(size, dtype=np.float32)
        z = np.zeros(size, dtype=np.float32)
        return Vec3(x,y,z)

    @staticmethod
    def ones(size):
        x = np.ones(size, dtype=np.float32)
        y = np.ones(size, dtype=np.float32)
        z = np.ones(size, dtype=np.float32)
        return Vec3(x,y,z)
    
    @staticmethod
    def where(condition, v1, v2):
        x = np.where(condition, v1.x, v2.x)
        y = np.where(condition, v1.y, v2.y)
        z = np.where(condition, v1.z, v2.z)
        return Vec3(x,y,z)
    
    def clip(self, vmin, vmax):
        x = np.clip(self.x, vmin, vmax)
        y = np.clip(self.y, vmin, vmax)
        z = np.clip(self.z, vmin, vmax)
        return Vec3(x,y,z)

    def fill(self, value):
        self.x.fill(value)
        self.y.fill(value)
        self.z.fill(value)

    def repeat(self, n):
        x = np.repeat(self.x, n)
        y = np.repeat(self.y, n)
        z = np.repeat(self.z, n)
        return Vec3(x,y,z)
    
    def __str__(self):
        return 'vec3: x:%s y:%s z:%s' % (str(self.x), str(self.y), str(self.z))
    
    def __len__(self):
        return self.x.size

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, scalar):
        return Vec3(self.x*scalar, self.y*scalar, self.z*scalar)

    def multiply(self, other):
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)

    def __truediv__(self, scalar):
        return Vec3(self.x/scalar, self.y/scalar, self.z/scalar)
    
    def tile(self, shape):
        '''Replicate np.tile on each component'''
        return Vec3(np.tile(self.x, shape), np.tile(self.y, shape), np.tile(self.z, shape))

    def __getitem__(self, idx):
        '''Extract a vector subset'''
        return Vec3(self.x[idx], self.y[idx], self.z[idx])
    
    def __setitem__(self, idx, other):
        '''Set a vector subset from another vector'''
        self.x[idx] = other.x
        self.y[idx] = other.y
        self.z[idx] = other.z

    def join(self):
        '''Join the three components into a single 3xN array'''
        return np.vstack((self.x, self.y, self.z))
    
    def append(self, other):
        '''Append another vector to this one.
        Use concatenate() because cupy has no append function.
        '''
        self.x = np.concatenate((self.x, other.x))
        self.y = np.concatenate((self.y, other.y))
        self.z = np.concatenate((self.z, other.z))
        

## Aliases
Point3 = Vec3
Color = Vec3

## Utility functions
def unit_vector(v):
    return v / length(v)

def dot(a, b):
    return a.x*b.x + a.y*b.y + a.z*b.z

def length(v):
    return length_squared(v)**0.5

def length_squared(v):
    return v.x*v.x + v.y*v.y + v.z*v.z

def cross(a, b):
    return Vec3(a.y*b.z - a.z*b.y,
                -(a.x*b.z - a.z*b.x),
                a.x*b.y - a.y*b.x)


def convert_to_pil(v, width, height, scale = 255.999):
    """
    Converts a numpy array to a PIL image.

    Parameters:
    v (numpy.ndarray): The input array.
    width (int): The width of the image.
    height (int): The height of the image.
    scale (float, optional): The scaling factor. Defaults to 255.999.

    Returns:
    PIL.Image.Image: The converted PIL image.
    """
    # joins the three components (presumably representing RGB color channels) into a single 3xN array. 
    # This array is then multiplied by scale, which could be a scalar or another array used to adjust 
    # the intensity of the colors. The result is then converted to 8-bit unsigned integer format using astype(np.uint8). 
    img = (v.join() * scale).astype(np.uint8)

    # The resulting 3xN array is then reshaped into a 2D array with dimensions (height, width, 3).
    # This is done using the swapaxes(0,1) method, which swaps the first and second axes of the array,
    # and the reshape method, which reshapes the array into the specified dimensions.
    if len(img.shape) == 2:
        img_rgb = img.swapaxes(0,1).reshape(height, width, 3)
    else:
        img_rgb = img.reshape(height, width)

    return Image.fromarray(img_rgb)
    
""""
The Ray class is used to represent a ray in 3D space.
"""
class Ray:
    def __init__(self, origin, direction):
        """
        Initialize a Ray object.

        Parameters:
        - origin: The origin point of the ray.
        - direction: The direction vector of the ray.
        """
        self.origin = origin
        self.direction = direction
        self._direction_length_squared = None

    def at(self, t):
        """
        Calculate the point on the ray at a given parameter t.

        Parameters:
        - t: The parameter value.

        Returns:
        - The point on the ray at parameter t.
        """
        return self.origin + self.direction*t
    
    def __getitem__(self, idx):
        """
        Get a sub-ray by indexing the origin and direction vectors.

        Parameters:
        - idx: The index value.

        Returns:
        - A sub-ray with origin and direction vectors indexed by idx.
        """
        return Ray(self.origin[idx], self.direction[idx])

    def __setitem__(self, idx, other):
        """
        Set the origin and direction vectors of a sub-ray by indexing.

        Parameters:
        - idx: The index value.
        - other: Another Ray object.

        Returns:
        - None
        """
        self.origin[idx] = other.origin
        self.direction[idx] = other.direction
        self._direction_length_squared = None
    
    def __len__(self):
        """
        Get the length of the ray.

        Returns:
        - The length of the ray.
        """
        return self.origin.x.size

    def direction_length_squared(self):
        """
        Calculate the squared length of the direction vector.

        Returns:
        - The squared length of the direction vector.
        """
        if self._direction_length_squared is None:
            self._direction_length_squared = length_squared(self.direction)
        return self._direction_length_squared


class Timer:
    """
    A context manager for measuring elapsed time.

    Usage:
    with Timer():
        # Code to be timed

    The elapsed time will be printed when the context is exited.
    """

    def __enter__(self):
        self.t0 = time.time()

    def __exit__(self, *args):
        t1 = time.time()
        print('Elapsed time: %.3f s' % (t1 - self.t0))


def my_random(low, high, size) -> np.ndarray:
    """
    Generate random numbers between `low` and `high`.

    Parameters:
    low (float): The lower bound of the random numbers.
    high (float): The upper bound of the random numbers.
    size (int): The number of random numbers to generate.

    Returns:
    numpy.ndarray: An array of random numbers between `low` and `high`.
    """
    return np.random.uniform(low, high, size).astype(np.float32)


def random_in_unit_sphere(n) -> np.ndarray:
    '''Generate random Vec3 arrays in batches and keep the ones inside the unit sphere
    
    Args:
        n (int): The number of random Vec3 arrays to generate
        
    Returns:
        numpy.ndarray: An array of random Vec3 arrays that are inside the unit sphere
    '''

    values = Vec3.zeros(0)

    while len(values) < n:
        random_values = Vec3(my_random(-1.0, 1.0, n), my_random(-1.0, 1.0, n), my_random(-1.0, 1.0, n))
        good_ones = length_squared(random_values) < 1
        values.append(random_values[good_ones])
        
    return values[np.arange(n)]


def random_unit_vectors(n):
    """
    Generate random unit vectors in 3D space.

    Parameters:
    n (int): Number of random unit vectors to generate.

    Returns:
    list: List of random unit vectors in 3D space.
    """
    a = my_random(0.0, 2.0*np.pi, n)
    z = my_random(-1.0, 1.0, n)
    r = np.sqrt(1 - z*z)
    return Vec3(r*np.cos(a), r*np.sin(a), z)


def random_in_unit_disk(n):
    '''Generate random Vec3 arrays in batches and keep the ones inside the unit disk.

    Args:
        n (int): The number of random Vec3 arrays to generate.

    Returns:
        Vec3: A Vec3 array containing the randomly generated arrays inside the unit disk.
    '''

    values = Vec3.zeros(0)

    while len(values) < n:
        random_values = Vec3(my_random(-1.0, 1.0, n), my_random(-1.0, 1.0, n), np.zeros(n))
        good_ones = length_squared(random_values) < 1
        values.append(random_values[good_ones])
    
    return values[:n]

   
def render_image(width, height):
    """
    Renders an image using ray tracing technique.

    Args:
        width (int): The width of the image in pixels.
        height (int): The height of the image in pixels.

    Returns:
        numpy.ndarray: The rendered image as a numpy array.
    """

    print('%dx%d pixels, %d samples per pixel' % (width, height, samples_per_pixel))

    """
    This is a context manager class used for measuring the time taken by a block of code. 
    It uses Python's time module to get the current time at the start and end of the context, 
    and then prints the elapsed time.
    """
    with Timer():
        """"
        uses numpy's mgrid function to generate a coordinate grid. mgrid returns 
        a dense multi-dimensional "meshgrid" which is a grid with coordinates specified 
        by the input arrays. Here, it's creating a 2D grid of indices for the image pixels, 
        with dimensions specified by the height and width of the image. 
        The float function is used to convert the height and width to floating point numbers, 
        which is necessary for the division operation that follows.
        - The 'ii' variable is a numpy ndarray representing the y-coordinates of the grid, 
        which range from 0 to height-1. It's used later in the code to calculate the v variable, 
        which represents the normalized y-coordinates of each pixel in the image. 
        - The 'jj' variable is a numpy ndarray representing the x-coordinates of the grid, used
        to calculate the u variable, which represents the normalized x-coordinates of each pixel.
        """
        ii, jj = np.mgrid[:float(height), :float(width)]

        """"
        The u and v variables are used to calculate the ray directions for each pixel in the image. 
        These coordinates are normalized to the range [0, 1] by dividing by width-1 and height-1, 
        respectively. The flatten method is used to convert the 2D arrays to 1D arrays, 
        and astype(np.float32) is used to ensure that the arrays are of type float32.
        """
        u = (jj/(width-1)).flatten().astype(np.float32)
        v = (ii/(height-1)).flatten().astype(np.float32)

        cam = get_camera()

        """"
        Creates a new Vec3 object with all its components (x, y, z) set to zero. 
        The size of each component is specified by width * height, which is likely the 
        total number of pixels in an image (given the context of the code).
        The Vec3.zeros method is a custom method defined in the Vec3 class. 
        This method creates three numpy arrays of zeros with the specified size and type np.float32, 
        and returns a new Vec3 object with these arrays as its x, y, and z components.
        This Vec3 object, img, could be used to store the color of each pixel in an image, 
        with the x, y, and z components representing the red, green, and blue color channels, respectively. 
        Initially, all the colors are set to zero, which corresponds to black in the RGB color model.
        """
        img = Vec3.zeros(width * height)

        """"
        The for loop iterates over each pixel in the image, and prints the pixel number
        and the total number of pixels in the image.
         
        's' is the loop variable, and it takes on each value in the sequence one by one. 
        In the context of ray tracing, samples_per_pixel is the number of rays 
        that are being cast through each pixel in the image, and s is the current sample number.
        This technique of casting multiple rays through each pixel is used to achieve effects 
        like antialiasing and depth of field.
        """
        for s in range(samples_per_pixel):
            print('Starting sample %d of %d' % ((s+1), samples_per_pixel))

            # Add a random offset to the ray origin to avoid artifacts
            # caused by hitting the origin of the sphere
            # typical antialiasing technique.
            # my_random(0.0, 1.0, u.size) calls the my_random function, 
            # which generates an array of random numbers between 0.0 and 1.0. 
            # The generated random numbers are then divided by width - 1 to normalize them to the range 
            # [0, 1/(width-1)]. This is done because the x-coordinates u are also normalized to the range [0, 1].
            # The normalized random numbers are added to the x-coordinates u. This effectively shifts the 
            # x-coordinates by a random amount, adding some randomness to the rays that are being cast.
            uu = u + my_random(0.0, 1.0, u.size) / (width - 1)
            vv = v + my_random(0.0, 1.0, v.size) / (height - 1)

            # calling the get_ray method of the cam object, which is an instance of a Camera class. 
            # The get_ray method is used to generate a ray from the camera through a point in the image plane, 
            # specified by the normalized coordinates uu and vv.
            r = cam.get_ray(uu,vv)

            # calling the ray_color function, which takes a Ray object as input and returns a Color object.
            # The Color object is then added to the img object, which is a Vec3 object.
            # The += operator is used to add the Color object to the Vec3 object.
            img += ray_color(r)

        # The img object is then divided by the number of samples per pixel to get the average color
        img *= 1.0 / samples_per_pixel
        # The sqrt function is applied to each component of the img object to gamma correct the image.
        img.x = np.sqrt(img.x)
        img.y = np.sqrt(img.y)
        img.z = np.sqrt(img.z)

        """"
        The clip method is used to ensure that the color values stay within a valid range. 
        In the context of an image, color values are often represented as floating-point numbers 
        between 0.0 and 1.0, where 0.0 represents no intensity and 1.0 represents full intensity. 
        By clipping the values to the range [0.0, 0.999], the code ensures that the color values stay 
        within this range, preventing any potential issues with colors that are too bright or too dark.
        """
        return img.clip(0.0, 0.999)


from collections import namedtuple
from abc import abstractmethod


class HitRecord:
    """"
    This class is used to store information about a ray-object intersection.
    The HitRecord class is used to store information about a ray-object intersection.
    It stores the following information:
    - The point of intersection p
    - The normal vector at the point of intersection normal
    - The t value of the ray at the point of intersection t
    - The index of the object that was hit index
    - The material of the object that was hit material
    if empty is True, it assigns True to all the arrays, otherwise it creates empty arrays
    """
    def __init__(self, n, empty=False):
        self.p           = empty or Vec3.empty(n)
        self.normal      = empty or Vec3.empty(n)
        self.front_face  = empty or np.empty(n, dtype=bool)
        self.t           = empty or np.full(n, np.inf, dtype=np.float32)
        self.center      = empty or Vec3.empty(n)
        self.radius      = empty or np.empty(n, dtype=np.float32)
        self.index       = empty or np.arange(n, dtype=np.int32)
        self.material_id = empty or np.zeros(n, dtype=np.int64)

    """"
    This method is used to access a subset of the hit records based on an index or a boolean mask.
    The __getitem__ method is a special method in Python that is used to implement object indexing or slicing. 
    In the context of the HitRecord class, it allows you to access a subset of the hit records in a convenient way, 
    similar to how you would access a subset of a list or an array. 
    For example, if hits is an instance of HitRecord, you can get the hit records where the t value is less than 1.0 
    with hits[hits.t < 1.0].
    """
    def __getitem__(self, idx):
        other = HitRecord(len(idx), empty=True)
        other.p           = self.p[idx]
        other.normal      = self.normal[idx]
        other.front_face = self.front_face[idx]
        other.t           = self.t[idx]
        other.center      = self.center[idx]
        other.radius      = self.radius[idx]
        other.index       = self.index[idx]
        other.material_id = self.material_id[idx]
        return other

""""
The Hittable class is an abstract base class that defines the interface for all hittable objects.
"""
class Hittable:
    """"
    This method is used to update the hit record with information about the closest intersection with the object.
    The update_hit_record method is used to update the hit record with information about the closest intersection
    with the object. It takes the following parameters:
    - rays: A Ray object or a list of Ray objects.
    - t_min: The minimum value of t.
    - t_max: The maximum value of t.
    - hit_record: A HitRecord object or a list of HitRecord objects.
    """
    @abstractmethod
    def update_hit_record(rays, t_min, t_max, hit_record: HitRecord):
        pass


""""
The Sphere class is a subclass of the Hittable class. It represents a sphere in 3D space.
"""
class Sphere(Hittable):
    '''A hittable sphere that knows how to update the hit record'''

    def __init__(self, center, radius, material):
        '''
        Initialize a Sphere object.

        Parameters:
        - center: The center coordinates of the sphere.
        - radius: The radius of the sphere.
        - material: The material of the sphere.

        '''
        self.center = center
        self.radius = radius
        self.material = material 

    def update_hit_record(self, rays, t_min, t_max, hit_record):
        '''
        Update the hit record for the given rays.

        Parameters:
        - rays: The rays to be checked for intersection with the sphere.
        - t_min: The minimum value of t for intersection.
        - t_max: The maximum value of t for intersection.
        - hit_record: The hit record to be updated.

        Returns:
        None
        '''
        
        # calculates the vector oc from the center of the sphere to the origin of the ray. 
        # This is done by subtracting the position vector of the sphere's center (self.center) 
        # from the position vector of the ray's origin (rays.origin).
        oc = rays.origin - self.center
        # calculates the a, b, and c coefficients of the quadratic equation for the ray-sphere intersection.
        a = rays.direction_length_squared()
        half_b = dot(oc, rays.direction)
        c = length_squared(oc) - self.radius*self.radius
        # calculates the discriminant of the quadratic equation.
        discriminant = half_b*half_b - a*c
        
        # calculates the roots of the quadratic equation.
        # The roots are calculated only if the discriminant is greater than or equal to zero,
        # which means that the ray intersects with the sphere.
        hits = np.where(discriminant >= 0)[0]

        # Early exit if our rays did not hit the sphere at all
        if len(hits) == 0:
            return

        # Only calculate roots on those rays that have hit
        half_b = half_b[hits]
        a = a[hits]
        
        # Calculate the roots
        # The discriminant is calculated only for the rays that have hit the sphere.
        # The np.sqrt function is used to calculate the square root of the discriminant.
        root = np.sqrt(discriminant[hits])
        t1 = (-half_b - root) / a
        t2 = (-half_b + root) / a
        
        # Update hit record where we are the closest
        t = np.where(t1 > t_min, t1, t2)
        # The np.where function is used to calculate the minimum value of t between t1 and t2,
        # and store it in the t variable. This is done because the minimum value of t is the closest intersection.
        closest = np.where((t < hit_record.t[hits]) & (t > t_min))
        
        # The hit record is updated with the closest intersection.
        # This line gets the index of the closest intersection from the hits array, 
        # which contains the indices of all intersections that were found. 
        idx = hits[closest]
        # The hit record is updated with the closest intersection.
        hit_record.t[idx] = t[closest]
        # This line updates the center field of the hit_record object at the index idx. 
        # The center field represents the center of the sphere that was hit.
        hit_record.center[idx] = self.center
        # This line updates the radius field of the hit_record object at the index idx. 
        # The radius field represents the radius of the sphere that was hit. 
        hit_record.radius[idx] = self.radius
        # updates the material_id field of the hit_record object at the index idx. 
        # The material_id field represents the ID of the material of the sphere that was hit.
        hit_record.material_id[idx] = id(self.material)


def calculate_normals(rays, hit_record):
    """
    Calculate the surface normal at the intersection point between a ray and a sphere.

    Parameters:
    rays (Ray): The ray object.
    hit_record (HitRecord): The hit record object containing information about the intersection.

    Returns:
    tuple: A tuple containing the intersection point (p), the surface normal (normal), 
    and a boolean indicating if the ray hit the front face of the sphere (front_face).
    """
    p = rays.at(hit_record.t)
    outward_normal = (p - hit_record.center) / hit_record.radius 
    front_face = dot(rays.direction, outward_normal) < 0 
    normal = Vec3.where(front_face, outward_normal, -outward_normal)
    
    return p, normal, front_face

""""
ScatterResult is a named tuple that has three fields: 'attenuation', 'rays', and 'is_scattered'.
We can create new ScatterResult objects like this: 
sr = ScatterResult(0.5, [ray1, ray2], True) 
and access the fields like this: 
sr.attenuation, sr.rays, sr.is_scattered
"""
ScatterResult = namedtuple('ScatterResult', 'attenuation rays is_scattered')


def reflect(v, n):
    """
    Reflects a vector `v` off a surface with normal vector `n`.

    Parameters:
    v (numpy.ndarray): The incident vector.
    n (numpy.ndarray): The surface normal vector.

    Returns:
    numpy.ndarray: The reflected vector.
    """
    return v - n*2*dot(v, n)


def refract(uv, n, etai_over_etat):
    """
    Compute the refraction of a ray given its incident direction, surface normal, and the ratio of refractive indices.
    
    Parameters:
    uv (numpy.ndarray): Incident direction of the ray.
    n (numpy.ndarray): Surface normal.
    etai_over_etat (float): Ratio of refractive indices.
    
    Returns:
    numpy.ndarray: Refracted direction of the ray.
    """
    cos_theta = dot(-uv, n)
    r_out_perp = (uv + n*cos_theta) * etai_over_etat
    r_out_parallel = n * (-np.sqrt(np.abs(1.0 - length_squared(r_out_perp))))
    return r_out_perp + r_out_parallel


def schlick(cosine, ref_idx):
    """
    Schlick approximation for the reflection coefficient.

    Args:
        cosine (float): The cosine of the angle between the incident ray and the surface normal.
        ref_idx (float): The refractive index of the material.

    Returns:
        float: The reflection coefficient.
    """
    r0 = (1 - ref_idx) / (1 + ref_idx)
    r0 = r0 * r0
    return r0 + (1 - r0) * (1 - cosine)**5



class Material:
    """A class representing a material in ray tracing."""
    
    def scatter(r_in: Ray, ray_idx, rec: HitRecord) -> ScatterResult:
        pass



class Lambertian(Material):
    """
    Lambertian material class for ray tracing.
    
    Args:
        albedo (Color): The albedo color of the material.
    """
    
    def __init__(self, albedo: Color):
        self.albedo = albedo
    
    def scatter(self, r_in: Ray, rec: HitRecord) -> ScatterResult:
        """
        Scatter the incoming ray off the material.
        
        Args:
            r_in (Ray): The incoming ray.
            rec (HitRecord): The hit record of the ray intersection.
        
        Returns:
            ScatterResult: The result of the scattering operation.
        """
        scatter_direction = rec.normal + random_unit_vectors(len(r_in))
        scattered = Ray(rec.p, scatter_direction)
        
        return ScatterResult(attenuation = self.albedo,
                             rays = scattered,
                             is_scattered = np.full(len(r_in), True, dtype=bool))


class Metal(Material):
    """
    Represents a metal material in ray tracing.
    
    Args:
        albedo (Color): The color of the metal.
        f (float): The fuzziness of the metal surface. Should be between 0 and 1.
        
    Attributes:
        albedo (Color): The color of the metal.
        fuzz (float): The fuzziness of the metal surface.
    """
    def __init__(self, albedo: Color, f):
        self.albedo = albedo
        self.fuzz = f if f < 1 else 1
        
    def scatter(self, r_in: Ray, rec: HitRecord) -> ScatterResult:
        """
        Calculates the scattered ray after a metal material interaction.
        
        Args:
            r_in (Ray): The incident ray.
            rec (HitRecord): The hit record containing information about the intersection point.
            
        Returns:
            ScatterResult: 
            The result of the scattering operation, including the scattered ray, attenuation, 
            and whether the ray is scattered or absorbed.
        """
        reflected = reflect(unit_vector(r_in.direction), rec.normal)
        scattered = Ray(rec.p, reflected + random_in_unit_sphere(len(r_in))*self.fuzz)

        return ScatterResult(attenuation = self.albedo,
                             rays = scattered,
                             is_scattered = dot(scattered.direction, rec.normal) > 0)


class Dielectric(Material):
    """
    Dielectric material class for ray tracing.
    
    Args:
        ref_idx (float): The refractive index of the material.
        
    Attributes:
        ref_idx (float): The refractive index of the material.
    """
    
    def __init__(self, ref_idx):
        self.ref_idx = ref_idx

    def scatter(self, r_in: Ray, rec: HitRecord) -> ScatterResult:
        """
        Scatter method for the dielectric material.
        
        Args:
            r_in (Ray): The incident ray.
            rec (HitRecord): The hit record containing information about the intersection.
            
        Returns:
            ScatterResult: The result of the scattering operation.
        """
        
        etai_over_etat = np.where(rec.front_face, 1.0 / self.ref_idx, self.ref_idx)
        
        unit_direction = unit_vector(r_in.direction)
        
        ## Reflection/refraction choice: calculate both and choose later
        cos_theta = np.fmin(dot(-unit_direction, rec.normal), 1.0)
        sin_theta = np.sqrt(1.0 - cos_theta*cos_theta)
        reflected = reflect(unit_direction, rec.normal)
        refracted = refract(unit_direction, rec.normal, etai_over_etat)

        reflected_rays = Ray(rec.p, reflected)
        refracted_rays = Ray(rec.p, refracted)

        reflect_prob = schlick(cos_theta, etai_over_etat)
        random_floats = my_random(0.0, 1.0, len(reflect_prob))

        must_reflect = (etai_over_etat * sin_theta > 1.0)
        again_reflect = (random_floats < reflect_prob)

        all_reflect = np.where(np.logical_or(must_reflect, again_reflect))
        
        refracted_rays[all_reflect] = reflected_rays[all_reflect]
        
        return ScatterResult(attenuation = Color(1.0, 1.0, 1.0),
                             rays = refracted_rays,
                             is_scattered = np.full(len(r_in), True, dtype=bool))


class Camera:
    """
    Represents a camera used for ray tracing.

    Args:
        lookfrom (Vec3): The position of the camera.
        lookat (Vec3): The point the camera is looking at.
        vup (Vec3): The up vector of the camera.
        vfov (float): The vertical field-of-view in degrees.
        aspect_ratio (float): The aspect ratio of the viewport.
        aperture (float): The aperture of the camera lens.
        focus_dist (float): The focal distance of the camera.

    Attributes:
        origin (Vec3): The origin of the camera.
        horizontal (Vec3): The horizontal vector of the viewport.
        vertical (Vec3): The vertical vector of the viewport.
        lower_left_corner (Vec3): The lower left corner of the viewport.
        lens_radius (float): The radius of the camera lens.
        u (Vec3): The u vector of the camera.
        v (Vec3): The v vector of the camera.
    """

    def __init__(self, lookfrom: Vec3,
                       lookat: Vec3,
                       vup: Vec3,
                       vfov: float,           # vertical field-of-view in degrees
                       aspect_ratio: float,
                       aperture: float,
                       focus_dist: float):

        theta = np.deg2rad(vfov)
        h = np.tan(theta/2)
        viewport_height = 2.0 * h;
        viewport_width = aspect_ratio * viewport_height;

        w = unit_vector(lookfrom - lookat)
        u = cross(vup, w)
        v = -cross(w, u)           # Minus here, to have things looking upright

        self.origin = lookfrom
        self.horizontal = u * viewport_width * focus_dist
        self.vertical = v * viewport_height * focus_dist
        self.lower_left_corner = self.origin - self.horizontal/2 - self.vertical/2 - w*focus_dist
        self.lens_radius = aperture / 2
        self.u = u
        self.v = v

    def get_ray(self, s, t):
        """
        Returns a ray from the camera origin to a specific point on the image plane.

        Parameters:
        - s: The horizontal coordinate of the point on the image plane (float)
        - t: The vertical coordinate of the point on the image plane (float)

        Returns:
        - ray: A Ray object representing the ray from the camera origin to the specified point on the image plane.
        """
        all_origins = self.origin.tile((s.size,))
        rd = random_in_unit_disk(s.size) * self.lens_radius
        offset = self.u * rd.x + self.v * rd.y

        return Ray(all_origins + offset, self.lower_left_corner
                                         + self.horizontal * s
                                         + self.vertical * t
                                         - all_origins - offset)
    

def ray_color(rays):
    '''Calculate the color of rays in a ray-tracing scene. Iterative version with materials
    Args:
        rays (array-like): The rays to calculate the color for.
    Returns:
        Color: The color of the rays.
    '''

    intensity = Vec3.ones(len(rays))
    all_rays = rays
    hit_record = HitRecord(len(rays))

    materials = set([x.material for x in world])

    for d in range(max_depth):

        print('Depth %d, %d rays' % (d, len(rays)))
        # Initialize all distances to infinite and propagate all rays
        hit_record.t.fill(np.inf)
        hit_record.material_id.fill(0)
        
        # Update the hit record with the closest intersection
        for hittable in world:
            hittable.update_hit_record(rays, 0.001, np.inf, hit_record)         
        
        # Calculate all hits normal and build a hit record for the scattering
        hits = np.where(hit_record.t != np.inf)[0]
        p, normal, front_face = calculate_normals(rays[hits], hit_record[hits])
        
        # Narrow down to the rays that have hit something
        material_rays = rays[hits]
        material_hit_record = hit_record[hits]
        material_hit_record.p = p
        material_hit_record.normal = normal
        material_hit_record.front_face = front_face
        
        # Scatter all rays
        # This is the main loop that iterates over all materials and scatters the rays that have hit something.
        # The material_rays and material_hit_record variables are used to store the rays and hit records
        for material in materials:
            # Find the rays that have hit this material
            material_hits = np.where(material_hit_record.material_id == id(material))[0]
            # Early exit if no rays have hit this material
            if len(material_hits) == 0:
                continue

            # Narrow down to this material and scatter
            my_rays = material_rays[material_hits]
            my_rec = material_hit_record[material_hits]
            result = material.scatter(my_rays, my_rec)         
            
            # All rays have done something
            all_rays[my_rec.index] = result.rays
            
            # Attenuation
            this_intensity = result.attenuation.multiply(intensity[my_rec.index])
            this_intensity[np.where(~result.is_scattered)] = Vec3(0,0,0)
            intensity[my_rec.index] = this_intensity

            # Those that have been scattered stop here
            not_scattered_material_idx = hits[material_hits[~result.is_scattered]]
            hit_record.t[not_scattered_material_idx] = np.inf
            
        # Iterate with those rays that have been scattered by something
        scattered_rays = np.where(hit_record.t != np.inf)[0]

        hit_record = hit_record[scattered_rays]
        rays = all_rays[hit_record.index]

        if len(rays) == 0:
            break
    # Calculate the background color        
    unit_direction = unit_vector(all_rays.direction)
    # The t variable is used to calculate the vertical coordinate of the image plane.
    t = 0.5 * unit_direction.y + 1.0
    # The background color is calculated using linear interpolation between white and blue.
    img = (Color(1.0, 1.0, 1.0) * (1 - t) + Color(0.5, 0.7, 1.0) * t).multiply(intensity)

    return img


def render(width, height):
    """
    Renders an image using ray tracing technique.

    Args:
        width (int): The width of the image.
        height (int): The height of the image.

    Returns:
        PIL.Image.Image: The rendered image.
    """
    colors = render_image(width, height)
    image = convert_to_pil(colors, width, height)
    return image


def random_double(low=0.0, high=1.0):
    """
    Generate a random floating-point number between the given low and high values.

    Args:
        low (float, optional): The lower bound of the random number range. Defaults to 0.0.
        high (float, optional): The upper bound of the random number range. Defaults to 1.0.

    Returns:
        float: A random floating-point number between low and high.
    """
    return np.random.uniform(low, high, 1).astype(np.float32)


def vec3_random(low=0.0, high=1.0):
    """
    Generate a random 3D vector with each component within the specified range.

    Args:
        low (float, optional): The lower bound of the range. Defaults to 0.0.
        high (float, optional): The upper bound of the range. Defaults to 1.0.

    Returns:
        Vec3: A random 3D vector.
    """
    r = my_random(low, high, size=3)
    return Vec3(r[0], r[1], r[2])

# The ground material is a Lambertian material with an albedo of 0.5.
ground_material = Lambertian(Color(0.5, 0.5, 0.5))

# The world is a list of hittable objects.
world = []
# The ground is a sphere with a radius of 1000.
world.append(Sphere(Point3(0, -1000, 0), 1000, ground_material))

# The world is populated with 22 randomly placed spheres.
# Each sphere has a random material, which is chosen based on a random number.
# The probability of choosing a Lambertian material is 0.8, the probability of choosing a metal material is 0.15,
# and the probability of choosing a glass material is 0.05.
# The Lambertian material has a random albedo, the metal material has a random albedo and fuzziness,
# and the glass material has a refractive index of 1.5.
# The spheres are placed in a grid of 20x20, with a spacing of 1.0 between each sphere.
# The spheres are placed in the range [-11, 11] in the x and z directions, and in the range [0, 10] in the y direction.
# The spheres are placed randomly in the y direction, with a maximum offset of 0.9.
# The spheres are placed only if the distance between the center of the sphere and the center of the world is greater than 0.9.
# This ensures that the spheres are not placed inside the ground sphere.
for a in range(-11, 11):
    for b in range(-11, 11):
        choose_mat = random_double()
        center = Point3(a + 0.9*random_double(), 0.2, b + 0.9*random_double())

        if length(center - Point3(4, 0.2, 0)) > 0.9:

            if choose_mat < 0.8:
                ## diffuse
                albedo = vec3_random().multiply(vec3_random())
                sphere_material = Lambertian(albedo)
                world.append(Sphere(center, 0.2, sphere_material))

            elif choose_mat < 0.95:
                ## metal
                albedo = vec3_random(0.5, 1)
                fuzz = random_double(0, 0.5)
                sphere_material = Metal(albedo, fuzz)
                world.append(Sphere(center, 0.2, sphere_material))

            else:
                ## glass
                sphere_material = Dielectric(1.5)
                world.append(Sphere(center, 0.2, sphere_material))

# The three large spheres are placed in the world.
# The first sphere is a Lambertian sphere with an albedo of 0.4.
# The second sphere is a Lambertian sphere with an albedo of 0.7.
# The third sphere is a metal sphere with an albedo of 0.6 and a fuzziness of 0.0.
# The spheres are placed at the following positions: (0, 1, 0), (-4, 1, 0), and (4, 1, 0).
# The spheres have a radius of 1.0.
# The spheres are placed in the world only if the distance between the center of the sphere 
# and the center of the world is greater than 1.0.
# This ensures that the spheres are not placed inside the ground sphere.
world.append(Sphere(Point3( 0, 1, 0), 1.0, Dielectric(1.5)))
world.append(Sphere(Point3(-4, 1, 0), 1.0, Lambertian(Color(0.4, 0.2, 0.1))))
world.append(Sphere(Point3( 4, 1, 0), 1.0, Metal(Color(0.7, 0.6, 0.5), 0.0)))

# The camera is placed at the following position: (13, 2, 3).
# The camera is looking at the origin of the world.
# The camera's up vector is (0, 1, 0).
# The camera's vertical field of view is 20 degrees.
# The camera's aspect ratio is 16/9.
# The camera's aperture is 0.1.
# The camera's focal distance is 10.0.
# The camera is created using the get_camera function.
image_width = 1200
aspect_ratio = 16/9
image_height = int(image_width / aspect_ratio)
samples_per_pixel = 10 #this affects greatly performance and quality
max_depth = 50

def get_camera():
    """
    Returns a Camera object with specified parameters.

    Parameters:
    - lookfrom (Point3): The position of the camera.
    - lookat (Point3): The point the camera is looking at.
    - vup (Vec3): The up direction of the camera.
    - vfov (float): The vertical field of view in degrees.
    - aspect_ratio (float): The aspect ratio of the image.
    - aperture (float): The aperture of the camera lens.
    - focus_dist (float): The focal distance of the camera.

    Returns:
    - Camera: A Camera object with the specified parameters.
    """
    lookfrom = Point3(13,2,3)
    lookat = Point3(0,0,0)
    
    return Camera(lookfrom = lookfrom,
                  lookat   = lookat,
                  vup      = Vec3(0,1,0),
                  vfov     = 20,
                  aspect_ratio = aspect_ratio,
                  aperture     = 0.1,
                  focus_dist   = 10.0)

# The render function is called to render the image.
img = render(image_width, image_height)
# The image is saved to a file named img.ppm.
img.save('RTinOneWeekendFinalimage.ppm')





















