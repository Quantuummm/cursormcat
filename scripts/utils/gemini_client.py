"""
Gemini API client wrapper with rate limiting, JSON mode, and retry logic.
Handles all communication with Google's Gemini 2.0 Flash model.
"""

import json
import time
import google.generativeai as genai
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE_EXTRACT,
    GEMINI_TEMPERATURE_RESTRUCTURE,
    GEMINI_TEMPERATURE_ENRICH,
    GEMINI_DELAY_BETWEEN_REQUESTS,
)


class GeminiClient:
    """
    Wrapper around the Gemini API with:
    - Automatic JSON mode (response_mime_type="application/json")
    - Rate limiting (respects free tier: 15 RPM)
    - Retry on failures with exponential backoff
    - PDF upload support
    - Temperature presets for extraction vs restructuring
    """

    # Temperature presets
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
        self._uploaded_files = {}  # Cache uploaded files by path

    def _get_model(self, temperature: float):
        """Create a Gemini model instance with JSON output mode."""
        return genai.GenerativeModel(
            GEMINI_MODEL,
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

    def upload_pdf(self, pdf_path: str | Path) -> object:
        """
        Upload a PDF to Gemini's file API (required for PDF reading).
        Caches uploads so the same PDF isn't uploaded twice.
        """
        pdf_path = str(pdf_path)
        if pdf_path in self._uploaded_files:
            return self._uploaded_files[pdf_path]

        print(f"  📤 Uploading PDF: {Path(pdf_path).name}...")
        uploaded = genai.upload_file(pdf_path)

        # Wait for file to be processed
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)

        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"PDF upload failed. State: {uploaded.state.name}")

        self._uploaded_files[pdf_path] = uploaded
        print(f"  ✅ PDF uploaded and ready")
        return uploaded

    def extract(self, prompt: str, pdf_file=None, max_retries: int = 3) -> dict:
        """
        Send an extraction prompt to Gemini. Returns parsed JSON.

        Args:
            prompt: The extraction prompt text
            pdf_file: Optional uploaded PDF file object (from upload_pdf)
            max_retries: Number of retries on failure

        Returns:
            Parsed JSON dict from Gemini's response
        """
        return self._call(prompt, pdf_file, self.TEMP_EXTRACT, max_retries)

    def restructure(self, prompt: str, max_retries: int = 3) -> dict:
        """Send a restructuring prompt (higher temperature for creative question wording)."""
        return self._call(prompt, None, self.TEMP_RESTRUCTURE, max_retries)

    def enrich(self, prompt: str, max_retries: int = 3) -> dict:
        """Send an enrichment prompt (moderate temperature)."""
        return self._call(prompt, None, self.TEMP_ENRICH, max_retries)

    def _call(self, prompt: str, pdf_file, temperature: float, max_retries: int) -> dict:
        """Internal: make a Gemini API call with retries and JSON parsing."""
        model = self._get_model(temperature)

        for attempt in range(max_retries):
            try:
                self._rate_limit()

                # Build content list
                content = []
                if pdf_file:
                    content.append(pdf_file)
                content.append(prompt)

                response = model.generate_content(content)

                # Parse JSON response
                result = json.loads(response.text)
                return result

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Try to clean the response and parse again
                    text = response.text.strip()
                    # Sometimes Gemini wraps JSON in markdown code fences
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
