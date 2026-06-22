"""Single-file inference helper — the entry point the agent's STT tool will call.

CLI:
    python -m src.transcribe --model.name ./outputs/whisper-small-darija \
        --audio path/to/clip.wav

Library:
    from src.transcribe import WhisperTranscriber
    tr = WhisperTranscriber("./outputs/whisper-small-darija")
    print(tr.transcribe("clip.wav"))
"""
from __future__ import annotations

import argparse

import torch


class WhisperTranscriber:
    """Loads a Whisper checkpoint once and transcribes audio files/arrays."""

    def __init__(
        self,
        model_name: str,
        language: str = "arabic",
        task: str = "transcribe",
        device: str | None = None,
        num_beams: int = 1,
    ) -> None:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.language = language
        self.task = task
        self.num_beams = num_beams
        self.processor = WhisperProcessor.from_pretrained(
            model_name, language=language, task=task
        )
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device).eval()

    def _load_audio(self, path: str, target_sr: int = 16000):
        import librosa

        audio, _ = librosa.load(path, sr=target_sr, mono=True)
        return audio

    def transcribe(self, audio, sampling_rate: int = 16000) -> str:
        """`audio` is a file path (str) or a 1-D float array at `sampling_rate`."""
        if isinstance(audio, str):
            audio = self._load_audio(audio)
            sampling_rate = 16000

        inputs = self.processor.feature_extractor(
            audio, sampling_rate=sampling_rate, return_tensors="pt"
        ).input_features.to(self.device)

        with torch.no_grad():
            generated = self.model.generate(
                inputs, language=self.language, task=self.task, max_length=225,
                num_beams=self.num_beams,
            )
        return self.processor.batch_decode(
            generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--model.name", dest="model_name", required=True)
    parser.add_argument("--audio", required=True, help="Path to an audio file.")
    parser.add_argument("--language", default="arabic")
    parser.add_argument("--task", default="transcribe")
    parser.add_argument("--num_beams", type=int, default=5,
                        help="Beam search width (1 = greedy).")
    args = parser.parse_args()

    tr = WhisperTranscriber(args.model_name, language=args.language, task=args.task,
                            num_beams=args.num_beams)
    print(tr.transcribe(args.audio))


if __name__ == "__main__":
    main()
