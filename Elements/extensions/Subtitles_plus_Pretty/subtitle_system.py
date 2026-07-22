# subtitle_system.py
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile

from Elements.pyGLV.GL.Textures import Texture
import Elements.pyECSS.math_utilities as util


class SubtitleManager:
    """
    Subtitle manager to show text 
    Use: subtitles = SubtitleManager()
        subtitles.add_subtitle("Welcome!", duration=3.0)
        subtitles.add_subtitle("This is cube", duration=2.5)
        
        # render loop:
        current_text = subtitles.update(delta_time)
    """
    
    def __init__(self):
        self.subtitle_queue = []  # list with(text, duration)
        self.current_subtitle = None  # current text
        self.current_duration = 0.0   # duration
        self.elapsed_time = 0.0       # time that has passed
        self.is_active = False        # Is the subtitle shown?
    
    def add_subtitle(self, text, duration=3.0):
        """
        Add subtitle in queue
        
        Args: text, duration
        """
        self.subtitle_queue.append((text, duration))
    
    def update(self, delta_time):
        """
        Udate in every frame
        
        Args: delta_time: time that has passed since the last frame
        
        Returns:
            str: null if the subtitle doesnt exist or the current text
        """
        #If the current is not active, take the next one from the queue
        if not self.is_active:
            if self.subtitle_queue:
                self.current_subtitle, self.current_duration = self.subtitle_queue.pop(0)
                self.elapsed_time = 0.0
                self.is_active = True
            else:
                return None
        
        #Update time for next frame
        self.elapsed_time += delta_time
        
        # If the time has passed, set to inactive
        if self.elapsed_time >= self.current_duration:
            self.is_active = False
            self.current_subtitle = None
            return None
        
        return self.current_subtitle
    
    def clear(self):
        """Clear all the subtitles"""
        self.subtitle_queue.clear()
        self.current_subtitle = None
        self.is_active = False
    
    def skip_current(self):
        """Skipp the current"""
        if self.is_active:
            self.is_active = False
            self.current_subtitle = None


class SubtitleRenderer:
    """
    Render the subtitles
    """
    
    def __init__(self, font_size=48, bg_color=(0, 0, 0, 180), 
                 text_color=(255, 255, 255, 255), padding=20):
        """
        Initialize the renderer
        Args:
            font_size: font size
            bg_color: background color rgba
            text_color: text color rgba
            padding
        """
        self.font_size = font_size
        self.bg_color = bg_color
        self.text_color = text_color
        self.padding = padding
        self.texture = None
        self.current_text = None
        
        # load font
        try:
            self.font = ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                self.font = ImageFont.truetype("Arial.ttf", self.font_size)
            except:
                self.font = ImageFont.load_default()
    
    def create_subtitle_texture(self, text, max_width=1200):
        """
        Create pillow
        
        Args:
            text, max_width
        
        Returns:
            Texture object
        """
        if not text:
            return None
        
        #if it is the same, keep the previous 
        if text == self.current_text and self.texture:
            return self.texture
        
        tmp = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(tmp)
        
        # split in lines if the text is long
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=self.font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width - 2 * self.padding:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        #Calculate the total size
        line_height = self.font_size + 10
        total_text = '\n'.join(lines)
        bbox = draw.textbbox((0, 0), total_text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = line_height * len(lines)
        
        img_width = text_width + 2 * self.padding
        img_height = text_height + 2 * self.padding
        
        # create image- textrue
        img = Image.new("RGBA", (img_width, img_height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        y_offset = self.padding
        for line in lines:
            draw.text((self.padding, y_offset), line, font=self.font, fill=self.text_color)
            y_offset += line_height
        
        # Save in a temporary file
        tmpdir = tempfile.gettempdir()
        path = os.path.join(tmpdir, f"subtitle_{abs(hash(text))}.png")
        img.save(path)
        
        # create and add to self the final texture
        self.texture = Texture(path)
        self.current_text = text
        
        return self.texture
    
    def get_screen_position(self, window_width, window_height, texture_width, texture_height):
        """
        Find the center to place the subtitle texture
        
        Returns:
            (x, y, width, height)
        """
        # Calc the ratio
        aspect = texture_width / texture_height
        
        #height set to 15% of screen (can be changed)
        screen_height = 0.15
        screen_width = screen_height * aspect * (window_height / window_width)
        
        # set bottom and center
        x = -screen_width / 2
        y = -0.85
        
        return (x, y, screen_width, screen_height)

# functions 
def render_subtitle_overlay(subtitle_text, renderer, window_width, window_height):
    """
    Render
    
    Args:
        subtitle_text,
        renderer: SubtitleRenderer instance
        window_width, window_height:
    """
    import OpenGL.GL as gl
    
    if not subtitle_text:
        return
    
    # Create texture
    texture = renderer.create_subtitle_texture(subtitle_text)
    if not texture:
        return
    
    pass