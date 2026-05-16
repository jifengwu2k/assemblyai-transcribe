#!/usr/bin/env python
# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""AssemblyAI CLI using only the Python standard library.

Run with:
    python -m assemblyai_transcribe AUDIO_FILE [AUDIO_FILE ...] --api-key YOUR_API_KEY -o transcript.txt
"""

from __future__ import print_function

import argparse
import io
import json
import os
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
        description="Upload local audio file(s) to AssemblyAI and save the transcript(s).",
    )
    parser.add_argument("audio_files", nargs="+", help="Path(s) to local audio file(s)")
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
        "--no-speaker-labels",
        action="store_false",
        dest="speaker_labels",
        default=True,
        help="Disable speaker diarization (enabled by default)",
    )
    parser.add_argument(
        "--no-language-detection",
        dest="language_detection",
        action="store_false",
        default=True,
        help="Disable automatic language detection (enabled by default)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=3.0,
        help="Seconds between polling attempts (default: 3.0)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Write transcript(s). With one input file, this is the output path "
            "(default: AUDIO_FILE.txt). With multiple input files, this is a "
            "directory (created if needed); each transcript is saved as "
            "BASENAME.txt inside it."
        ),
    )
    return parser


def parse_args(argv=None):
    # type: (Optional[List[str]]) -> argparse.Namespace
    parser = build_parser()
    args = parser.parse_args(argv)
    args.models = args.models or list(DEFAULT_SPEECH_MODELS)
    return args


def make_json_request(method, url, api_key, payload=None, timeout=None):
    # type: (str, str, str, Optional[Dict[str, Any]], Optional[float]) -> Dict[str, Any]
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


def upload_file(audio_path, base_url, api_key, timeout=None):
    # type: (str, str, str, Optional[float]) -> str
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
    timeout=None,
):
    # type: (str, str, str, List[str], bool, bool, Optional[float]) -> str
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


def poll_transcript(transcript_id, base_url, api_key, poll_interval, timeout=None):
    # type: (str, str, str, float, Optional[float]) -> Dict[str, Any]
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


def format_transcript_output(transcript, speaker_labels):
    # type: (Dict[str, Any], bool) -> str
    if speaker_labels:
        utterances = transcript.get("utterances") or []
        lines = []
        for utterance in utterances:
            speaker = utterance.get("speaker", "?")
            text = utterance.get("text", "")
            lines.append("Speaker %s: %s" % (speaker, text))
        return "\n".join(lines)

    return transcript.get("text", "")



def write_output_text(output_text, output_path):
    # type: (str, str) -> None
    try:
        with io.open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(output_text)
            output_file.write(u"\n")
    except (IOError, OSError) as exc:
        raise AssemblyAIError("Cannot write output file %s: %s" % (output_path, exc))



def output_path(input_file, output_arg):
    # type: (str, Optional[str]) -> str
    """Determine output file path for a single input file."""
    if output_arg is None:
        return input_file + ".txt"
    if os.path.isdir(output_arg):
        base = os.path.splitext(os.path.basename(input_file))[0]
        return os.path.join(output_arg, base + ".txt")
    return output_arg


def ensure_dir_for_file(file_path):
    # type: (str) -> None
    """Create parent directories for *file_path* if they don't exist."""
    parent = os.path.dirname(file_path)
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent)
        except (IOError, OSError) as exc:
            raise AssemblyAIError(
                "Cannot create output directory %s: %s" % (parent, exc)
            )


def run_transcribe(args):
    # type: (argparse.Namespace) -> int
    base_url = EU_BASE_URL if args.eu else args.base_url
    audio_files = args.audio_files  # type: List[str]

    # When --output is given with multiple files, treat it as a directory
    # and create it if it doesn't exist.
    if args.output is not None and len(audio_files) > 1:
        if not os.path.isdir(args.output):
            try:
                os.makedirs(args.output)
            except (IOError, OSError) as exc:
                eprint("Error: cannot create output directory %s: %s" % (args.output, exc))
                return 1

    try:
        for audio_file in audio_files:
            eprint("--- Processing: %s ---" % audio_file)
            eprint("Uploading: %s" % audio_file)
            upload_url = upload_file(audio_file, base_url, args.api_key)

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
            )

            eprint("Transcript ID: %s" % transcript_id)
            transcript = poll_transcript(
                transcript_id=transcript_id,
                base_url=base_url,
                api_key=args.api_key,
                poll_interval=args.poll_interval,
            )

            output_text = format_transcript_output(transcript, args.speaker_labels)
            out_path = output_path(audio_file, args.output)
            ensure_dir_for_file(out_path)
            write_output_text(output_text, out_path)
            eprint("Wrote transcript to: %s" % out_path)

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
