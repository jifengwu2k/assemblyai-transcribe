# assemblyai-transcribe

Small CLI for uploading a local audio file to AssemblyAI and printing the transcript.

The code is compatible with Python 2.7 and Python 3.x.

## Installation

Install from PyPI:

```bash
pip install assemblyai-transcribe
```

## Usage

Run the module directly:

```bash
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY
```

Examples:

```bash
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --eu
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro --model universal-2
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --language-detection
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --speaker-labels
python -m assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY > transcript.txt
```

Arguments:

- `audio_file`: path to the local audio file.
- `--api-key API_KEY`: AssemblyAI API key.
- `--base-url BASE_URL`: override the API base URL. Default: `https://api.assemblyai.com`
- `--eu`: use the EU AssemblyAI endpoint.
- `--model MODEL`: repeat to provide multiple speech models. Default models: `universal-3-pro`, `universal-2`
- `--speaker-labels`: enable speaker diarization and print utterances after the transcript.
- `--language-detection` or `--language_detection`: enable automatic language detection.
- `--poll-interval SECONDS`: seconds between polling attempts. Default: `3.0`
- `--timeout SECONDS`: HTTPS timeout in seconds. Default: `30.0`

Help:

```bash
python -m assemblyai_transcribe --help
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
