# assemblyai-transcribe

Small CLI for uploading local audio file(s) to AssemblyAI and saving the transcript(s).

The code is compatible with Python 2.7 and Python 3.x.

## Installation

Install from PyPI:

```bash
pip install assemblyai-transcribe
```
After installation, run it as `assemblyai_transcribe`.

## Usage

Transcribe a single file:

```bash
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY -o transcript.txt
```

Transcribe multiple files:

```bash
assemblyai_transcribe ./ep1.mp3 ./ep2.mp3 ./ep3.mp3 --api-key YOUR_API_KEY
# Saves: ep1.mp3.txt, ep2.mp3.txt, ep3.mp3.txt
```

Transcribe multiple files into a directory (auto-created if it doesn't exist):

```bash
assemblyai_transcribe ./ep1.mp3 ./ep2.mp3 --api-key YOUR_API_KEY -o transcripts/
# Saves: transcripts/ep1.txt, transcripts/ep2.txt
```

Examples:

```bash
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --eu -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro --model universal-2 -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --no-language-detection -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --no-speaker-labels -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --language zh -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --language zh --language en -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --language zh,en --code-switching -o transcript.txt
```

Arguments:

- `audio_files`: one or more paths to local audio files.
- `--api-key API_KEY`: AssemblyAI API key.
- `--base-url BASE_URL`: override the API base URL. Default: `https://api.assemblyai.com`
- `--eu`: use the EU AssemblyAI endpoint.
- `--model MODEL`: repeat to provide multiple speech models. Default models: `universal-3-pro`, `universal-2`
- `--language LANG`: expected language as an ISO code. Repeat the flag for several languages, or pass a comma-separated list (`--language zh,en`).
  - one language (e.g. `--language zh`): transcription is forced into that language;
  - two or more languages: automatic detection is restricted to them, with the first one as fallback;
  - omitted (default): automatic language detection over all languages, as before.
- `--code-switching`: allow a single recording to mix the `--language` values. Requires at least two `--language` values.
- `--no-speaker-labels`: disable speaker diarization (enabled by default).
- `--no-language-detection`: disable automatic language detection (enabled by default). Cannot be combined with multiple `--language` values.
- `--poll-interval SECONDS`: seconds between polling attempts. Default: `3.0`
- `-o OUTPUT`, `--output OUTPUT`: write transcript(s). With one input file, this is the output file path (default: `AUDIO_FILE.txt`). With multiple input files, this must be a directory; each transcript is saved as `BASENAME.txt` inside it.

Help:

```bash
assemblyai_transcribe --help
```

## Mixed-language recordings

By default the CLI leaves language handling to AssemblyAI, which is the right choice
for most files. Two things are worth knowing when a recording switches languages.

**1. The detected language is chosen per file, not per sentence.** If a long recording
is mostly English with a Chinese section at the end, plain automatic detection can
drop the minority-language section entirely (it is transcribed as nothing rather than
as the wrong language). Tell the CLI about both languages instead:

```bash
assemblyai_transcribe ./episode.m4a --api-key YOUR_API_KEY \
    --language zh --language en --code-switching -o transcript.txt
```

**2. Detection still prefers the dominant language.** Restricting detection to a list
helps, but the whole file is still classified as one language. If a minority-language
stretch is being lost, either force that language for the specific file/segment:

```bash
assemblyai_transcribe ./chinese-segment.m4a --api-key YOUR_API_KEY --language zh -o zh.txt
```

or cut the recording into stretches per language (`ffmpeg -ss/-t`) and transcribe each
one, then stitch the results together. The `Language:` line printed on stderr shows
which strategy was used for each file.

## Development

```bash
python -m unittest discover -s tests
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
