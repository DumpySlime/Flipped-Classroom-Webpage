from manim import *
from scene import CScene
import numpy as np

class GeneratedScene(CScene):
    def construct(self):
        # Beat 1: Show title 'Polygons' and a simple closed shape
        title = self.setup_scene("Polygons")

        # Create irregular pentagon
        P1 = np.array([-2.5, -0.5, 0])
        P2 = np.array([-1, 1.5, 0])
        P3 = np.array([1.5, 1, 0])
        P4 = np.array([2, -1, 0])
        P5 = np.array([-1, -1.5, 0])
        pentagon = self.polygon(P1, P2, P3, P4, P5)
        shape_center = self.get_shape_center(P1, P2, P3, P4, P5)

        self.pause(0.5)

        # Beat 2: Highlight that all sides are straight
        # Create all sides with highlight color
        side1 = self.segment(P1, P2, color=YELLOW)
        side2 = self.segment(P2, P3, color=YELLOW)
        side3 = self.segment(P3, P4, color=YELLOW)
        side4 = self.segment(P4, P5, color=YELLOW)
        side5 = self.segment(P5, P1, color=YELLOW)

        # Sequential indication
        self.play_steps(Indicate(side1))
        self.play_steps(Indicate(side2))
        self.play_steps(Indicate(side3))
        self.play_steps(Indicate(side4))
        self.play_steps(Indicate(side5))

        self.pause(0.5)

        # Beat 3: Emphasize closed path by tracing perimeter
        # Create a moving dot to trace the perimeter
        trace_dot = Dot(color=YELLOW, radius=0.08)
        trace_path = VMobject(color=YELLOW, stroke_width=3)
        trace_path.set_points_as_corners([P1, P2, P3, P4, P5, P1])

        # Animate the dot along the path
        self.play_steps(Create(trace_dot))
        self.play_steps(MoveAlongPath(trace_dot, trace_path, run_time=2))
        self.play_steps(FadeOut(trace_dot))

        self.pause(0.5)

        # Beat 4: Fade title and transform to triangle
        self.fade_out_group([title, side1, side2, side3, side4, side5])

        # Define triangle vertices
        T1 = np.array([-2, -1, 0])
        T2 = np.array([2, -1, 0])
        T3 = np.array([0, 1.5, 0])

        # Transform pentagon to triangle
        triangle = self.transform_focus(
            pentagon,
            self.polygon(T1, T2, T3),
            fade_out=[]
        )
        triangle_center = self.get_shape_center(T1, T2, T3)

        self.pause(0.5)

        # Beat 5: Label triangle as '3 sides'
        side_label_tri = Text("3 sides", font_size=36, color=WHITE)
        side_label_tri.next_to(triangle, DOWN, buff=0.5)
        self.play_steps(Write(side_label_tri))

        self.pause(0.5)

        # Beat 6: Transform to square
        self.fade_out_group([side_label_tri])

        # Define square vertices
        S1 = np.array([-1.5, -1.5, 0])
        S2 = np.array([1.5, -1.5, 0])
        S3 = np.array([1.5, 1.5, 0])
        S4 = np.array([-1.5, 1.5, 0])

        square = self.transform_focus(
            triangle,
            self.polygon(S1, S2, S3, S4),
            fade_out=[]
        )
        square_center = self.get_shape_center(S1, S2, S3, S4)

        self.pause(0.5)

        # Beat 7: Label square as '4 sides'
        side_label_sq = Text("4 sides", font_size=36, color=WHITE)
        side_label_sq.next_to(square, DOWN, buff=0.5)
        self.play_steps(Write(side_label_sq))

        self.pause(0.5)

        # Beat 8: Transform to pentagon
        self.fade_out_group([side_label_sq])

        # Define regular pentagon vertices
        P1_new = np.array([0, 1.5, 0])
        P2_new = np.array([-1.2, 0.5, 0])
        P3_new = np.array([-0.8, -1.2, 0])
        P4_new = np.array([0.8, -1.2, 0])
        P5_new = np.array([1.2, 0.5, 0])

        pentagon_new = self.transform_focus(
            square,
            self.polygon(P1_new, P2_new, P3_new, P4_new, P5_new),
            fade_out=[]
        )
        pentagon_center = self.get_shape_center(P1_new, P2_new, P3_new, P4_new, P5_new)

        self.pause(0.5)

        # Beat 9: Label pentagon as '5 sides'
        side_label_pent = Text("5 sides", font_size=36, color=WHITE)
        side_label_pent.next_to(pentagon_new, DOWN, buff=0.5)
        self.play_steps(Write(side_label_pent))

        self.pause(0.5)

        # Beat 10: Fade all and show summary text
        self.fade_out_group([pentagon_new, side_label_pent])

        summary_text = Text("Named by number of sides", font_size=48, color=WHITE)
        self.play_steps(Write(summary_text))

        self.pause(1.0)