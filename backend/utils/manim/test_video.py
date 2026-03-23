from manim import *
from scene import CScene
import numpy as np

class GeneratedScene1(CScene):
    def construct(self):
        # Beat 1: Show right triangle with right angle at A
        title = self.setup_scene("直角三角形比例")
        
        A = np.array([-2, -1, 0])
        B = np.array([2, -1, 0])
        C = np.array([-2, 2, 0])
        triangle = self.polygon(A, B, C)

        shape_center = self.get_shape_center(A, B, C)
        A_label = self.label_point(A, "A", shape_center)
        B_label = self.label_point(B, "B", shape_center)
        C_label = self.label_point(C, "C", shape_center)
        right_mark = self.right_angle_mark(B, A, C, size=0.25, color=YELLOW)
        
        self.pause(0.5)
        
        # Beat 2: Label hypotenuse (BC)
        hyp_line = self.segment(B, C, color=RED, stroke_width=6)
        hyp_label = self.label_line(hyp_line, "斜邊", shape_center)
        
        self.pause(0.5)
        
        # Beat 3: Focus on angle B
        angle_B_mark = self.angle_mark(A, B, C, color=YELLOW, label="B")
        
        self.pause(0.5)
        
        # Beat 4: Label side opposite to angle B (AC)
        opp_line_B = self.segment(A, C, color=BLUE, stroke_width=6)
        opp_label_B = self.label_line(opp_line_B, "對邊", shape_center)
        
        self.pause(0.5)
        
        # Beat 5: Label side adjacent to angle B (AB)
        adj_line_B = self.segment(A, B, color=GREEN, stroke_width=6)
        adj_label_B = self.label_line(adj_line_B, "鄰邊", shape_center)
        
        self.pause(0.5)
        
        # Beat 6: Dim triangle and labels
        self.play_steps(
            triangle.animate.set_opacity(0.3),
            hyp_line.animate.set_opacity(0.3),
            opp_line_B.animate.set_opacity(0.3),
            adj_line_B.animate.set_opacity(0.3),
            hyp_label.animate.set_opacity(0.3),
            opp_label_B.animate.set_opacity(0.3),
            adj_label_B.animate.set_opacity(0.3),
            angle_B_mark.animate.set_opacity(0.3)
        )
        
        self.pause(0.5)
        
        # Beat 7: Transform to focus on angle C (fade old helpers, restore triangle)
        self.fade_out_group([hyp_label, opp_label_B, adj_label_B, angle_B_mark])
        
        # Restore triangle to full opacity
        new_triangle = self.transform_focus(
            triangle,
            self.polygon(A, B, C),
            fade_out=[]
        )
        self.play_steps(
            new_triangle.animate.set_opacity(1.0),
            hyp_line.animate.set_opacity(1.0),
            opp_line_B.animate.set_opacity(1.0),
            adj_line_B.animate.set_opacity(1.0)
        )
        
        self.pause(0.5)
        
        # Beat 8: Highlight angle C
        angle_C_mark = self.angle_mark(A, C, B, color=YELLOW, label="C")
        
        self.pause(0.5)
        
        # Beat 9: Label side opposite to angle C (AB)
        opp_line_C = self.segment(A, B, color=BLUE, stroke_width=6)
        opp_label_C = self.label_line(opp_line_C, "對邊", shape_center)
        
        self.pause(0.5)
        
        # Beat 10: Label side adjacent to angle C (AC)
        adj_line_C = self.segment(A, C, color=GREEN, stroke_width=6)
        adj_label_C = self.label_line(adj_line_C, "鄰邊", shape_center)
        
        self.pause(1.0)

class GeneratedScene2(CScene):
    def construct(self):
        # Beat 1: Show right triangle with angle θ labeled
        title = self.setup_scene("Trigonometric Ratios")

        # Define triangle vertices (right angle at A)
        A = np.array([-2, -1, 0])  # Right angle vertex
        B = np.array([2, -1, 0])   # Angle θ at B
        C = np.array([-2, 2, 0])   # Top vertex

        triangle = self.polygon(A, B, C)
        shape_center = self.get_shape_center(A, B, C)

        # Label vertices
        A_label = self.label_point(A, "A", shape_center)
        B_label = self.label_point(B, "B", shape_center)
        C_label = self.label_point(C, "C", shape_center)

        # Right angle mark at A
        right_mark = self.right_angle_mark(B, A, C, size=0.25, color=YELLOW)

        # Angle θ at B
        angle_theta = self.angle_mark(A, B, C, color=YELLOW, label=r"\theta")

        self.pause(0.5)

        # Beat 2: Highlight and label opposite side (AC)
        opp_line = self.segment(A, C, color=YELLOW, stroke_width=6)
        opp_label = self.label_line(opp_line, "Opp", shape_center)
        self.pause(0.5)

        # Beat 3: Highlight and label adjacent side (BA)
        adj_line = self.segment(B, A, color=YELLOW, stroke_width=6)
        adj_label = self.label_line(adj_line, "Adj", shape_center)
        self.pause(0.5)

        # Beat 4: Highlight and label hypotenuse (BC)
        hyp_line = self.segment(B, C, color=YELLOW, stroke_width=6)
        hyp_label = self.label_line(hyp_line, "Hyp", shape_center)
        self.pause(0.5)

        # Beat 5: Fade old labels, show sin ratio equation
        self.fade_out_group([opp_label, adj_label, hyp_label])

        # Dim triangle background
        self.play_steps(triangle.animate.set_opacity(0.3))

        sin_eq = self.mtex(r"\sin\theta = \frac{\text{Opp}}{\text{Hyp}}")
        sin_eq.to_corner(UR)
        self.play_steps(Write(sin_eq))
        self.pause(0.5)

        # Beat 6: Transform to cos ratio equation
        self.transform_focus(
            triangle,
            self.polygon(A, B, C),
            fade_out=[sin_eq]
        )

        cos_eq = self.mtex(r"\cos\theta = \frac{\text{Adj}}{\text{Hyp}}")
        cos_eq.to_corner(UR)
        self.play_steps(Write(cos_eq))
        self.pause(0.5)

        # Beat 7: Transform to tan ratio equation
        self.transform_focus(
            triangle,
            self.polygon(A, B, C),
            fade_out=[cos_eq]
        )

        tan_eq = self.mtex(r"\tan\theta = \frac{\text{Opp}}{\text{Adj}}")
        tan_eq.to_corner(UR)
        self.play_steps(Write(tan_eq))
        self.pause(0.5)

        # Beat 8: Fade triangle, show SOH-CAH-TOA mnemonic
        self.fade_out_group([triangle, A_label, B_label, C_label, right_mark, angle_theta])

        mnemonic = self.mtex(r"\text{SOH-CAH-TOA}")
        mnemonic.scale(1.5)
        self.play_steps(Write(mnemonic))
        self.pause(1.0)

class GeneratedScene3(CScene):
    def construct(self):
        # Beat 1: Show hexagon
        title = self.setup_scene("Polygons")
        
        # Hexagon vertices (regular hexagon centered at origin)
        hex_vertices = []
        for i in range(6):
            angle = i * np.pi / 3
            x = 2 * np.cos(angle)
            y = 2 * np.sin(angle)
            hex_vertices.append(np.array([x, y, 0]))
        
        hexagon = self.polygon(*hex_vertices)
        shape_center = self.get_shape_center(*hex_vertices)
        hex_label = self.label_point(ORIGIN, "Polygon", shape_center)
        self.pause(0.5)
        
        # Beat 2: Highlight first side and endpoints
        side_start = hex_vertices[0]
        side_end = hex_vertices[1]
        highlighted_side = self.segment(side_start, side_end, color=YELLOW, stroke_width=8)
        
        # Highlight endpoints
        start_dot = Dot(side_start, color=YELLOW, radius=0.08)
        end_dot = Dot(side_end, color=YELLOW, radius=0.08)
        self.play_steps(Create(start_dot), Create(end_dot))
        self.pause(0.5)
        
        # Beat 3: Trace perimeter
        trace_path = VMobject(color=GREEN, stroke_width=4)
        trace_path.set_points_as_corners(hex_vertices + [hex_vertices[0]])
        self.play_steps(Create(trace_path, run_time=2))
        self.pause(0.5)
        
        # Beat 4: Transform hexagon to triangle
        # First fade helpers
        self.fade_out_group([highlighted_side, start_dot, end_dot, trace_path, hex_label])
        
        # Triangle vertices
        A = np.array([-2, -1.5, 0])
        B = np.array([2, -1.5, 0])
        C = np.array([0, 1.5, 0])
        
        triangle = self.transform_focus(
            hexagon,
            self.polygon(A, B, C),
            fade_out=[]
        )
        self.pause(0.5)
        
        # Beat 5: Label triangle as "3 sides"
        tri_center = self.get_shape_center(A, B, C)
        tri_label = self.label_point(tri_center, "3 sides", tri_center)
        self.pause(0.5)
        
        # Beat 6: Transform triangle to square
        self.fade_out_group([tri_label])
        
        # Square vertices
        S1 = np.array([-1.5, -1.5, 0])
        S2 = np.array([1.5, -1.5, 0])
        S3 = np.array([1.5, 1.5, 0])
        S4 = np.array([-1.5, 1.5, 0])
        
        square = self.transform_focus(
            triangle,
            self.polygon(S1, S2, S3, S4),
            fade_out=[]
        )
        self.pause(0.5)
        
        # Beat 7: Label square as "4 sides"
        sq_center = self.get_shape_center(S1, S2, S3, S4)
        sq_label = self.label_point(sq_center, "4 sides", sq_center)
        self.pause(0.5)
        
        # Beat 8: Transform square to pentagon
        self.fade_out_group([sq_label])
        
        # Pentagon vertices
        P1 = np.array([0, 1.5, 0])
        P2 = np.array([-1.2, 0.5, 0])
        P3 = np.array([-0.8, -1.2, 0])
        P4 = np.array([0.8, -1.2, 0])
        P5 = np.array([1.2, 0.5, 0])
        
        pentagon = self.transform_focus(
            square,
            self.polygon(P1, P2, P3, P4, P5),
            fade_out=[]
        )
        self.pause(0.5)
        
        # Beat 9: Label pentagon as "5 sides"
        pent_center = self.get_shape_center(P1, P2, P3, P4, P5)
        pent_label = self.label_point(pent_center, "5 sides", pent_center)
        self.pause(0.5)
        
        # Beat 10: Show all three polygons side by side
        self.fade_out_group([pent_label, title])
        
        # Position polygons side by side
        tri_pos = np.array([-4, 0, 0])
        sq_pos = np.array([0, 0, 0])
        pent_pos = np.array([4, 0, 0])
        
        # Create new polygons at new positions
        tri_vertices = [A + tri_pos, B + tri_pos, C + tri_pos]
        tri_final = self.polygon(*tri_vertices)
        tri_final_center = self.get_shape_center(*tri_vertices)
        tri_final_label = self.label_point(tri_final_center, "3 sides", tri_final_center)
        
        sq_vertices = [S1 + sq_pos, S2 + sq_pos, S3 + sq_pos, S4 + sq_pos]
        sq_final = self.polygon(*sq_vertices)
        sq_final_center = self.get_shape_center(*sq_vertices)
        sq_final_label = self.label_point(sq_final_center, "4 sides", sq_final_center)
        
        pent_vertices = [P1 + pent_pos, P2 + pent_pos, P3 + pent_pos, P4 + pent_pos, P5 + pent_pos]
        pent_final = self.polygon(*pent_vertices)
        pent_final_center = self.get_shape_center(*pent_vertices)
        pent_final_label = self.label_point(pent_final_center, "5 sides", pent_final_center)
        
        # Transform pentagon to the three polygons
        self.transform_focus(
            pentagon,
            VGroup(tri_final, sq_final, pent_final),
            fade_out=[]
        )
        
        # Create labels
        self.play_steps(
            Write(tri_final_label),
            Write(sq_final_label),
            Write(pent_final_label)
        )
        self.pause(0.5)
        
        # Beat 11: Emphasize naming rule
        rule_text = self.mtex(r"\text{Named by number of sides}")
        rule_text.scale(1.2)
        rule_text.set_color(YELLOW)
        rule_text.to_edge(UP)
        self.play_steps(Write(rule_text))
        self.pause(1.0)

class GeneratedScene4(CScene):
    def construct(self):
        # Beat 1: Show title
        title = self.setup_scene("Polygons: Regular vs Irregular")
        self.pause(0.5)
        
        # Beat 2: Show regular hexagon
        # Regular hexagon vertices (centered at origin)
        hex_center = ORIGIN
        hex_radius = 2.0
        hex_vertices = []
        for i in range(6):
            angle = i * 2 * PI / 6
            x = hex_center[0] + hex_radius * np.cos(angle)
            y = hex_center[1] + hex_radius * np.sin(angle)
            hex_vertices.append(np.array([x, y, 0]))
        
        regular_hexagon = self.polygon(*hex_vertices)
        shape_center_hex = self.get_shape_center(*hex_vertices)
        hex_label = self.label_point(hex_center, "Regular", shape_center_hex)
        self.pause(0.5)
        
        # Beat 3: Highlight one side and one angle
        # Highlight side 0 (between vertices 0 and 1)
        side0 = self.segment(hex_vertices[0], hex_vertices[1], color=YELLOW, stroke_width=6)
        # Highlight angle at vertex 0 (between vertices 5-0-1)
        angle0 = self.angle_mark(hex_vertices[5], hex_vertices[0], hex_vertices[1], 
                                color=YELLOW, label="")
        self.pause(0.5)
        
        # Beat 4: Fade title and show definition text
        self.fade_out_group([title])
        definition_text = self.mtex(r"\text{All sides equal, all angles equal}")
        definition_text.to_edge(UP)
        self.play_steps(Write(definition_text))
        self.pause(0.5)
        
        # Beat 5: Fade regular hexagon and its text
        self.fade_out_group([regular_hexagon, hex_label, side0, angle0, definition_text])
        self.pause(0.5)
        
        # Beat 6: Show irregular pentagon
        # Irregular pentagon vertices (scalene)
        pent_vertices = [
            np.array([-1.5, 0.5, 0]),    # A
            np.array([0.5, 1.2, 0]),     # B
            np.array([1.8, -0.3, 0]),    # C
            np.array([0.2, -1.5, 0]),    # D
            np.array([-1.8, -0.8, 0])    # E
        ]
        
        irregular_pentagon = self.polygon(*pent_vertices)
        shape_center_pent = self.get_shape_center(*pent_vertices)
        pent_label = self.label_point(self.get_shape_center(*pent_vertices), "Irregular", shape_center_pent)
        self.pause(0.5)
        
        # Beat 7: Highlight two sides of different lengths
        # Side 0 (A-B)
        side_a = self.segment(pent_vertices[0], pent_vertices[1], color=YELLOW, stroke_width=6)
        # Side 2 (C-D)
        side_b = self.segment(pent_vertices[2], pent_vertices[3], color=RED, stroke_width=6)
        self.pause(0.5)
        
        # Beat 8: Show definition text
        definition_text2 = self.mtex(r"\text{Sides and/or angles are different}")
        definition_text2.to_edge(UP)
        self.play_steps(Write(definition_text2))
        self.pause(0.5)
        
        # Beat 9: Fade irregular pentagon and its text
        self.fade_out_group([irregular_pentagon, pent_label, side_a, side_b, definition_text2])
        self.pause(0.5)
        
        # Beat 10: Transform to regular octagon (stop sign)
        # Regular octagon vertices
        oct_radius = 2.0
        oct_vertices = []
        for i in range(8):
            angle = i * 2 * PI / 8 - PI/8  # Rotate so flat side is at top
            x = oct_radius * np.cos(angle)
            y = oct_radius * np.sin(angle)
            oct_vertices.append(np.array([x, y, 0]))
        
        regular_octagon = self.polygon(*oct_vertices)
        # Transform from irregular pentagon to regular octagon
        self.transform_focus(
            irregular_pentagon,
            regular_octagon,
            fade_out=[]
        )
        self.pause(0.5)
        
        # Beat 11: Label the shape
        shape_center_oct = self.get_shape_center(*oct_vertices)
        stop_label = self.label_point(np.array([0, 2.5, 0]), "Stop Sign", shape_center_oct)
        
        conclusion_text = self.mtex(r"\text{Regular Octagon (8 equal sides)}")
        conclusion_text.to_edge(DOWN)
        self.play_steps(Write(conclusion_text))
        self.pause(0.5)
        
        # Beat 12: Emphasize conclusion text
        self.play_steps(Indicate(conclusion_text))
        self.pause(1.0)