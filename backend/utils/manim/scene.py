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
        self.play(Write(group), run_time=1)
        self.wait(0.5)
        return group

    def pause(self, t: float = 0.5) -> None:
        self.wait(t)

    def play_steps(self, *anims, run_time: float = 0.5, rate_func = smooth) -> None:
        self.play(*anims, run_time=run_time, rate_func=rate_func)

    # ---------- High-level animation helpers ----------

    def fade_out_group(
        self,
        mobjects: list[Mobject] | tuple[Mobject, ...],
        run_time: float = 0.6,
    ) -> None:
        """
        Fade out multiple non-prominent objects at once.

        Args:
            mobjects: Iterable of mobjects to fade out (labels, guides, etc.)
            run_time: Duration of fade-out animation.
        """
        if not mobjects:
            return
        group = VGroup(*mobjects)
        self.play_steps(FadeOut(group), run_time=run_time)

    def transform_focus(
        self,
        old_main: Mobject,
        new_main: Mobject,
        fade_out: list[Mobject] | tuple[Mobject, ...] = (),
        run_time: float = 1.0,
    ) -> Mobject:
        """
        Transform the main object while fading out secondary helpers.

        Typical pattern:
        - Transform a prominent object (triangle, main line, main equation).
        - Simultaneously fade out labels, braces, guide lines, etc.

        Args:
            old_main: Current prominent object to transform from.
            new_main: Target object to transform to.
            fade_out: Non-prominent objects to fade away during the transform.
            run_time: Duration of the transform.

        Returns:
            The (now transformed) main object, for continued use.
        """
        anims = [ReplacementTransform(old_main, new_main)]
        if fade_out:
            anims.append(FadeOut(VGroup(*fade_out)))
        self.play_steps(*anims, run_time=run_time)
        return new_main

    # ---------- Text & labels ----------

    def mtex(self, s: str, scale: float = 0.9, color=None) -> MathTex:
        m = SingleStringMathTex(s)
        m.scale(scale)
        if color:
            m.set_color(color)
        else:
            m.set_color(self.CONFIG_COLOR_TEXT)
        return m

    def label_point(self, point: np.ndarray, name: str, shape_center: np.ndarray, font_size: int = 28) -> Text:
        """
        Label a point positioned OUTSIDE the shape, away from shape center.
        
        Args:
            point: The point location to label
            name: Label text (≤3 chars)
            shape_center: Center of the polygon/shape (use triangle/pentagon center)
        """
        label = Text(name, font_size=font_size, color=self.CONFIG_COLOR_TEXT)
        
        # Vector from shape center → this point (outward direction)
        outward_dir = (point - shape_center) / np.linalg.norm(point - shape_center) if np.linalg.norm(point - shape_center) > 1e-6 else RIGHT
        
        # Position label outside: point + outward direction
        label_pos = point + 0.4 * outward_dir
        label.move_to(label_pos)
        
        self.play_steps(FadeIn(label, shift=0.2 * outward_dir))
        return label

    def label_line(self, line: Line, text: str, 
               shape_center: np.ndarray, font_size: int = 26) -> Text:
        """
        Label a line positioned OUTSIDE the shape, away from shape center.
        
        Args:
            line: The line/segment to label
            text: Label text (≤3 chars)
            shape_center: Center of the polygon/shape
        """
        mid = line.get_center()
        label = Text(text, font_size=font_size, color=self.CONFIG_COLOR_TEXT)
        
        # Vector from shape center → line midpoint (outward direction)
        outward_dir = (mid - shape_center) / np.linalg.norm(mid - shape_center) if np.linalg.norm(mid - shape_center) > 1e-6 else RIGHT
        
        # Position label outside near line: midpoint + outward direction
        label_pos = mid + 0.35 * outward_dir
        label.move_to(label_pos)
        
        self.play_steps(FadeIn(label, shift=0.2 * OUT))
        return label

    def get_shape_center(self, *points: np.ndarray) -> np.ndarray:
        """Average of polygon vertices = shape center."""
        if not points:
            return [0,0]
        return np.mean(points, axis=0)


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
        # Vectors OA and OB
        v1 = A - O
        v2 = B - O

        # Angles of OA, OB in [-pi, pi]
        ang1 = np.arctan2(v1[1], v1[0])
        ang2 = np.arctan2(v2[1], v2[0])

        # Difference in [-pi, pi]
        diff = ang2 - ang1
        diff = (diff + np.pi) % (2 * np.pi) - np.pi

        # If diff is negative, swap lines so that Angle takes the smaller interior angle
        if diff < 0:
            line1 = Line(O, B)
            line2 = Line(O, A)
        else:
            line1 = Line(O, A)
            line2 = Line(O, B)

        # OA and OB rays
        angle = Angle(
            line1,
            line2,
            radius=radius,
            other_angle=False,
            color=color,
        )
        group = VGroup(angle)
        
        if label:
            # Angle bisector direction (unit vector pointing into/out of angle)
            bisector_dir = normalize(A - O + B - O)  # Sum OA + OB vectors  
            label_m = MathTex(label, font_size=label_font_size, color=color)
            label_m.move_to(angle.point_from_proportion(0.5) + label_offset * bisector_dir)
            group.add(label_m)
        self.play(Create(group))
        return group

    def right_angle_mark(
        self,
        A: np.ndarray,
        O: np.ndarray,
        B: np.ndarray,
        size: float = 0.4,
        color=YELLOW,
    ) -> RightAngle:
        right_angle = RightAngle(
            Line(O, A),
            Line(O, B),
            length=size,
            color=color,
        )

        self.play(FadeIn(right_angle, scale=0.8))
        return right_angle


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

    # ---------- Generic shape ----------