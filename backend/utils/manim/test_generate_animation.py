#!/usr/bin/env python3
"""
Complete pipeline: Text → AI Manim code → Programmatic MP4 rendering.
Uses advanced Manim config for production-quality output.
"""

code_sample = """
from scene import CScene
import numpy as np

class TrigonometryRatios(CScene):
    def construct(self):
        # Beat 1: Show right triangle with angle θ
        title = self.setup_scene("Trig Ratios")

        # Create right triangle vertices
        A = np.array([-2, -1, 0])  # Right angle vertex
        B = np.array([2, -1, 0])   # Bottom right
        C = np.array([2, 1, 0])    # Top right (acute angle θ at B)

        triangle = self.polygon(A, B, C)
        shape_center = self.get_shape_center(A, B, C)

        # Right angle at A
        right_mark = self.right_angle_mark(B, A, C, size=0.25, color=YELLOW)

        # Angle θ at B (acute angle)
        angle_theta = self.angle_mark(A, B, C, color=YELLOW, label="θ")

        # Labels for vertices
        A_label = self.label_point(A, "A", shape_center)
        B_label = self.label_point(B, "B", shape_center)
        C_label = self.label_point(C, "C", shape_center)

        self.pause(0.5)

        # Beat 2: Label sides
        # Opposite side to θ (AC)
        opp_line = self.segment(A, C, color=RED, stroke_width=6)
        opp_label = self.label_line(opp_line, "對", shape_center)

        # Adjacent side to θ (BC)
        adj_line = self.segment(B, C, color=GREEN, stroke_width=6)
        adj_label = self.label_line(adj_line, "鄰", shape_center)

        # Hypotenuse (AB)
        hyp_line = self.segment(A, B, color=ORANGE, stroke_width=6)
        hyp_label = self.label_line(hyp_line, "斜", shape_center)

        self.pause(0.5)

        # Beat 3: Show sin ratio
        sin_eq = self.mtex(r"\sin\theta = \frac{\text{對}}{\text{斜}}")
        sin_eq.to_corner(UR)
        self.play_steps(Write(sin_eq))
        self.pause(0.5)

        # Beat 4: Show cos ratio
        cos_eq = self.mtex(r"\cos\theta = \frac{\text{鄰}}{\text{斜}}")
        cos_eq.next_to(sin_eq, DOWN, buff=0.3)
        self.play_steps(Write(cos_eq))
        self.pause(0.5)

        # Beat 5: Show tan ratio
        tan_eq = self.mtex(r"\tan\theta = \frac{\text{對}}{\text{鄰}}")
        tan_eq.next_to(cos_eq, DOWN, buff=0.3)
        self.play_steps(Write(tan_eq))
        self.pause(0.5)

        # Beat 6: Fade helpers (prepare for transformation)
        self.fade_out_group([opp_label, adj_label, hyp_label, sin_eq, cos_eq, tan_eq])
        self.pause(0.5)

        # Beat 7: Transform to example triangle (3-4-5 triangle)
        # New triangle vertices for 3-4-5 triangle
        A2 = np.array([-2, -1, 0])  # Same right angle vertex
        B2 = np.array([2, -1, 0])   # Same bottom right
        C2 = np.array([2, 2, 0])    # New height for 3-4-5 (opposite=3, adjacent=4)

        # Transform main triangle
        new_triangle = self.transform_focus(
            triangle,
            self.polygon(A2, B2, C2),
            fade_out=[title, right_mark, angle_theta, A_label, B_label, C_label]
        )

        # New shape center
        shape_center2 = self.get_shape_center(A2, B2, C2)

        # New right angle
        new_right_mark = self.right_angle_mark(B2, A2, C2, size=0.25, color=YELLOW)

        # New angle θ
        new_angle_theta = self.angle_mark(A2, B2, C2, color=YELLOW, label="θ")

        self.pause(0.5)

        # Beat 8: Label sides with numbers
        # Opposite side = 3 (A2C2)
        opp_line2 = self.segment(A2, C2, color=RED, stroke_width=6)
        opp_label2 = self.label_line(opp_line2, "3", shape_center2)

        # Hypotenuse = 5 (A2B2)
        hyp_line2 = self.segment(A2, B2, color=ORANGE, stroke_width=6)
        hyp_label2 = self.label_line(hyp_line2, "5", shape_center2)

        self.pause(0.5)

        # Beat 9: Show Pythagorean theorem calculation
        pythagoras_eq = self.mtex(r"\text{鄰}^2 = 5^2 - 3^2 = 16")
        pythagoras_eq.to_corner(UL)
        self.play_steps(Write(pythagoras_eq))

        pythagoras_result = self.mtex(r"\text{鄰} = 4")
        pythagoras_result.next_to(pythagoras_eq, DOWN, buff=0.3)
        self.play_steps(Write(pythagoras_result))
        self.pause(0.5)

        # Beat 10: Label adjacent side = 4
        adj_line2 = self.segment(B2, C2, color=GREEN, stroke_width=6)
        adj_label2 = self.label_line(adj_line2, "4", shape_center2)
        self.pause(0.5)

        # Beat 11: Show cosθ = 4/5
        cos_calc = self.mtex(r"\cos\theta = \frac{4}{5}")
        cos_calc.next_to(pythagoras_result, DOWN, buff=0.5)
        self.play_steps(Write(cos_calc))
        self.pause(0.5)

        # Beat 12: Show tanθ = 3/4
        tan_calc = self.mtex(r"\tan\theta = \frac{3}{4}")
        tan_calc.next_to(cos_calc, DOWN, buff=0.3)
        self.play_steps(Write(tan_calc))
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
