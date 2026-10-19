#!/usr/bin/env python
"""Tests for the --language / --code-switching CLI options.

Run with:  python -m unittest discover -s tests
"""

from __future__ import print_function

import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import assemblyai_transcribe as cli  # noqa: E402


class LanguageRequestTests(unittest.TestCase):
    """Unit tests for build_language_request()."""

    def test_default_is_automatic_detection(self):
        fields, description = cli.build_language_request([], True, False)
        self.assertEqual(fields, {"language_detection": True})
        self.assertEqual(description, "automatic detection")

    def test_detection_disabled(self):
        fields, _ = cli.build_language_request([], False, False)
        self.assertEqual(fields, {"language_detection": False})

    def test_single_language_forces_language_code(self):
        fields, description = cli.build_language_request(["zh"], True, False)
        self.assertEqual(fields, {"language_code": "zh", "language_detection": False})
        self.assertEqual(description, "forced to zh")

    def test_multiple_languages_use_expected_languages(self):
        fields, description = cli.build_language_request(["zh", "en"], True, False)
        self.assertEqual(
            fields,
            {
                "language_detection": True,
                "language_detection_options": {
                    "expected_languages": ["zh", "en"],
                    "fallback_language": "zh",
                },
            },
        )
        self.assertEqual(description, "detection limited to zh, en")

    def test_code_switching_adds_option(self):
        fields, description = cli.build_language_request(["zh", "en"], True, True)
        self.assertTrue(fields["language_detection_options"]["code_switching"])
        self.assertEqual(description, "detection limited to zh, en with code switching")


class ArgumentParsingTests(unittest.TestCase):
    """Unit tests for normalize_languages() and argument validation."""

    def test_normalize_flattens_and_dedupes(self):
        self.assertEqual(
            cli.normalize_languages(["zh,en", " en ", "zh", "fr"]),
            ["zh", "en", "fr"],
        )

    def test_normalize_handles_empty(self):
        self.assertEqual(cli.normalize_languages(None), [])
        self.assertEqual(cli.normalize_languages(["", " , "]), [])

    def test_code_switching_requires_two_languages(self):
        with self.assertRaises(SystemExit) as ctx:
            cli.parse_args(["a.mp3", "--api-key", "k", "--code-switching", "--language", "zh"])
        self.assertEqual(ctx.exception.code, 2)

    def test_multiple_languages_conflict_with_disabled_detection(self):
        with self.assertRaises(SystemExit) as ctx:
            cli.parse_args(
                ["a.mp3", "--api-key", "k", "--no-language-detection",
                 "--language", "zh", "--language", "en"]
            )
        self.assertEqual(ctx.exception.code, 2)


class PayloadTests(unittest.TestCase):
    """End-to-end (offline) check of the request payload sent to AssemblyAI."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.payloads = []
        self._orig = (
            cli.upload_file,
            cli.make_json_request,
            cli.poll_transcript,
        )

        def fake_upload(audio_path, base_url, api_key, timeout=None):
            return "https://example.invalid/upload"

        def fake_json_request(method, url, api_key, payload=None, timeout=None):
            self.payloads.append(payload)
            if method == "POST":
                return {"id": "transcript-id"}
            return {"status": "completed", "text": "hello", "utterances": []}

        cli.upload_file = fake_upload
        cli.make_json_request = fake_json_request
        cli.poll_transcript = lambda *a, **kw: {
            "status": "completed",
            "text": "hello",
            "utterances": [],
        }

    def tearDown(self):
        cli.upload_file, cli.make_json_request, cli.poll_transcript = self._orig
        shutil.rmtree(self.tmpdir)

    def run_cli(self, *argv):
        audio = os.path.join(self.tmpdir, "a.mp3")
        open(audio, "w").close()
        output = os.path.join(self.tmpdir, "out.txt")
        args = cli.parse_args([audio, "--api-key", "k", "-o", output] + list(argv))
        self.assertEqual(cli.run_transcribe(args), 0)
        with io.open(output, encoding="utf-8") as handle:
            return handle.read(), self.payloads[-1]

    def test_default_payload_unchanged(self):
        _, payload = self.run_cli()
        self.assertEqual(
            sorted(payload),
            ["audio_url", "language_detection", "speaker_labels", "speech_models"],
        )
        self.assertTrue(payload["language_detection"])
        self.assertNotIn("language_detection_options", payload)
        self.assertNotIn("language_code", payload)

    def test_forced_language_payload(self):
        _, payload = self.run_cli("--language", "zh")
        self.assertEqual(payload["language_code"], "zh")
        self.assertFalse(payload["language_detection"])

    def test_two_languages_payload(self):
        _, payload = self.run_cli("--language", "zh,en")
        self.assertEqual(
            payload["language_detection_options"]["expected_languages"], ["zh", "en"]
        )
        self.assertEqual(payload["language_detection_options"]["fallback_language"], "zh")
        self.assertNotIn("code_switching", payload["language_detection_options"])

    def test_code_switching_payload(self):
        _, payload = self.run_cli("--language", "zh", "--language", "en", "--code-switching")
        self.assertTrue(payload["language_detection_options"]["code_switching"])

    def test_disabled_detection_payload(self):
        _, payload = self.run_cli("--no-language-detection")
        self.assertFalse(payload["language_detection"])


if __name__ == "__main__":
    unittest.main()
