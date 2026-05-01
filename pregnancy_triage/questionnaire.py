"""
Terminal-based clinical questionnaire for the Muuza Pregnancy Triage tool.

Run directly:  python3 -m pregnancy_triage.questionnaire
"""

from __future__ import annotations
import sys
import textwrap
from .models import PatientContext
from .engine import ClinicalEngine
from .renderers import render_terminal


class Questionnaire:
    """
    Guides a clinician or patient through the triage questions in the terminal.
    Returns a fully populated PatientContext for the engine to assess.
    """

    # ------------------------------------------------------------------
    # Low-level input helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _yn(prompt: str) -> bool:
        while True:
            raw = input(f"  {prompt} (y/n): ").strip().lower()
            if raw in ("y", "yes"):
                return True
            if raw in ("n", "no"):
                return False
            print("    Please enter y or n.")

    @staticmethod
    def _choose(prompt: str, options: list[tuple[str, str]]) -> str:
        """Numbered menu; returns the value of the chosen option."""
        print(f"  {prompt}")
        for i, (label, _) in enumerate(options, start=1):
            print(f"    {i}. {label}")
        while True:
            raw = input("  Enter number: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1][1]
            print(f"    Please enter a number between 1 and {len(options)}.")

    @staticmethod
    def _integer(prompt: str, lo: int, hi: int) -> int:
        while True:
            raw = input(f"  {prompt} ({lo}–{hi}): ").strip()
            if raw.isdigit() and lo <= int(raw) <= hi:
                return int(raw)
            print(f"    Please enter a whole number between {lo} and {hi}.")

    @staticmethod
    def _float_input(prompt: str, lo: float, hi: float) -> float:
        while True:
            raw = input(f"  {prompt}: ").strip()
            try:
                val = float(raw)
                if lo <= val <= hi:
                    return val
            except ValueError:
                pass
            print(f"    Please enter a number between {lo} and {hi}.")

    # ------------------------------------------------------------------
    # Section prompts
    # ------------------------------------------------------------------

    def _ask_immediate_danger(self, ctx: PatientContext) -> bool:
        """Return True if patient needs 999 immediately (no further questions)."""
        print()
        print("  EMERGENCY SCREENING")
        print("  " + "─" * 52)
        if self._yn("Is the patient currently fitting or unconscious?"):
            ctx.seizure = True
            return True
        if self._yn("Signs of severe blood loss (very pale, faint, collapsed)?"):
            ctx.has_bleeding = True
            ctx.bleeding_amount = "soaking"
            return True
        return False

    def _ask_gestation(self, ctx: PatientContext) -> None:
        print()
        print("  GESTATIONAL AGE")
        print("  " + "─" * 52)
        ctx.weeks = self._integer("How many completed weeks pregnant?", 1, 42)
        ctx.days  = self._integer("And how many extra days?", 0, 6)

    def _ask_bleeding(self, ctx: PatientContext) -> None:
        print()
        print("  BLEEDING / SPOTTING")
        print("  " + "─" * 52)
        ctx.has_bleeding = self._yn("Any vaginal bleeding or spotting?")
        if not ctx.has_bleeding:
            return
        ctx.bleeding_amount = self._choose(
            "How much blood?",
            [
                ("A few spots on underwear", "spots"),
                ("Light — like a light period", "light"),
                ("Heavy — like a heavy period", "heavy"),
                ("Soaking through pads", "soaking"),
            ],
        )
        ctx.bleeding_with_clots = self._yn("Any clots passed?")

    def _ask_pain(self, ctx: PatientContext) -> None:
        print()
        print("  PAIN / CRAMPING")
        print("  " + "─" * 52)
        ctx.has_pain = self._yn("Any abdominal or pelvic pain or cramping?")
        if not ctx.has_pain:
            return
        ctx.pain_severity = self._integer("Pain severity (1 = very mild, 10 = worst imaginable)", 1, 10)
        ctx.pain_location  = self._choose(
            "Where is the pain mainly felt?",
            [
                ("Lower abdomen / pelvis", "lower_abdomen"),
                ("Upper abdomen / under ribs", "upper_abdomen"),
                ("One-sided (left or right)", "one_sided"),
                ("All over / difficult to pinpoint", "generalised"),
            ],
        )
        ctx.pain_character = self._choose(
            "How would you describe the pain?",
            [
                ("Cramping / coming and going", "cramping"),
                ("Constant / always there", "constant"),
                ("Sharp / stabbing", "sharp"),
                ("Pressure / heaviness", "pressure"),
            ],
        )
        ctx.shoulder_tip_pain = self._yn(
            "Any pain at the tip of the shoulder (not the neck or upper arm)?"
        )

    def _ask_nausea(self, ctx: PatientContext) -> None:
        print()
        print("  NAUSEA / VOMITING")
        print("  " + "─" * 52)
        ctx.has_nausea = self._yn("Any nausea or vomiting?")
        if not ctx.has_nausea:
            return
        ctx.vomiting_frequency = self._integer(
            "Times vomited in the last 24 hours (0 if nausea only)", 0, 30
        )
        if ctx.vomiting_frequency > 0:
            ctx.unable_to_keep_fluids = self._yn(
                "Unable to keep any fluids down for more than 12 hours?"
            )

    def _ask_discharge(self, ctx: PatientContext) -> None:
        print()
        print("  VAGINAL DISCHARGE")
        print("  " + "─" * 52)
        ctx.has_discharge_change = self._yn("Any change in vaginal discharge?")
        if not ctx.has_discharge_change:
            return
        ctx.discharge_colour = self._choose(
            "What does the discharge look like?",
            [
                ("Clear or white (just more than usual)", "clear_white"),
                ("Yellow or green", "yellow_green"),
                ("Grey", "grey"),
                ("Pink or brown-tinged", "pink_brown"),
                ("Sudden watery gush", "watery"),
            ],
        )
        ctx.discharge_odour = self._yn("Is there an unusual or unpleasant smell?")
        ctx.has_itching      = self._yn("Any generalised itching of the skin?")

    def _ask_systemic(self, ctx: PatientContext) -> None:
        print()
        print("  GENERAL / SYSTEMIC SYMPTOMS")
        print("  " + "─" * 52)
        ctx.fever         = self._yn("Any fever or temperature ≥38°C?")
        if ctx.fever:
            ctx.fever_temp = self._float_input("Measured temperature in °C (0 if unknown)", 36.0, 42.0)
        ctx.chest_pain     = self._yn("Any chest pain?")
        ctx.breathlessness = self._yn("Any new or worsening breathlessness?")
        ctx.dizziness      = self._yn("Any dizziness or feeling faint?")
        ctx.trauma         = self._yn("Any fall or blow to the abdomen?")

        if ctx.weeks >= 20:
            print()
            print("  PRE-ECLAMPSIA SCREENING  (relevant from 20 weeks)")
            print("  " + "─" * 52)
            ctx.headache_severe     = self._yn("Any severe headache not relieved by paracetamol?")
            ctx.visual_disturbance  = self._yn("Any visual disturbances (flashing lights, blurred vision)?")
            ctx.facial_hand_swelling = self._yn("Any sudden swelling of face, hands, or feet?")

        if ctx.weeks >= 24:
            print()
            print("  FETAL MOVEMENTS  (relevant from 24 weeks)")
            print("  " + "─" * 52)
            ctx.reduced_movements = self._yn(
                "Any reduction in the baby's movements compared to the usual pattern?"
            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> PatientContext:
        print()
        print("  ══════════════════════════════════════════════════════════════")
        print("  MUUZA PREGNANCY TRIAGE — CLINICAL QUESTIONNAIRE")
        print("  Based on NICE CG62, NG25, NG133, NG201, NG158")
        print("  ══════════════════════════════════════════════════════════════")
        print()
        print(
            textwrap.fill(
                "  Answer each question carefully. "
                "If the patient is in immediate danger, stop and call 999.",
                width=70,
            )
        )

        ctx = PatientContext(weeks=0)

        immediate = self._ask_immediate_danger(ctx)
        if immediate:
            ctx.weeks = 0
            ctx.seizure = True
            return ctx

        self._ask_gestation(ctx)
        self._ask_bleeding(ctx)
        self._ask_pain(ctx)
        self._ask_nausea(ctx)
        self._ask_discharge(ctx)
        self._ask_systemic(ctx)

        return ctx


# ---------------------------------------------------------------------------
# Terminal entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        questionnaire = Questionnaire()
        ctx = questionnaire.run()
        engine = ClinicalEngine()
        result = engine.assess(ctx)
        render_terminal(result)
    except KeyboardInterrupt:
        print("\n\n  Assessment cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
