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
```

Arguments:

- `audio_files`: one or more paths to local audio files.
- `--api-key API_KEY`: AssemblyAI API key.
- `--base-url BASE_URL`: override the API base URL. Default: `https://api.assemblyai.com`
- `--eu`: use the EU AssemblyAI endpoint.
- `--model MODEL`: repeat to provide multiple speech models. Default models: `universal-3-pro`, `universal-2`
- `--no-speaker-labels`: disable speaker diarization (enabled by default).
- `--no-language-detection`: disable automatic language detection (enabled by default).
- `--poll-interval SECONDS`: seconds between polling attempts. Default: `3.0`
- `-o OUTPUT`, `--output OUTPUT`: write transcript(s). With one input file, this is the output file path (default: `AUDIO_FILE.txt`). With multiple input files, this must be a directory; each transcript is saved as `BASENAME.txt` inside it.

Help:

```bash
assemblyai_transcribe --help
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
