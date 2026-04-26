# assemblyai-transcribe

Small CLI for uploading a local audio file to AssemblyAI and saving the transcript.

The code is compatible with Python 2.7 and Python 3.x.

## Installation

Install from PyPI:

```bash
pip install assemblyai-transcribe
```
After installation, run it as `assemblyai_transcribe`.

## Usage

Run the installed command directly:

```bash
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY -o transcript.txt
```

Examples:

```bash
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --eu -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --model universal-3-pro --model universal-2 -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --language-detection -o transcript.txt
assemblyai_transcribe ./example.mp3 --api-key YOUR_API_KEY --speaker-labels -o transcript.txt
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
- `-o OUTPUT`, `--output OUTPUT`: required. Write the transcript to a file.
- `--timeout SECONDS`: HTTPS timeout in seconds. Default: `30.0`

Help:

```bash
assemblyai_transcribe --help
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
