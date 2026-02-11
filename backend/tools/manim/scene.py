'''
Manim scene template for HKDSE geometry lessons
This file defines a base scene class `CScene` with helper methods for: 
- common geometric constructions
- text formatting
- dynamic geometry 
Each lesson can subclass this and override the `construct` method to create the specific content for that lesson.

'''
from manim import *
import numpy as np


# ========= Base Scene for HKDSE Geometry =========

class CScene(Scene):
    CONFIG_COLOR_BG = "#1E1E2E"
    CONFIG_COLOR_POINT = YELLOW
    CONFIG_COLOR_LINE = BLUE_B
    CONFIG_COLOR_AUX = GRAY
    CONFIG_COLOR_CIRCLE = GREEN_B
    CONFIG_COLOR_TEXT = WHITE

    def construct(self):
        # Subclasses override this
        pass

    # ---------- Scene / layout boilerplate ----------

    def setup_scene(self, title: str, subtitle: str | None = None) -> VGroup:
        title_m = Text(title, weight=BOLD, font_size=40, color=self.CONFIG_COLOR_TEXT)
        title_m.to_edge(UP)
        if subtitle:
            subtitle_m = Text(subtitle, font_size=28, color=self.CONFIG_COLOR_TEXT)
            subtitle_m.next_to(title_m, DOWN, buff=0.1)
            group = VGroup(title_m, subtitle_m)
        else:
            group = VGroup(title_m)
        self.play(Write(group))
        self.wait(0.5)
        return group

    def pause(self, t: float = 0.5) -> None:
        self.wait(t)

    def play_steps(self, *anims, run_time: float = 1.0, rate_func = smooth) -> None:
        self.play(*anims, run_time=run_time, rate_func=rate_func)


    # ---------- Text & labels ----------

    def mtex(self, s: str, scale: float = 0.9, color=None) -> MathTex:
        m = MathTex(s)
        m.scale(scale)
        if color:
            m.set_color(color)
        else:
            m.set_color(self.CONFIG_COLOR_TEXT)
        return m

    def label_point(self, dot: Dot, 
                    name: str,
                    direction=UR, 
                    buff: float = 0.15,
                    font_size: int = 28) -> Text:
        label = Text(name, font_size=font_size, color=self.CONFIG_COLOR_TEXT)
        label.next_to(dot, direction, buff=buff)
        self.play(FadeIn(label, shift=0.2 * direction))
        return label

    def label_line(self, line: Line, 
                   text: str,
                   offset=UP, 
                   buff: float = 0.15,
                   font_size: int = 26) -> Text:
        mid = line.get_center()
        label = Text(text, font_size=font_size, color=self.CONFIG_COLOR_TEXT)
        label.move_to(mid + buff * offset)
        self.play(FadeIn(label))
        return label

    def show_equation_step(
        self,
        prev: Mobject | None,
        new_latex: str,
        to_edge_dir = DOWN,
        buff: float = 0.4
    ) -> MathTex:
        eq = self.mtex(new_latex, scale=0.9)
        eq.to_edge(to_edge_dir, buff=buff)
        if prev is None:
            self.play(Write(eq))
        else:
            self.play(Transform(prev, eq))
            eq = prev  # keep reference
        self.wait(0.3)
        return eq


    # ---------- Coordinate plane helpers ----------

    def make_plane(
        self,
        x_range = [-6, 6, 1],
        y_range = [-4, 4, 1],
        x_length: float = 10,
        y_length: float = 6,
        show_numbers: bool = True,
    ) -> NumberPlane:
        plane = NumberPlane(
            x_range=x_range,
            y_range=y_range,
            x_length=x_length,
            y_length=y_length,
            background_line_style={
                "stroke_color": GRAY_D,
                "stroke_width": 1,
                "stroke_opacity": 0.6,
            },
        )
        if show_numbers:
            plane.add_coordinates()
        plane.to_edge(DOWN, buff=0.4)
        self.play(Create(plane))
        return plane

    def to_xy(self, plane: NumberPlane, x: float, y: float) -> np.ndarray:
        return plane.c2p(x, y)

    def plot_point(
        self,
        plane: NumberPlane,
        x: float,
        y: float,
        color=None,
        radius: float = 0.06,
    ) -> Dot:
        if color is None:
            color = self.CONFIG_COLOR_POINT
        dot = Dot(point=plane.c2p(x, y), radius=radius, color=color)
        self.play(FadeIn(dot, scale=0.8))
        return dot


    # ---------- Static geometric constructions ----------

    def segment(
        self,
        A: np.ndarray,
        B: np.ndarray,
        color=None,
        stroke_width: float = 4,
        dashed: bool = False,
    ) -> Line:
        if color is None:
            color = self.CONFIG_COLOR_LINE
        if dashed:
            line = DashedLine(A, B, color=color, stroke_width=stroke_width)
        else:
            line = Line(A, B, color=color, stroke_width=stroke_width)
        self.play(Create(line))
        return line

    def ray(
        self,
        A: np.ndarray,
        B: np.ndarray,
        length: float = 6,
        color=None,
        stroke_width: float = 4,
    ) -> Line:
        if color is None:
            color = self.CONFIG_COLOR_LINE
        direction = (B - A) / np.linalg.norm(B - A)
        end = A + direction * length
        line = Line(A, end, color=color, stroke_width=stroke_width)
        self.play(Create(line))
        return line

    def polygon(self, *points: np.ndarray,
                color=None,
                stroke_width: float = 4,
                fill_opacity: float = 0.0) -> Polygon:
        if color is None:
            color = self.CONFIG_COLOR_LINE
        poly = Polygon(*points,
                       color=color,
                       stroke_width=stroke_width,
                       fill_opacity=fill_opacity)
        self.play(Create(poly))
        return poly

    def circle_from_center_radius(
        self,
        center: np.ndarray,
        r: float,
        color=None,
        stroke_width: float = 4,
    ) -> Circle:
        if color is None:
            color = self.CONFIG_COLOR_CIRCLE
        circle = Circle(radius=r, color=color, stroke_width=stroke_width)
        circle.move_to(center)
        self.play(Create(circle))
        return circle

    def angle_mark(
        self,
        A: np.ndarray,
        O: np.ndarray,
        B: np.ndarray,
        radius: float = 0.4,
        color=YELLOW,
        label: str | None = None,
        label_offset: float = 0.2,
        label_font_size: int = 26,
    ) -> VGroup:
        # OA and OB rays
        angle = Angle(
            Line(O, A),
            Line(O, B),
            radius=radius,
            other_angle=False,
            color=color,
        )
        group = VGroup(angle)
        if label:
            label_m = MathTex(label, font_size=label_font_size, color=color)
            label_m.move_to(angle.point_from_proportion(0.5) + label_offset * OUT)
            group.add(label_m)
        self.play(Create(group))
        return group

    def right_angle_mark(
        self,
        A: np.ndarray,
        O: np.ndarray,
        B: np.ndarray,
        size: float = 0.25,
        color=YELLOW,
    ) -> Polygon:
        # simple square at vertex O
        OA = (A - O) / np.linalg.norm(A - O)
        OB = (B - O) / np.linalg.norm(B - O)
        p1 = O + OA * size
        p2 = p1 + OB * size
        p3 = O + OB * size
        mark = Polygon(p1, p2, p3, color=color, fill_opacity=1.0)
        self.play(FadeIn(mark))
        return mark

    def distance_brace(
        self,
        A: np.ndarray,
        B: np.ndarray,
        label: str | None = None,
        label_font_size: int = 26,
        color=WHITE,
    ) -> VGroup:
        brace = BraceBetweenPoints(A, B, color=color)
        group = VGroup(brace)
        if label:
            t = MathTex(label, font_size=label_font_size, color=color)
            t.next_to(brace, brace.get_direction(), buff=0.15)
            group.add(t)
        self.play(GrowFromCenter(brace))
        if len(group) > 1:
            self.play(FadeIn(group[1]))
        return group


    # ---------- Drag-a-point / dynamic geometry ----------

    def tracker(self, x0: float) -> ValueTracker:
        return ValueTracker(x0)

    def dynamic_point_on_plane(
        self,
        plane: NumberPlane,
        x_tracker: ValueTracker,
        y_tracker: ValueTracker,
        color=None,
        radius: float = 0.06,
    ) -> Dot:
        if color is None:
            color = self.CONFIG_COLOR_POINT

        dot = always_redraw(
            lambda: Dot(
                point=plane.c2p(x_tracker.get_value(), y_tracker.get_value()),
                radius=radius,
                color=color,
            )
        )
        self.add(dot)
        return dot

    def dynamic_line(
        self,
        get_A,
        get_B,
        color=None,
        stroke_width: float = 4,
    ) -> Line:
        if color is None:
            color = self.CONFIG_COLOR_LINE

        line = always_redraw(
            lambda: Line(
                get_A(),
                get_B(),
                color=color,
                stroke_width=stroke_width,
            )
        )
        self.add(line)
        return line

    def dynamic_circle_center_point(
        self,
        get_center,
        get_point,
        color=None,
        stroke_width: float = 4,
    ) -> Circle:
        if color is None:
            color = self.CONFIG_COLOR_CIRCLE

        circle = always_redraw(
            lambda: Circle(
                radius=np.linalg.norm(get_point() - get_center()),
                color=color,
                stroke_width=stroke_width,
            ).move_to(get_center())
        )
        self.add(circle)
        return circle

    def dynamic_angle(
        self,
        get_A,
        get_O,
        get_B,
        radius: float = 0.4,
        color=YELLOW,
    ) -> Angle:
        angle = always_redraw(
            lambda: Angle(
                Line(get_O(), get_A()),
                Line(get_O(), get_B()),
                radius=radius,
                color=color,
            )
        )
        self.add(angle)
        return angle

    def freeze_updaters(self, *mobs: Mobject) -> None:
        for m in mobs:
            m.suspend_updating()

    def unfreeze_updaters(self, *mobs: Mobject) -> None:
        for m in mobs:
            m.resume_updating()


    # ---------- HKDSE “lesson atoms” ----------

    def theorem_card(
        self,
        name: str,
        statement_latex: str,
        diagram: Mobject,
    ) -> VGroup:
        title = Text(name, font_size=30, weight=BOLD, color=self.CONFIG_COLOR_TEXT)
        stmt = self.mtex(statement_latex, scale=0.8)
        card = VGroup(title, stmt, diagram)
        card.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        rect = SurroundingRectangle(card, color=WHITE, buff=0.3)
        full = VGroup(rect, card)
        self.play(FadeIn(full))
        return full

    def proof_skeleton(
        self,
        givens: list[str],
        to_prove: str,
    ) -> VGroup:
        given_text = Text("Given:", weight=BOLD, font_size=26).to_corner(UL)
        given_items = VGroup(*[Text(f"- {g}", font_size=24) for g in givens])
        given_items.arrange(DOWN, aligned_edge=LEFT).next_to(given_text, DOWN, buff=0.2)

        prove_text = Text("To prove:", weight=BOLD, font_size=26).next_to(
            given_items, DOWN, buff=0.4
        )
        prove_eq = self.mtex(to_prove, scale=0.8).next_to(prove_text, RIGHT, buff=0.2)

        group = VGroup(given_text, given_items, prove_text, prove_eq)
        self.play(FadeIn(group, lag_ratio=0.1))
        return group

    def locus_traced_path(
        self,
        moving_dot: Dot,
        color=ORANGE,
        stroke_width: float = 3,
    ) -> TracedPath:
        path = TracedPath(moving_dot.get_center,
                          stroke_color=color,
                          stroke_width=stroke_width)
        self.add(path)
        return path

    def coordinate_solution_template(
        self,
        problem_latex: str,
        steps: list[str],
        final_latex: str,
    ) -> VGroup:
        prob = self.mtex(problem_latex, scale=0.8)
        prob.to_edge(UP, buff=0.5)

        self.play(Write(prob))
        last = None
        lines = VGroup()
        for s in steps:
            eq = self.mtex(s, scale=0.8)
            if last is None:
                eq.next_to(prob, DOWN, buff=0.3, aligned_edge=LEFT)
            else:
                eq.next_to(last, DOWN, buff=0.2, aligned_edge=LEFT)
            self.play(Write(eq))
            lines.add(eq)
            last = eq

        final = self.mtex(final_latex, scale=0.9, color=YELLOW)
        final.next_to(last, DOWN, buff=0.4, aligned_edge=LEFT)
        self.play(Write(final))
        return VGroup(prob, lines, final)

    # ==================================
    # TRIGONOMETRY HIGH-LEVEL TEMPLATES
    # ==================================

    ## Basic Trigonometric Ratios

    def animate_right_triangle_ratios(
        self,
        focus_angle: str = "A",
        highlight_sequence: list[str] = ["hyp", "opp", "adj"],
        show_ratio_equations: bool = False,
    ) -> None:
        """
        Label and highlight sides of right triangle relative to an angle.
        Demonstrates opposite, adjacent, and hypotenuse concept.
        
        Args:
            focus_angle: Which angle to focus on ("A" or "B")
            highlight_sequence: Order to highlight sides
            show_ratio_equations: Whether to show sin/cos/tan equations
        """
        # 0-1s: Show triangle with right angle
        A = np.array([-2, -1, 0])
        B = np.array([2, -1, 0])
        C = np.array([-2, 2, 0])
        
        triangle = self.polygon(A, B, C, color=WHITE, fill_opacity=0.1)
        right_mark = self.right_angle_mark(B, A, C)
        self.pause(0.5)
        
        # Mark focus angle
        if focus_angle == "A":
            angle_mark = self.angle_mark(B, A, C, color=YELLOW, label=focus_angle)
            sides = {
                "hyp": (B, C, RED, UR),
                "opp": (B, C, BLUE, RIGHT),
                "adj": (A, B, GREEN, DOWN),
            }
        else:  # angle B
            angle_mark = self.angle_mark(A, B, C, color=YELLOW, label=focus_angle)
            sides = {
                "hyp": (B, C, RED, UR),
                "opp": (A, C, BLUE, LEFT),
                "adj": (A, B, GREEN, DOWN),
            }
        
        self.pause(1)
        
        # 1-7s: Highlight each side
        lines = {}
        for side_name in highlight_sequence:
            P1, P2, color, label_dir = sides[side_name]
            line = self.segment(P1, P2, color=color, stroke_width=6)
            self.label_line(line, side_name, offset=label_dir)
            lines[side_name] = line
            self.play(Indicate(line, scale_factor=1.15))
            self.pause(1.2)
        
        # 7-10s: Show ratio equations if requested
        if show_ratio_equations:
            eq = self.mtex(
                rf"\sin {focus_angle} = \frac{{\text{{opp}}}}{{\text{{hyp}}}}",
                scale=0.8
            )
            eq.to_edge(DOWN, buff=0.5)
            self.play(Write(eq))
            self.pause(1.5)
        else:
            self.play(triangle.animate.set_opacity(0.3))
            self.pause(2)


    def animate_trig_ratio_values(
        self,
        angle_degrees: float = 30,
        ratios: list[str] = ["sin", "cos", "tan"],
    ) -> None:
        """
        Show numerical values of sin/cos/tan for a specific angle.
        Good for special angles (30°, 45°, 60°).
        
        Args:
            angle_degrees: The angle to demonstrate
            ratios: Which ratios to show
        """
        # 0-2s: Show right triangle with specified angle
        A = np.array([-2.5, -1, 0])
        B = np.array([2.5, -1, 0])
        
        # Calculate C based on angle
        angle_rad = angle_degrees * DEGREES
        height = 5 * np.tan(angle_rad)
        C = np.array([-2.5, -1 + height, 0])
        
        triangle = self.polygon(A, B, C, color=WHITE)
        self.right_angle_mark(B, A, C)
        angle_mark = self.angle_mark(B, A, C, color=YELLOW, label=f"{angle_degrees}°")
        self.pause(1.5)
        
        # 2-9s: Show each ratio with value
        import math
        values = {
            "sin": math.sin(angle_rad),
            "cos": math.cos(angle_rad),
            "tan": math.tan(angle_rad),
        }
        
        equations = VGroup()
        for i, ratio in enumerate(ratios):
            val = values[ratio]
            # Format nicely for special angles
            if angle_degrees == 30:
                val_str = r"\frac{1}{2}" if ratio == "sin" else (
                    r"\frac{\sqrt{3}}{2}" if ratio == "cos" else r"\frac{1}{\sqrt{3}}"
                )
            elif angle_degrees == 45:
                val_str = r"\frac{\sqrt{2}}{2}" if ratio != "tan" else "1"
            elif angle_degrees == 60:
                val_str = r"\frac{\sqrt{3}}{2}" if ratio == "sin" else (
                    r"\frac{1}{2}" if ratio == "cos" else r"\sqrt{3}"
                )
            else:
                val_str = f"{val:.3f}"
            
            eq = self.mtex(rf"\{ratio} {angle_degrees}° = {val_str}", scale=0.8)
            equations.add(eq)
        
        equations.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        equations.to_edge(RIGHT, buff=0.8)
        
        for eq in equations:
            self.play(Write(eq))
            self.pause(1.5)


    ## Trigonometric Graphs

    def animate_sine_wave_properties(
        self,
        show_amplitude: bool = True,
        show_period: bool = True,
    ) -> None:
        """
        Show sine wave with key properties marked (max/min, period, zeros).
        
        Args:
            show_amplitude: Whether to mark amplitude
            show_period: Whether to mark period
        """
        # 0-2s: Draw axes and sine curve
        axes = Axes(
            x_range=[0, 2*PI, PI/2],
            y_range=[-1.5, 1.5, 0.5],
            x_length=9,
            y_length=4,
            tips=False,
        ).shift(DOWN*0.5)
        
        sine_curve = axes.plot(lambda x: np.sin(x), color=BLUE, stroke_width=4)
        
        self.play(Create(axes))
        self.play(Create(sine_curve))
        self.pause(0.5)
        
        # 2-5s: Mark maximum and minimum
        max_dot = Dot(axes.c2p(PI/2, 1), color=YELLOW)
        min_dot = Dot(axes.c2p(3*PI/2, -1), color=YELLOW)
        
        self.play(FadeIn(max_dot), FadeIn(min_dot))
        
        if show_amplitude:
            max_label = self.mtex("1", scale=0.7).next_to(max_dot, UR, buff=0.1)
            min_label = self.mtex("-1", scale=0.7).next_to(min_dot, DR, buff=0.1)
            self.play(Write(max_label), Write(min_label))
        
        self.pause(1.5)
        
        # 5-8s: Show period
        if show_period:
            period_brace = BraceBetweenPoints(
                axes.c2p(0, -1.5),
                axes.c2p(2*PI, -1.5),
                direction=DOWN,
            )
            period_label = self.mtex("2\pi", scale=0.8).next_to(period_brace, DOWN)
            
            self.play(GrowFromCenter(period_brace))
            self.play(Write(period_label))
        
        self.pause(2)


    ## Area, Sine Rule, Cosine Rule

    def animate_triangle_area_formula(
        self,
        side_a: float = 4,
        side_b: float = 3,
        angle_C_degrees: float = 60,
    ) -> None:
        """
        Demonstrate area = ½ab sin C formula with visual height.
        
        Args:
            side_a, side_b: Two sides of triangle
            angle_C_degrees: Included angle between sides
        """
        # 0-2s: Show triangle
        A = np.array([-side_b/2, 0, 0])
        angle_rad = angle_C_degrees * DEGREES
        B = np.array([side_b/2, 0, 0])
        C_x = A[0] + side_a * np.cos(angle_rad)
        C_y = side_a * np.sin(angle_rad)
        C = np.array([C_x, C_y, 0])
        
        triangle = self.polygon(A, B, C, color=WHITE, fill_opacity=0.15)
        
        # Label sides
        self.label_line(Line(A, C), "b", offset=LEFT)
        self.label_line(Line(A, B), "a", offset=DOWN)
        
        # Mark angle
        self.angle_mark(B, A, C, color=YELLOW, label="C")
        self.pause(1.5)
        
        # 2-5s: Drop perpendicular height
        h_point = np.array([C_x, 0, 0])
        height_line = self.segment(C, h_point, color=RED, dashed=True)
        self.label_line(height_line, "h", offset=RIGHT)
        
        self.right_angle_mark(C, h_point, B)
        self.pause(1.5)
        
        # 5-8s: Show h = b sin C
        eq1 = self.show_equation_step(None, r"h = b \sin C")
        self.pause(1)
        
        # 8-10s: Show area formula
        eq2 = self.show_equation_step(
            eq1,
            r"\text{Area} = \frac{1}{2} a b \sin C"
        )
        self.pause(2)


    def animate_sine_rule(
        self,
        triangle_angles: tuple[float, float, float] = (30, 60, 90),
    ) -> None:
        """
        Demonstrate sine rule: a/sin A = b/sin B = c/sin C.
        
        Args:
            triangle_angles: Three angles in degrees (A, B, C)
        """
        # 0-2s: Show triangle with labels
        A_deg, B_deg, C_deg = triangle_angles
        
        # Use sine rule to construct triangle
        a = 4.0  # side opposite angle A
        A_rad = A_deg * DEGREES
        B_rad = B_deg * DEGREES
        
        b = a * np.sin(B_rad) / np.sin(A_rad)
        
        # Place triangle
        P1 = np.array([-2, -1, 0])
        P2 = np.array([2, -1, 0])
        P3 = np.array([P1[0] + b * np.cos(A_rad), P1[1] + b * np.sin(A_rad), 0])
        
        triangle = self.polygon(P1, P2, P3, color=WHITE)
        
        # Label vertices
        self.label_point(Dot(P1), "A", direction=LEFT)
        self.label_point(Dot(P2), "B", direction=RIGHT)
        self.label_point(Dot(P3), "C", direction=UP)
        
        # Label sides (opposite angles)
        self.label_line(Line(P2, P3), "a", offset=UR)
        self.label_line(Line(P1, P3), "b", offset=LEFT)
        
        self.pause(1.5)
        
        # 2-6s: Show sine rule equation
        eq = self.show_equation_step(
            None,
            rf"\frac{{a}}{{\sin {A_deg}°}} = \frac{{b}}{{\sin {B_deg}°}}"
        )
        self.pause(2)
        
        # 6-10s: Highlight the ratio relationship
        self.play(Circumscribe(eq, color=YELLOW))
        self.pause(2)


    def animate_cosine_rule(
        self,
        side_a: float = 5,
        side_b: float = 4,
        angle_C_degrees: float = 60,
    ) -> None:
        """
        Demonstrate cosine rule: c² = a² + b² - 2ab cos C.
        
        Args:
            side_a, side_b: Two known sides
            angle_C_degrees: Included angle
        """
        # 0-2s: Show triangle
        import math
        angle_rad = angle_C_degrees * DEGREES
        
        P1 = np.array([-2, -1, 0])
        P2 = np.array([2, -1, 0])
        P3 = np.array([
            P1[0] + side_b * np.cos(angle_rad),
            P1[1] + side_b * np.sin(angle_rad),
            0
        ])
        
        triangle = self.polygon(P1, P2, P3, color=WHITE)
        
        # Label
        self.label_line(Line(P1, P2), f"{side_a}", offset=DOWN)
        self.label_line(Line(P1, P3), f"{side_b}", offset=LEFT)
        self.angle_mark(P2, P1, P3, color=YELLOW, label=f"{angle_C_degrees}°")
        
        # Unknown side c
        c_line = self.segment(P2, P3, color=RED, stroke_width=6)
        self.label_line(c_line, "c", offset=UR)
        
        self.pause(1.5)
        
        # 2-5s: Show formula
        eq1 = self.show_equation_step(
            None,
            rf"c^2 = {side_a}^2 + {side_b}^2 - 2({side_a})({side_b})\cos {angle_C_degrees}°"
        )
        self.pause(2)
        
        # 5-8s: Calculate
        c_squared = side_a**2 + side_b**2 - 2*side_a*side_b*math.cos(angle_rad)
        c = math.sqrt(c_squared)
        
        eq2 = self.show_equation_step(
            eq1,
            rf"c = {c:.2f}"
        )
        
        # 8-10s: Highlight result on diagram
        self.play(Indicate(c_line, scale_factor=1.2, color=YELLOW))
        self.pause(2)


    ## 3D Trigonometry

    def animate_3d_angle_between_lines(
        self,
        show_projection: bool = True,
    ) -> None:
        """
        Demonstrate finding angle between two lines in 3D space.
        Uses projection method.
        
        Args:
            show_projection: Whether to show projection onto base plane
        """
        # 0-2s: Show 3D box with two lines
        # Create simple 3D rectangular prism
        # (Simplified 2D representation of 3D)
        
        # Base rectangle
        A = np.array([-2, -1, 0])
        B = np.array([2, -1, 0])
        C = np.array([2, 1, 0])
        D = np.array([-2, 1, 0])
        
        # Top vertices (shifted up and right to show 3D)
        E = A + np.array([0.5, 1.5, 0])
        F = B + np.array([0.5, 1.5, 0])
        G = C + np.array([0.5, 1.5, 0])
        H = D + np.array([0.5, 1.5, 0])
        
        # Draw edges
        base = self.polygon(A, B, C, D, color=GRAY)
        
        # Vertical edges
        self.segment(A, E, color=GRAY)
        self.segment(B, F, color=GRAY)
        self.segment(C, G, color=GRAY)
        self.segment(D, H, color=GRAY)
        
        # Top edges (some dashed for hidden)
        self.segment(E, F, color=GRAY)
        self.segment(F, G, color=GRAY)
        self.segment(G, H, color=GRAY, dashed=True)
        self.segment(H, E, color=GRAY, dashed=True)
        
        self.pause(1)
        
        # 2-5s: Highlight two lines of interest
        line1 = self.segment(A, G, color=BLUE, stroke_width=5)
        line2 = self.segment(B, H, color=RED, stroke_width=5)
        
        self.pause(1.5)
        
        # 5-8s: Show projection (if enabled)
        if show_projection:
            # Project onto base plane
            proj1 = self.segment(A, C, color=BLUE, stroke_width=3, dashed=True)
            proj2 = self.segment(B, D, color=RED, stroke_width=3, dashed=True)
            
            # Show angle between projections
            # Find intersection point
            M = ORIGIN  # simplified: diagonals intersect at center
            angle = self.angle_mark(C, M, D, color=YELLOW)
            
            self.pause(2)
        
        # 8-10s: Show equation
        eq = self.mtex(r"\cos \theta = \text{(use cosine rule)}", scale=0.8)
        eq.to_edge(DOWN)
        self.play(Write(eq))
        self.pause(2)


    def animate_angle_line_to_plane(
        self,
    ) -> None:
        """
        Show angle between a line and a plane in 3D.
        Uses perpendicular projection from point to plane.
        """
        # 0-2s: Show plane (horizontal) and line
        # Plane represented as rectangle
        plane_corners = [
            np.array([-2.5, -1, 0]),
            np.array([2.5, -1, 0]),
            np.array([2.5, 1, 0]),
            np.array([-2.5, 1, 0]),
        ]
        plane = self.polygon(*plane_corners, color=GRAY, fill_opacity=0.2)
        
        # Point above plane
        P = np.array([0, 2, 0])
        P_dot = Dot(P, color=YELLOW)
        self.play(FadeIn(P_dot))
        self.label_point(P_dot, "P", direction=UP)
        
        # Point on plane
        Q = np.array([1.5, -0.5, 0])
        Q_dot = Dot(Q, color=YELLOW)
        self.play(FadeIn(Q_dot))
        self.label_point(Q_dot, "Q")
        
        # Line PQ
        line_PQ = self.segment(P, Q, color=BLUE, stroke_width=5)
        
        self.pause(1.5)
        
        # 2-5s: Drop perpendicular from P to plane
        P_proj = np.array([P[0], P[1], 0])  # Project onto z=0
        # For visual clarity, project onto plane at same y
        R = np.array([0, -0.5, 0])
        R_dot = Dot(R, color=RED)
        self.play(FadeIn(R_dot))
        self.label_point(R_dot, "R")
        
        perp = self.segment(P, R, color=RED, dashed=True)
        self.right_angle_mark(Q, R, P)
        
        self.pause(1.5)
        
        # 5-8s: Show angle θ in triangle PQR
        angle = self.angle_mark(Q, P, R, color=YELLOW, label="θ")
        
        self.pause(1.5)
        
        # 8-10s: Show formula
        eq = self.mtex(r"\sin \theta = \frac{PR}{PQ}", scale=0.9)
        eq.to_edge(DOWN, buff=0.5)
        self.play(Write(eq))
        self.pause(2)


    ## Solving Trigonometric Equations

    def animate_solve_trig_equation(
        self,
        equation_latex: str = r"\sin \theta = 0.5",
        solutions_degrees: list[float] = [30, 150],
    ) -> None:
        """
        Show solutions of trigonometric equation on unit circle.
        Solutions confined to [0°, 360°].
        
        Args:
            equation_latex: The equation to solve
            solutions_degrees: List of solutions in degrees
        """
        # 0-2s: Show equation
        eq = self.mtex(equation_latex, scale=1.0)
        eq.to_edge(UP, buff=0.8)
        self.play(Write(eq))
        self.pause(1)
        
        # 2-5s: Draw unit circle
        circle = self.circle_from_center_radius(ORIGIN, 2, color=WHITE)
        
        # Draw axes
        self.segment(np.array([-2.5, 0, 0]), np.array([2.5, 0, 0]), color=GRAY)
        self.segment(np.array([0, -2.5, 0]), np.array([0, 2.5, 0]), color=GRAY)
        
        self.pause(1)
        
        # 5-9s: Mark solutions on circle
        for i, angle_deg in enumerate(solutions_degrees):
            angle_rad = angle_deg * DEGREES
            x = 2 * np.cos(angle_rad)
            y = 2 * np.sin(angle_rad)
            point = np.array([x, y, 0])
            
            dot = Dot(point, color=YELLOW)
            self.play(FadeIn(dot, scale=1.5))
            
            label = self.mtex(f"{angle_deg}°", scale=0.7)
            label.next_to(dot, UR if x > 0 else UL, buff=0.15)
            self.play(Write(label))
            
            # Draw radius to point
            radius = self.segment(ORIGIN, point, color=YELLOW, dashed=True)
            
            self.pause(1.5 if i == 0 else 1)
        
        # 9-10s: Final pause
        self.pause(1)
