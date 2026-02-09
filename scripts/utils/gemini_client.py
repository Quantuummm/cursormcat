"""
Gemini API client wrapper with rate limiting, JSON mode, retry logic, and cost tracking.

Model strategy:
  - gemini-2.5-flash: All EXTRACTION from PDFs (copyright-safe, reads textbooks)
  - gemini-3-flash-preview: All GENERATION (restructuring, question writing, enrichment)
"""

import json
import time
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_LIGHT,
    GEMINI_MODEL_HEAVY,
    GEMINI_MODEL_CREATIVE,
    GEMINI_TEMPERATURE_EXTRACT,
    GEMINI_TEMPERATURE_RESTRUCTURE,
    GEMINI_TEMPERATURE_ENRICH,
    GEMINI_DELAY_BETWEEN_REQUESTS,
    PROJECT_ROOT,
)

# ─── Cost Estimates (per 1M tokens, free tier = $0) ────────
# These are approximate paid-tier rates for tracking purposes.
# On the free tier you pay $0 but we track to estimate what it WOULD cost.
# Rates from https://ai.google.dev/gemini-api/docs/billing
COST_PER_1M_INPUT = {
    "gemini-2.0-flash":       0.10,
    "gemini-2.5-flash":       0.15,
    "gemini-2.5-flash-lite":  0.075,
    "gemini-3-flash-preview": 0.20,   # Preview pricing, may change
}
COST_PER_1M_OUTPUT = {
    "gemini-2.0-flash":       0.40,
    "gemini-2.5-flash":       0.60,
    "gemini-2.5-flash-lite":  0.30,
    "gemini-3-flash-preview": 0.80,   # Preview pricing, may change
}


class GeminiClient:
    """
    Wrapper around the Gemini API with:
    - Multi-model support (light vs heavy)
    - Automatic JSON mode (response_mime_type="application/json")
    - Rate limiting (respects free tier RPM)
    - Retry on failures with exponential backoff
    - PDF upload support
    - Temperature presets for extraction vs restructuring
    - Cost/token tracking per call and cumulative
    """

    TEMP_EXTRACT = GEMINI_TEMPERATURE_EXTRACT
    TEMP_RESTRUCTURE = GEMINI_TEMPERATURE_RESTRUCTURE
    TEMP_ENRICH = GEMINI_TEMPERATURE_ENRICH

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey\n"
                "Then create a .env file in the project root with:\n"
                "GEMINI_API_KEY=your_key_here"
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self._last_request_time = 0
        self._uploaded_files = {}

        # ─── Cost Tracking ──────────────────────────────────
        self._usage_log = []       # Every call logged
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_estimate = 0.0
        self._call_count = 0
        self._session_start = datetime.now()

    def _get_model(self, model_name: str, temperature: float):
        """Create a Gemini model instance with JSON output mode."""
        return genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < GEMINI_DELAY_BETWEEN_REQUESTS:
            sleep_time = GEMINI_DELAY_BETWEEN_REQUESTS - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _track_usage(self, model_name: str, phase: str, response):
        """Track token usage and estimated cost from a response."""
        try:
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count or 0
            output_tokens = usage.candidates_token_count or 0
        except (AttributeError, TypeError):
            input_tokens = 0
            output_tokens = 0

        # Calculate cost estimate
        input_cost = (input_tokens / 1_000_000) * COST_PER_1M_INPUT.get(model_name, 0.15)
        output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT.get(model_name, 0.60)
        call_cost = input_cost + output_cost

        # Update totals
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_estimate += call_cost
        self._call_count += 1

        # Log this call
        entry = {
            "call_number": self._call_count,
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "phase": phase,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_estimate": round(call_cost, 6),
        }
        self._usage_log.append(entry)

        # Print inline cost report
        print(f"     📊 Tokens: {input_tokens:,} in / {output_tokens:,} out | "
              f"Cost: ${call_cost:.4f} | Running total: ${self._total_cost_estimate:.4f}")

    def upload_pdf(self, pdf_path: str | Path) -> object:
        """Upload a PDF to Gemini's file API. Caches uploads."""
        pdf_path = str(pdf_path)
        if pdf_path in self._uploaded_files:
            return self._uploaded_files[pdf_path]

        print(f"  📤 Uploading PDF: {Path(pdf_path).name}...")
        uploaded = genai.upload_file(pdf_path)

        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)

        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"PDF upload failed. State: {uploaded.state.name}")

        self._uploaded_files[pdf_path] = uploaded
        print(f"  ✅ PDF uploaded and ready")
        return uploaded

    # ─── Public Methods ─────────────────────────────────────

    def extract_light(self, prompt: str, pdf_file=None, phase: str = "extract_light", max_retries: int = 3) -> dict:
        """
        Light extraction: small/focused output (TOC, assessments, figures, enrichment).
        Uses gemini-2.5-flash (65K output, reliable).
        """
        return self._call(GEMINI_MODEL_LIGHT, prompt, pdf_file, self.TEMP_EXTRACT, phase, max_retries)

    def extract_heavy(self, prompt: str, pdf_file=None, phase: str = "extract_heavy", max_retries: int = 3) -> dict:
        """
        Heavy extraction: large structured output (full chapter sections, glossary).
        Uses gemini-3-flash-preview (65K output, best reasoning).
        """
        return self._call(GEMINI_MODEL_HEAVY, prompt, pdf_file, self.TEMP_EXTRACT, phase, max_retries)

    def restructure(self, prompt: str, phase: str = "restructure", max_retries: int = 3) -> dict:
        """
        Restructure content into guided learning format.
        Uses Gemini 3 Flash (best reasoning for ADHD-optimized question wording).
        No PDF attached — works from already-extracted text, so no copyright issues.
        """
        return self._call(GEMINI_MODEL_CREATIVE, prompt, None, self.TEMP_RESTRUCTURE, phase, max_retries)

    def enrich(self, prompt: str, phase: str = "enrich", max_retries: int = 3) -> dict:
        """
        Enrichment/generation tasks (wrong-answer explanations, bridges, game classification).
        Uses Gemini 3 Flash (best quality for generating explanations and questions).
        No PDF attached — works from already-extracted text, so no copyright issues.
        """
        return self._call(GEMINI_MODEL_CREATIVE, prompt, None, self.TEMP_ENRICH, phase, max_retries)

    # Legacy alias
    def extract(self, prompt: str, pdf_file=None, max_retries: int = 3) -> dict:
        return self.extract_heavy(prompt, pdf_file, "extract_legacy", max_retries)

    # ─── Cost Reporting ─────────────────────────────────────

    def print_cost_summary(self):
        """Print a summary of all API usage and estimated costs."""
        elapsed = (datetime.now() - self._session_start).total_seconds()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print(f"\n{'='*60}")
        print(f"💰 BILLING SUMMARY")
        print(f"{'='*60}")
        print(f"  Session duration: {minutes}m {seconds}s")
        print(f"  Total API calls:  {self._call_count}")
        print(f"  Input tokens:     {self._total_input_tokens:,}")
        print(f"  Output tokens:    {self._total_output_tokens:,}")
        print(f"  Total tokens:     {self._total_input_tokens + self._total_output_tokens:,}")
        print(f"  ─────────────────────────────────")
        print(f"  Estimated cost:   ${self._total_cost_estimate:.4f}")
        print(f"  (Free tier = $0 actual. This shows what paid tier would cost.)")
        print(f"{'='*60}")

        # Breakdown by model
        model_usage = {}
        for entry in self._usage_log:
            model = entry["model"]
            if model not in model_usage:
                model_usage[model] = {"calls": 0, "input": 0, "output": 0, "cost": 0.0}
            model_usage[model]["calls"] += 1
            model_usage[model]["input"] += entry["input_tokens"]
            model_usage[model]["output"] += entry["output_tokens"]
            model_usage[model]["cost"] += entry["cost_estimate"]

        if model_usage:
            print(f"\n  By model:")
            for model, stats in model_usage.items():
                print(f"    {model}:")
                print(f"      Calls: {stats['calls']} | Tokens: {stats['input']:,} in / {stats['output']:,} out | ${stats['cost']:.4f}")

        # Breakdown by phase
        phase_usage = {}
        for entry in self._usage_log:
            phase = entry["phase"]
            if phase not in phase_usage:
                phase_usage[phase] = {"calls": 0, "cost": 0.0}
            phase_usage[phase]["calls"] += 1
            phase_usage[phase]["cost"] += entry["cost_estimate"]

        if phase_usage:
            print(f"\n  By phase:")
            for phase, stats in phase_usage.items():
                print(f"    {phase}: {stats['calls']} calls, ${stats['cost']:.4f}")

    def save_usage_log(self, filename: str = None):
        """Save detailed usage log to a JSON file."""
        if not filename:
            timestamp = self._session_start.strftime("%Y%m%d_%H%M%S")
            filename = f"usage_log_{timestamp}.json"

        log_path = PROJECT_ROOT / filename
        log_data = {
            "session_start": self._session_start.isoformat(),
            "total_calls": self._call_count,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_estimate": round(self._total_cost_estimate, 6),
            "models_used": {
                "light": GEMINI_MODEL_LIGHT,
                "heavy": GEMINI_MODEL_HEAVY,
            },
            "calls": self._usage_log,
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"  💾 Usage log saved: {filename}")
        return log_path

    # ─── Internal ───────────────────────────────────────────

    def _call(self, model_name: str, prompt: str, pdf_file, temperature: float, phase: str, max_retries: int) -> dict:
        """Internal: make a Gemini API call with retries, JSON parsing, and cost tracking."""
        model = self._get_model(model_name, temperature)

        for attempt in range(max_retries):
            try:
                self._rate_limit()

                content = []
                if pdf_file:
                    content.append(pdf_file)
                content.append(prompt)

                response = model.generate_content(content)

                # Track usage BEFORE parsing (so we log even if JSON fails)
                self._track_usage(model_name, phase, response)

                # Parse JSON response
                result = json.loads(response.text)
                return result

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        print(f"  🔄 Retrying...")
                        time.sleep(2 ** attempt)
                else:
                    print(f"  ❌ Failed to parse JSON after {max_retries} attempts")
                    print(f"  Raw response (first 500 chars): {response.text[:500]}")
                    raise

            except Exception as e:
                print(f"  ⚠️  API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  🔄 Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    def cleanup(self):
        """Delete uploaded files from Gemini's servers."""
        for path, uploaded in self._uploaded_files.items():
            try:
                genai.delete_file(uploaded.name)
                print(f"  🗑️  Deleted uploaded file: {Path(path).name}")
            except Exception:
                pass
        self._uploaded_files.clear()
