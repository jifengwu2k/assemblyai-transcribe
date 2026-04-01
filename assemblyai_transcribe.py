#!/usr/bin/env python
# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""AssemblyAI CLI using only the Python standard library.

Run with:
    python -m assemblyai_transcribe AUDIO_FILE --api-key YOUR_API_KEY
"""

from __future__ import print_function

import argparse
import json
import sys
import time

from typing import Any, Dict, List, Optional

if sys.version_info[0] >= 3:
    from http.client import HTTPSConnection
    from urllib.parse import urlparse
else:
    from httplib import HTTPSConnection
    from urlparse import urlparse

DEFAULT_BASE_URL = "https://api.assemblyai.com"
EU_BASE_URL = "https://api.eu.assemblyai.com"
DEFAULT_SPEECH_MODELS = ["universal-3-pro", "universal-2"]


class AssemblyAIError(Exception):
    __slots__ = ()


def eprint(message):
    # type: (str) -> None
    print(message, file=sys.stderr)


def build_parser():
    # type: () -> argparse.ArgumentParser
    parser = argparse.ArgumentParser(
        description="Upload a local audio file to AssemblyAI and print the transcript.",
    )
    parser.add_argument("audio_file", help="Path to the local audio file")
    parser.add_argument(
        "--api-key",
        required=True,
        help="AssemblyAI API key",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="AssemblyAI API base URL (default: %s)" % DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "--eu",
        action="store_true",
        help="Use the EU data residency endpoint",
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help=(
            "Speech model to use. Repeat this flag to provide multiple models. "
            "Default: %s"
        ) % ", ".join(DEFAULT_SPEECH_MODELS),
    )
    parser.add_argument(
        "--speaker-labels",
        action="store_true",
        help="Enable speaker diarization and print utterances",
    )
    parser.add_argument(
        "--language-detection",
        "--language_detection",
        dest="language_detection",
        action="store_true",
        help="Enable automatic language detection",
    )
    parser.add_argument(
        "--poll-interval",
        default="3.0",
        help="Seconds between polling attempts (default: 3.0)",
    )
    parser.add_argument(
        "--timeout",
        default="30.0",
        help="HTTPS connection timeout in seconds (default: 30.0)",
    )
    return parser


def parse_positive_float_argument(parser, option_name, option_value):
    # type: (argparse.ArgumentParser, str, str) -> float
    try:
        parsed_value = float(option_value)
    except ValueError:
        parser.error("%s must be a number: %s" % (option_name, option_value))

    if parsed_value <= 0.0:
        parser.error("%s must be greater than 0: %s" % (option_name, option_value))

    return parsed_value


def parse_args(argv=None):
    # type: (Optional[List[str]]) -> argparse.Namespace
    parser = build_parser()
    args = parser.parse_args(argv)
    args.models = args.models or list(DEFAULT_SPEECH_MODELS)
    args.poll_interval = parse_positive_float_argument(
        parser, "--poll-interval", args.poll_interval
    )
    args.timeout = parse_positive_float_argument(parser, "--timeout", args.timeout)
    return args


def make_json_request(method, url, api_key, payload=None, timeout=30.0):
    # type: (str, str, str, Optional[Dict[str, Any]], float) -> Dict[str, Any]
    parsed = urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path = "%s?%s" % (path, parsed.query)

    body = None  # type: Optional[bytes]
    headers = {
        "authorization": api_key,
        "accept": "application/json",
    }
    if payload is not None:
        body_text = json.dumps(payload)
        if sys.version_info[0] >= 3:
            body = body_text.encode("utf-8")
        else:
            body = body_text
        headers["content-type"] = "application/json"
        headers["content-length"] = str(len(body))

    conn = HTTPSConnection(parsed.netloc, timeout=timeout)
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        return parse_json_response(response)
    finally:
        conn.close()


def parse_json_response(response):
    # type: (Any) -> Dict[str, Any]
    raw_body = response.read()
    if sys.version_info[0] >= 3 and isinstance(raw_body, bytes):
        text_body = raw_body.decode("utf-8", "replace")
    else:
        text_body = raw_body

    try:
        data = json.loads(text_body) if text_body else {}
    except ValueError:
        raise AssemblyAIError(
            "Unexpected non-JSON response (%s): %s" % (response.status, text_body)
        )

    if response.status < 200 or response.status >= 300:
        if isinstance(data, dict):
            message = data.get("error", text_body)
        else:
            message = text_body
        raise AssemblyAIError("HTTP %s: %s" % (response.status, message))

    if not isinstance(data, dict):
        raise AssemblyAIError("Unexpected response payload: %r" % (data,))
    return data


def upload_file(audio_path, base_url, api_key, timeout):
    # type: (str, str, str, float) -> str
    parsed = urlparse(base_url)
    upload_path = "/v2/upload"

    try:
        with open(audio_path, "rb") as audio_file:
            audio_file.seek(0, 2)
            file_size = audio_file.tell()
            audio_file.seek(0)

            headers = {
                "authorization": api_key,
                "content-length": str(file_size),
                "content-type": "application/octet-stream",
                "accept": "application/json",
            }

            conn = HTTPSConnection(parsed.netloc, timeout=timeout)
            try:
                conn.putrequest("POST", upload_path)
                for key in headers:
                    conn.putheader(key, headers[key])
                conn.endheaders()

                while True:
                    chunk = audio_file.read(1024 * 1024)
                    if not chunk:
                        break
                    conn.send(chunk)

                response = conn.getresponse()
                data = parse_json_response(response)
            finally:
                conn.close()
    except (IOError, OSError) as exc:
        raise AssemblyAIError("Cannot open audio file %s: %s" % (audio_path, exc))

    upload_url = data.get("upload_url")
    if not upload_url:
        raise AssemblyAIError(
            "Upload succeeded but no upload_url returned: %s" % (data,)
        )
    return upload_url


def submit_transcription(
    audio_url,
    base_url,
    api_key,
    speech_models,
    speaker_labels,
    language_detection,
    timeout,
):
    # type: (str, str, str, List[str], bool, bool, float) -> str
    payload = {
        "audio_url": audio_url,
        "speech_models": speech_models,
        "language_detection": language_detection,
        "speaker_labels": speaker_labels,
    }
    data = make_json_request(
        "POST",
        "%s/v2/transcript" % base_url,
        api_key,
        payload=payload,
        timeout=timeout,
    )
    transcript_id = data.get("id")
    if not transcript_id:
        raise AssemblyAIError(
            "Transcription request succeeded but no transcript id returned: %s"
            % (data,)
        )
    return transcript_id


def poll_transcript(transcript_id, base_url, api_key, poll_interval, timeout):
    # type: (str, str, str, float, float) -> Dict[str, Any]
    polling_url = "%s/v2/transcript/%s" % (base_url, transcript_id)
    while True:
        data = make_json_request("GET", polling_url, api_key, timeout=timeout)
        status = data.get("status")
        if status == "completed":
            return data
        if status == "error":
            raise AssemblyAIError(
                "Transcription failed: %s" % data.get("error", "unknown error")
            )
        eprint("Status: %s; waiting %ss..." % (status or "unknown", poll_interval))
        time.sleep(poll_interval)


def run_transcribe(args):
    # type: (argparse.Namespace) -> int
    base_url = EU_BASE_URL if args.eu else args.base_url

    try:
        eprint("Uploading: %s" % args.audio_file)
        upload_url = upload_file(args.audio_file, base_url, args.api_key, args.timeout)

        eprint(
            "Submitting transcription request with models: %s"
            % ", ".join(args.models)
        )
        transcript_id = submit_transcription(
            audio_url=upload_url,
            base_url=base_url,
            api_key=args.api_key,
            speech_models=args.models,
            speaker_labels=args.speaker_labels,
            language_detection=args.language_detection,
            timeout=args.timeout,
        )

        eprint("Transcript ID: %s" % transcript_id)
        transcript = poll_transcript(
            transcript_id=transcript_id,
            base_url=base_url,
            api_key=args.api_key,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

        if args.speaker_labels:
            utterances = transcript.get("utterances") or []
            for utterance in utterances:
                speaker = utterance.get("speaker", "?")
                text = utterance.get("text", "")
                print("Speaker %s: %s" % (speaker, text))
        else:
            print(transcript.get("text", ""))

        return 0
    except AssemblyAIError as exc:
        eprint("Error: %s" % exc)
        return 1
    except KeyboardInterrupt:
        eprint("Interrupted.")
        return 130


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    args = parse_args(argv)
    return run_transcribe(args)


if __name__ == "__main__":
    sys.exit(main())
