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
