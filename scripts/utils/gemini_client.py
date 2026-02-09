"""
Gemini API client with automatic fallback, rate limiting, JSON mode, and cost tracking.

Model strategy:
  - PDF extraction: gemini-2.5-flash (copyright-safe)
  - Generation tasks: gemini-3-flash-preview FIRST, fallback to 2.5-flash if it fails
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
    GEMINI_MODEL_PRIMARY,
    GEMINI_MODEL_FALLBACK,
    GEMINI_MODEL_EXTRACT,
    GEMINI_TEMPERATURE_EXTRACT,
    GEMINI_TEMPERATURE_RESTRUCTURE,
    GEMINI_TEMPERATURE_ENRICH,
    GEMINI_DELAY_BETWEEN_REQUESTS,
    PROJECT_ROOT,
)

# ─── Cost Estimates (per 1M tokens, free tier = $0) ────────
COST_PER_1M_INPUT = {
    "gemini-2.0-flash": 0.10, "gemini-2.5-flash": 0.15,
    "gemini-2.5-flash-lite": 0.075, "gemini-3-flash-preview": 0.20,
}
COST_PER_1M_OUTPUT = {
    "gemini-2.0-flash": 0.40, "gemini-2.5-flash": 0.60,
    "gemini-2.5-flash-lite": 0.30, "gemini-3-flash-preview": 0.80,
}


class GeminiClient:
    """
    Gemini API wrapper with:
    - Automatic Gemini 3 → 2.5 fallback on generation tasks
    - JSON mode enforced on all calls
    - Rate limiting for free tier
    - Per-call and cumulative cost tracking
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey\n"
                "Then add to .env: GEMINI_API_KEY=your_key_here"
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self._last_request_time = 0
        self._uploaded_files = {}
        self._usage_log = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_estimate = 0.0
        self._call_count = 0
        self._session_start = datetime.now()

    # ─── Public API ─────────────────────────────────────────

    def extract_light(self, prompt, pdf_file=None, phase="extract_light", max_retries=2):
        """Small extraction (TOC, assessments, figures). Uses 2.5 Flash (copyright-safe)."""
        return self._call(GEMINI_MODEL_EXTRACT, prompt, pdf_file,
                          GEMINI_TEMPERATURE_EXTRACT, phase, max_retries, fallback=False)

    def extract_heavy(self, prompt, pdf_file=None, phase="extract_heavy", max_retries=2):
        """Large extraction (full chapter sections, glossary). Uses 2.5 Flash (copyright-safe)."""
        return self._call(GEMINI_MODEL_EXTRACT, prompt, pdf_file,
                          GEMINI_TEMPERATURE_EXTRACT, phase, max_retries, fallback=False)

    def restructure(self, prompt, phase="restructure", max_retries=2):
        """Restructure into guided learning. Gemini 3 first, falls back to 2.5."""
        return self._call_with_fallback(prompt, None,
                                        GEMINI_TEMPERATURE_RESTRUCTURE, phase, max_retries)

    def enrich(self, prompt, phase="enrich", max_retries=2):
        """Generation tasks (explanations, games, bridges). Gemini 3 first, falls back to 2.5."""
        return self._call_with_fallback(prompt, None,
                                        GEMINI_TEMPERATURE_ENRICH, phase, max_retries)

    def extract(self, prompt, pdf_file=None, max_retries=2):
        """Legacy alias — uses extract_heavy."""
        return self.extract_heavy(prompt, pdf_file, "extract", max_retries)

    def upload_pdf(self, pdf_path):
        """Upload PDF to Gemini file API. Cached per path."""
        pdf_path = str(pdf_path)
        if pdf_path in self._uploaded_files:
            return self._uploaded_files[pdf_path]
        print(f"  📤 Uploading PDF: {Path(pdf_path).name}...")
        uploaded = genai.upload_file(pdf_path)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)
        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"PDF upload failed: {uploaded.state.name}")
        self._uploaded_files[pdf_path] = uploaded
        print(f"  ✅ PDF ready")
        return uploaded

    # ─── Core call with fallback ────────────────────────────

    def _call_with_fallback(self, prompt, pdf_file, temperature, phase, max_retries):
        """Try Gemini 3 Flash first. If it fails, fall back to 2.5 Flash."""
        try:
            return self._call(GEMINI_MODEL_PRIMARY, prompt, pdf_file,
                              temperature, phase, max_retries, fallback=False)
        except Exception as e:
            err_str = str(e)
            # Check for copyright block or persistent failure
            if "copyrighted" in err_str.lower() or "finish_reason" in err_str.lower() \
               or "reciting" in err_str.lower() or "RECITATION" in err_str:
                print(f"  ⬇️  Gemini 3 blocked (copyright). Falling back to 2.5 Flash...")
            else:
                print(f"  ⬇️  Gemini 3 failed: {err_str[:100]}. Falling back to 2.5 Flash...")
            return self._call(GEMINI_MODEL_FALLBACK, prompt, pdf_file,
                              temperature, f"{phase}_fallback", max_retries, fallback=False)

    def _call(self, model_name, prompt, pdf_file, temperature, phase, max_retries, fallback=False):
        """Make a Gemini API call with retries, JSON parsing, and cost tracking."""
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )

        for attempt in range(max_retries):
            try:
                self._rate_limit()
                content = []
                if pdf_file:
                    content.append(pdf_file)
                content.append(prompt)

                response = model.generate_content(content)
                self._track_usage(model_name, phase, response)

                result = json.loads(response.text)
                return result

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON error (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        time.sleep(2 ** attempt)
                else:
                    raise

            except Exception as e:
                err_msg = str(e)
                # Don't retry copyright blocks — they won't resolve
                if "copyrighted" in err_msg.lower() or "reciting" in err_msg.lower():
                    raise
                print(f"  ⚠️  API error (attempt {attempt+1}/{max_retries}): {err_msg[:80]}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                else:
                    raise

    # ─── Rate limiting ──────────────────────────────────────

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < GEMINI_DELAY_BETWEEN_REQUESTS:
            time.sleep(GEMINI_DELAY_BETWEEN_REQUESTS - elapsed)
        self._last_request_time = time.time()

    # ─── Cost tracking ──────────────────────────────────────

    def _track_usage(self, model_name, phase, response):
        try:
            u = response.usage_metadata
            inp = u.prompt_token_count or 0
            out = u.candidates_token_count or 0
        except (AttributeError, TypeError):
            inp, out = 0, 0

        cost = (inp / 1e6) * COST_PER_1M_INPUT.get(model_name, 0.15) + \
               (out / 1e6) * COST_PER_1M_OUTPUT.get(model_name, 0.60)

        self._total_input_tokens += inp
        self._total_output_tokens += out
        self._total_cost_estimate += cost
        self._call_count += 1
        self._usage_log.append({
            "n": self._call_count, "time": datetime.now().isoformat(),
            "model": model_name, "phase": phase,
            "in": inp, "out": out, "cost": round(cost, 6),
        })
        print(f"     📊 [{model_name.split('-')[-1]}] {inp:,}in/{out:,}out "
              f"${cost:.4f} | total: ${self._total_cost_estimate:.4f}")

    def print_cost_summary(self):
        elapsed = (datetime.now() - self._session_start).total_seconds()
        print(f"\n{'='*60}")
        print(f"💰 BILLING: {self._call_count} calls | "
              f"{self._total_input_tokens + self._total_output_tokens:,} tokens | "
              f"${self._total_cost_estimate:.4f} est. | {int(elapsed)}s")
        print(f"{'='*60}")

    def save_usage_log(self, filename=None):
        if not filename:
            filename = f"usage_{self._session_start.strftime('%Y%m%d_%H%M%S')}.json"
        path = PROJECT_ROOT / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "session": self._session_start.isoformat(),
                "calls": self._call_count,
                "tokens": self._total_input_tokens + self._total_output_tokens,
                "cost": round(self._total_cost_estimate, 6),
                "log": self._usage_log,
            }, f, indent=2)
        print(f"  💾 Log: {filename}")

    def cleanup(self):
        for path, up in self._uploaded_files.items():
            try:
                genai.delete_file(up.name)
            except Exception:
                pass
        self._uploaded_files.clear()
