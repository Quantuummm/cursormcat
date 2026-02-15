"""
Manim Demo: DNA Replication Fork (30-60 seconds)
Shows helicase unwinding, leading/lagging strand synthesis, Okazaki fragments.
Run: manim -pql scripts/demos/dna_replication_demo.py DNAReplication
"""

from manim import *

# ── Color Palette (matches MCAT Mastery game theme) ──────────────────────
BG_COLOR     = "#0A0E17"
HELIX_A      = "#58CC02"   # Green strand (template)
HELIX_B      = "#1CB0F6"   # Blue strand  (template)
NEW_A        = "#FF4B4B"   # Red — newly synthesized
NEW_B        = "#FFC800"   # Gold — newly synthesized
HELICASE_CLR = "#CE82FF"   # Purple enzyme
PRIMASE_CLR  = "#FF9600"   # Orange enzyme
POLYMERASE   = "#00CED1"   # Teal enzyme (Luminara primary)
LIGASE_CLR   = "#FF69B4"   # Pink (Luminara accent)
BASE_PAIR    = "#334155"   # Dim base-pair rungs


class DNAReplication(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        # ── Title ─────────────────────────────────────────────────────
        title = Text("DNA Replication", font_size=44, font="Fredoka One",
                      color=WHITE, weight=BOLD)
        subtitle = Text("The Replication Fork", font_size=24, color=GREY_B)
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.15)
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header, shift=DOWN * 0.3), run_time=0.8)
        self.wait(0.5)

        # ── Draw the double-stranded DNA (simplified as parallel lines) ──
        strand_len = 10
        y_gap = 0.35  # half-gap between strands

        top_strand = Line(LEFT * 5, RIGHT * 5, color=HELIX_A, stroke_width=5)
        bot_strand = Line(LEFT * 5, RIGHT * 5, color=HELIX_B, stroke_width=5)
        top_strand.shift(UP * y_gap)
        bot_strand.shift(DOWN * y_gap)

        # Base pair rungs
        rungs = VGroup()
        for x in range(-4, 5):
            rung = Line(UP * y_gap, DOWN * y_gap, color=BASE_PAIR,
                        stroke_width=2).shift(RIGHT * x * 0.9)
            rungs.add(rung)

        dna = VGroup(top_strand, bot_strand, rungs).shift(DOWN * 0.5)

        dna_label = Text("Double-stranded DNA", font_size=18, color=GREY_B)
        dna_label.next_to(dna, DOWN, buff=0.3)

        self.play(
            Create(top_strand), Create(bot_strand),
            LaggedStart(*[FadeIn(r) for r in rungs], lag_ratio=0.05),
            FadeIn(dna_label, shift=UP * 0.2),
            run_time=1.5
        )
        self.wait(0.6)

        # ── Step 1: Helicase unwinds ──────────────────────────────────
        step1 = Text("1. Helicase unwinds the double helix",
                      font_size=22, color=HELICASE_CLR)
        step1.to_edge(UP, buff=0.4)

        helicase = Circle(radius=0.3, color=HELICASE_CLR,
                          fill_opacity=0.85, stroke_width=2)
        hel_label = Text("Helicase", font_size=12, color=WHITE)
        hel_label.move_to(helicase)
        helicase_grp = VGroup(helicase, hel_label).move_to(dna.get_left() + RIGHT * 0.5)

        self.play(
            ReplacementTransform(header, step1),
            FadeOut(dna_label),
            FadeIn(helicase_grp, scale=0.5),
            run_time=0.8
        )

        # Animate helicase moving right and "splitting" the strands
        fork_x = 0.5  # where the fork will be
        split_top = top_strand.copy().set_color(HELIX_A)
        split_bot = bot_strand.copy().set_color(HELIX_B)

        self.play(
            helicase_grp.animate.move_to(RIGHT * fork_x + DOWN * 0.5),
            # Split: top goes up, bottom goes down (to the right of fork)
            top_strand.animate.put_start_and_end_on(LEFT * 5 + UP * y_gap,
                                                     RIGHT * fork_x + UP * y_gap),
            bot_strand.animate.put_start_and_end_on(LEFT * 5 + DOWN * y_gap,
                                                     RIGHT * fork_x + DOWN * y_gap),
            # Fade out rungs past the fork
            *[FadeOut(r) for r in rungs if r.get_center()[0] > fork_x - 0.5],
            run_time=1.5
        )

        # Draw separated template strands
        sep_top = Line(RIGHT * fork_x + UP * y_gap, RIGHT * 5 + UP * 1.2,
                       color=HELIX_A, stroke_width=5)
        sep_bot = Line(RIGHT * fork_x + DOWN * y_gap, RIGHT * 5 + DOWN * 1.2,
                       color=HELIX_B, stroke_width=5)
        sep_top.shift(DOWN * 0.5)
        sep_bot.shift(DOWN * 0.5)

        self.play(Create(sep_top), Create(sep_bot), run_time=0.8)
        self.wait(0.4)

        # ── Step 2: Leading strand — continuous synthesis ─────────────
        step2 = Text("2. Leading strand: continuous synthesis (5'→3')",
                      font_size=22, color=POLYMERASE)
        step2.to_edge(UP, buff=0.4)

        pol_lead = Circle(radius=0.25, color=POLYMERASE,
                          fill_opacity=0.85, stroke_width=2)
        pol_label = Text("Pol III", font_size=10, color=WHITE)
        pol_label.move_to(pol_lead)
        pol_lead_grp = VGroup(pol_lead, pol_label)
        pol_lead_grp.move_to(RIGHT * (fork_x + 0.3) + UP * 0.7 + DOWN * 0.5)

        # New strand alongside template top — red
        leading_strand = Line(
            RIGHT * fork_x + UP * (y_gap - 0.15) + DOWN * 0.5,
            RIGHT * fork_x + UP * (y_gap - 0.15) + DOWN * 0.5,
            color=NEW_A, stroke_width=5
        )

        self.play(
            ReplacementTransform(step1, step2),
            FadeIn(pol_lead_grp, scale=0.5),
            run_time=0.6
        )

        # Animate polymerase moving and leaving a trail
        end_lead = RIGHT * 4.5 + UP * 1.0 + DOWN * 0.5
        leading_strand_final = Line(
            RIGHT * fork_x + UP * (y_gap - 0.15) + DOWN * 0.5,
            end_lead + DOWN * 0.15,
            color=NEW_A, stroke_width=5
        )

        arrow_5_3 = Text("5' → 3'", font_size=14, color=NEW_A)
        arrow_5_3.next_to(leading_strand_final, UP, buff=0.1)

        self.play(
            pol_lead_grp.animate.move_to(end_lead),
            Transform(leading_strand, leading_strand_final),
            FadeIn(arrow_5_3),
            run_time=2.0
        )

        lead_label = Text("Leading strand", font_size=16, color=NEW_A)
        lead_label.next_to(leading_strand_final, UP, buff=0.25)
        self.play(FadeIn(lead_label, shift=DOWN * 0.1), FadeOut(arrow_5_3),
                  run_time=0.4)
        self.wait(0.3)

        # ── Step 3: Lagging strand — Okazaki fragments ───────────────
        step3 = Text("3. Lagging strand: Okazaki fragments (5'→3')",
                      font_size=22, color=NEW_B)
        step3.to_edge(UP, buff=0.4)

        self.play(ReplacementTransform(step2, step3), run_time=0.5)

        # Primase lays RNA primers
        primase = Circle(radius=0.2, color=PRIMASE_CLR,
                         fill_opacity=0.85, stroke_width=2)
        pri_label = Text("Primase", font_size=9, color=WHITE)
        pri_label.move_to(primase)
        primase_grp = VGroup(primase, pri_label)

        # Create 3 Okazaki fragments on the bottom strand
        frag_starts = [fork_x + 0.5, fork_x + 2.0, fork_x + 3.5]
        frag_len = 1.2
        fragments = VGroup()
        primers = VGroup()

        for i, sx in enumerate(frag_starts):
            # Primer (short orange tick)
            frac = (sx - fork_x) / (5 - fork_x)
            y_at_sx = -(y_gap + frac * 0.85) - 0.5
            primer = Line(
                RIGHT * sx + UP * (y_at_sx + 0.15),
                RIGHT * (sx + 0.25) + UP * (y_at_sx + 0.15),
                color=PRIMASE_CLR, stroke_width=6
            )
            primers.add(primer)

            # Fragment (gold)
            frac_end = ((sx + frag_len) - fork_x) / (5 - fork_x)
            y_at_end = -(y_gap + frac_end * 0.85) - 0.5
            frag = Line(
                RIGHT * (sx + 0.25) + UP * (y_at_sx + 0.15),
                RIGHT * (sx + frag_len) + UP * (y_at_end + 0.15),
                color=NEW_B, stroke_width=5
            )
            fragments.add(frag)

        # Animate primers appearing, then fragments synthesized
        self.play(
            LaggedStart(*[FadeIn(p, scale=1.5) for p in primers],
                         lag_ratio=0.3),
            run_time=1.0
        )

        pol_lag = Circle(radius=0.22, color=POLYMERASE,
                         fill_opacity=0.85, stroke_width=2)
        pol_lag_l = Text("Pol III", font_size=9, color=WHITE)
        pol_lag_l.move_to(pol_lag)
        pol_lag_grp = VGroup(pol_lag, pol_lag_l)
        pol_lag_grp.move_to(primers[0].get_center())

        self.play(FadeIn(pol_lag_grp, scale=0.5), run_time=0.3)
        self.play(
            LaggedStart(*[Create(f) for f in fragments], lag_ratio=0.3),
            run_time=1.5
        )

        lag_label = Text("Lagging strand", font_size=16, color=NEW_B)
        lag_label.next_to(fragments, DOWN, buff=0.25)
        okazaki_label = Text("(Okazaki fragments)", font_size=13, color=GREY_B)
        okazaki_label.next_to(lag_label, DOWN, buff=0.08)

        self.play(FadeIn(lag_label), FadeIn(okazaki_label), run_time=0.5)
        self.wait(0.4)

        # ── Step 4: Ligase seals the gaps ─────────────────────────────
        step4 = Text("4. DNA Ligase seals the fragments",
                      font_size=22, color=LIGASE_CLR)
        step4.to_edge(UP, buff=0.4)

        ligase = Circle(radius=0.22, color=LIGASE_CLR,
                        fill_opacity=0.85, stroke_width=2)
        lig_label = Text("Ligase", font_size=9, color=WHITE)
        lig_label.move_to(ligase)
        ligase_grp = VGroup(ligase, lig_label)
        ligase_grp.move_to(fragments[0].get_left() + LEFT * 0.3)

        self.play(
            ReplacementTransform(step3, step4),
            FadeOut(pol_lag_grp),
            FadeIn(ligase_grp, scale=0.5),
            run_time=0.6
        )

        # Flash each gap to show sealing
        for i in range(len(fragments) - 1):
            gap_pos = fragments[i].get_right()
            flash = Dot(gap_pos, color=LIGASE_CLR, radius=0.08)
            self.play(
                ligase_grp.animate.move_to(gap_pos),
                Flash(gap_pos, color=LIGASE_CLR, line_length=0.15,
                      num_lines=8, flash_radius=0.2),
                FadeOut(flash),
                run_time=0.5
            )

        self.play(FadeOut(ligase_grp), FadeOut(primers), run_time=0.4)
        self.wait(0.3)

        # ── Final summary card ────────────────────────────────────────
        step_final = Text("Two identical DNA molecules!",
                          font_size=28, color=WHITE, weight=BOLD)
        step_final.to_edge(UP, buff=0.4)

        # Summary box
        summary_items = VGroup(
            Text("• Helicase → unwinds", font_size=16, color=HELICASE_CLR),
            Text("• Primase → RNA primers", font_size=16, color=PRIMASE_CLR),
            Text("• DNA Pol III → synthesizes", font_size=16, color=POLYMERASE),
            Text("• Ligase → seals fragments", font_size=16, color=LIGASE_CLR),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

        summary_box = SurroundingRectangle(summary_items, color=GREY_B,
                                            buff=0.2, corner_radius=0.1,
                                            fill_opacity=0.15, fill_color=BG_COLOR)
        summary = VGroup(summary_box, summary_items)
        summary.to_corner(DL, buff=0.5)

        self.play(
            ReplacementTransform(step4, step_final),
            FadeOut(helicase_grp), FadeOut(pol_lead_grp),
            FadeIn(summary, shift=UP * 0.3),
            run_time=1.0
        )

        # Key takeaway
        takeaway = Text("Leading = continuous  |  Lagging = fragments",
                         font_size=20, color=GREY_A)
        takeaway.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(takeaway, shift=UP * 0.2), run_time=0.6)

        self.wait(2)

        # Fade everything out
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.8)
