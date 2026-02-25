from manim import *
from scene import CScene
import numpy as np

class GeneratedScene(CScene):
    def construct(self):
        # Beat 1: Setup scene with right triangle
        title = self.setup_scene("Trigonometric Ratios")

        # Define triangle vertices (right angle at A)
        A = np.array([-2, 0, 0])
        B = np.array([2, 0, 0])
        C = np.array([0, 2, 0])

        # Create triangle and right angle mark
        triangle = self.polygon(A, B, C)
        right_mark = self.right_angle_mark(B, A, C, size=0.25, color=YELLOW)

        # Label vertices
        shape_center = self.get_shape_center(A, B, C)
        A_label = self.label_point(A, "A", shape_center)
        B_label = self.label_point(B, "B", shape_center)
        C_label = self.label_point(C, "C", shape_center)

        self.pause(1.0)

        # Beat 2: Highlight opposite side to angle B (AC)
        opp_line = self.segment(A, C, color=BLUE, stroke_width=6)
        opp_label = self.label_line(opp_line, "opp", shape_center)
        self.play_steps(Indicate(opp_line))
        self.pause(1.0)

        # Beat 3: Highlight adjacent side to angle B (AB)
        adj_line = self.segment(A, B, color=GREEN, stroke_width=6)
        adj_label = self.label_line(adj_line, "adj", shape_center)
        self.play_steps(Indicate(adj_line))
        self.pause(1.0)

        # Beat 4: Highlight hypotenuse (BC)
        hyp_line = self.segment(B, C, color=RED, stroke_width=6)
        hyp_label = self.label_line(hyp_line, "hyp", shape_center)
        self.play_steps(Indicate(hyp_line))
        self.pause(1.0)

        # Beat 5: Fade title and show sine ratio
        self.fade_out_group([title])

        sin_eq = self.mtex(r"\sin \theta = \frac{\text{opp}}{\text{hyp}}")
        sin_eq.to_edge(UP)
        self.play_steps(Write(sin_eq))
        self.pause(1.0)

        # Beat 6: Transform to show cosine ratio
        # Fade old labels and equation
        self.fade_out_group([opp_label, hyp_label, sin_eq])

        # Show cosine equation
        cos_eq = self.mtex(r"\cos \theta = \frac{\text{adj}}{\text{hyp}}")
        cos_eq.to_edge(UP)
        self.play_steps(Write(cos_eq))
        self.pause(1.0)

        # Beat 7: Transform to show tangent ratio
        self.fade_out_group([adj_label, hyp_label, cos_eq])

        # Show tangent equation
        tan_eq = self.mtex(r"\tan \theta = \frac{\text{opp}}{\text{adj}}")
        tan_eq.to_edge(UP)
        self.play_steps(Write(tan_eq))
        self.pause(1.0)

        # Beat 8: Show SOH-CAH-TOA mnemonic
        self.fade_out_group([tan_eq])

        mnemonic = self.mtex(r"\text{SOH-CAH-TOA}")
        mnemonic.scale(1.5)
        self.play_steps(Write(mnemonic))
        self.pause(1.0)

        # Beat 9: Emphasize final result
        self.fade_out_group([mnemonic])

        # Show all three ratios together
        final_text = self.mtex(r"\sin = \frac{\text{opp}}{\text{hyp}},\quad \cos = \frac{\text{adj}}{\text{hyp}},\quad \tan = \frac{\text{opp}}{\text{adj}}")
        final_text.to_edge(DOWN)
        self.play_steps(Write(final_text))
        self.pause(2.0)