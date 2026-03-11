#!/usr/bin/env python3
"""
Complete pipeline: Text → AI Manim code → Programmatic MP4 rendering.
Uses advanced Manim config for production-quality output.
"""

code_sample = """
from manim import *                                                                                                                                                                                                           
from scene import CScene                                                                                                                                                                                                      
import numpy as np                                                                                                                                                                                                            
                                                                                                                                                                                                                            
class GeneratedScene(CScene):                                                                                                                                                                                                 
    def construct(self):                                                                                                                                                                                                      
        # Beat 1: Show pentagon with vertex labels                                                                                                                                                                            
        title = self.setup_scene("Polygons")                                                                                                                                                                                  
                                                                                                                                                                                                                            
        # Pentagon vertices (centered)                                                                                                                                                                                        
        A = np.array([0, 1.5, 0])                                                                                                                                                                                             
        B = np.array([-1.2, 0.5, 0])                                                                                                                                                                                          
        C = np.array([-0.8, -1.2, 0])                                                                                                                                                                                         
        D = np.array([0.8, -1.2, 0])                                                                                                                                                                                          
        E = np.array([1.2, 0.5, 0])                                                                                                                                                                                           
                                                                                                                                                                                                                            
        pentagon = self.polygon(A, B, C, D, E)                                                                                                                                                                                
        shape_center = self.get_shape_center(A, B, C, D, E)                                                                                                                                                                   
                                                                                                                                                                                                                            
        # Label vertices                                                                                                                                                                                                      
        A_label = self.label_point(A, "A", shape_center)                                                                                                                                                                      
        B_label = self.label_point(B, "B", shape_center)                                                                                                                                                                      
        C_label = self.label_point(C, "C", shape_center)                                                                                                                                                                      
        D_label = self.label_point(D, "D", shape_center)                                                                                                                                                                      
        E_label = self.label_point(E, "E", shape_center)                                                                                                                                                                      
                                                                                                                                                                                                                            
        self.pause(0.5)                                                                                                                                                                                                       
                                                                                                                                                                                                                            
        # Beat 2: Highlight all sides (closed path)                                                                                                                                                                           
        # Create all sides with highlight color                                                                                                                                                                               
        AB = self.segment(A, B, color=YELLOW, stroke_width=6)                                                                                                                                                                 
        BC = self.segment(B, C, color=YELLOW, stroke_width=6)                                                                                                                                                                 
        CD = self.segment(C, D, color=YELLOW, stroke_width=6)                                                                                                                                                                 
        DE = self.segment(D, E, color=YELLOW, stroke_width=6)                                                                                                                                                                 
        EA = self.segment(E, A, color=YELLOW, stroke_width=6)                                                                                                                                                                 
                                                                                                                                                                                                                            
        self.pause(0.5)                                                                                                                                                                                                       
                                                                                                                                                                                                                            
        # Beat 3: Transform pentagon to triangle                                                                                                                                                                              
        # First fade vertex labels                                                                                                                                                                                            
        self.fade_out_group([A_label, B_label, C_label, D_label, E_label])                                                                                                                                                    
                                                                                                                                                                                                                            
        # Triangle vertices                                                                                                                                                                                                   
        T1 = np.array([-2, -1, 0])                                                                                                                                                                                            
        T2 = np.array([2, -1, 0])                                                                                                                                                                                             
        T3 = np.array([0, 2, 0])                                                                                                                                                                                              
                                                                                                                                                                                                                            
        triangle = self.transform_focus(                                                                                                                                                                                      
            pentagon,                                                                                                                                                                                                         
            self.polygon(T1, T2, T3),                                                                                                                                                                                         
            fade_out=[AB, BC, CD, DE, EA]                                                                                                                                                                                     
        )                                                                                                                                                                                                                     
                                                                                                                                                                                                                            
        triangle_center = self.get_shape_center(T1, T2, T3)                                                                                                                                                                   
        self.pause(0.5)                                                                                                                                                                                                       
                                                                                                                                                                                                                            
        # Beat 4: Label triangle as "3 sides"                                                                                                                                                                                 
        side_label = self.label_line(                                                                                                                                                                                         
            self.segment(T1, T2, color=WHITE),                                                                                                                                                                                
            "3 sides",                                                                                                                                                                                                        
            triangle_center                                                                                                                                                                                                   
        )                                                                                                                                                                                                                     
        side_label.shift(UP * 1.5)                                                                                                                                                                                            
        self.pause(0.5)                                                                                                                                                                                                       
                                                                                                                                                                                                                            
        # Beat 5: Transform triangle to hexagon                                                                                                                                                                               
        self.fade_out_group([side_label])                                                                                                                                                                                     
                                                                                                                                                                                                                            
        # Hexagon vertices (regular hexagon)                                                                                                                                                                                  
        H1 = np.array([-2, 0, 0])                                                                                                                                                                                             
        H2 = np.array([-1, 1.732, 0])                                                                                                                                                                                         
        H3 = np.array([1, 1.732, 0])                                                                                                                                                                                          
        H4 = np.array([2, 0, 0])                                                                                                                                                                                              
        H5 = np.array([1, -1.732, 0])                                                                                                                                                                                         
        H6 = np.array([-1, -1.732, 0])                                                                                                                                                                                        
                                                                                                                                                                                                                            
        hexagon = self.transform_focus(                                                                                                                                                                                       
            triangle,                                                                                                                                                                                                         
            self.polygon(H1, H2, H3, H4, H5, H6),                                                                                                                                                                             
            fade_out=[]                                                                                                                                                                                                       
        )                                                                                                                                                                                                                     
                                                                                                                                                                                                                            
        hexagon_center = self.get_shape_center(H1, H2, H3, H4, H5, H6)                                                                                                                                                        
        self.pause(0.5)                                                                                                                                                                                                       
                                                                                                                                                                                                                            
        # Beat 6: Label hexagon as "6 sides"                                                                                                                                                                                  
        hex_side_label = self.label_line(                                                                                                                                                                                     
            self.segment(H1, H2, color=WHITE),                                                                                                                                                                                
            "6 sides",                                                                                                                                                                                                        
            hexagon_center                                                                                                                                                                                                    
        )                                                                                                                                                                                                                     
        hex_side_label.shift(UP * 2.0)                                                                                                                                                                                        
        self.pause(1.0)   
"""

sample_slide_text = """
A polygon is a closed shape with straight sides
All sides connect end-to-end to form a single closed path
Polygons are named by how many sides they have
"""
import generate_animation

if __name__ == "__main__":
    
    generated_code = generate_animation.generate_animation(sample_slide_text)
    print(generated_code)
