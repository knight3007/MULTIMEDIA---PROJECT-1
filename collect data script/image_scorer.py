from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


DEFAULT_SIGLIP_MODEL = "google/siglip2-so400m-patch16-384"
HF_CACHE_MODEL_DIR = Path.home() / ".cache" / "huggingface" / "hub" / "models--google--siglip2-so400m-patch16-384"


class ImageScoringError(Exception):
    pass


@dataclass(frozen=True)
class ScoreResult:
    image_path: Path
    score: float


def resolve_local_model_path(model_name_or_path: str) -> str:
    path = Path(model_name_or_path)
    if path.exists():
        return str(path)

    if model_name_or_path == DEFAULT_SIGLIP_MODEL and HF_CACHE_MODEL_DIR.exists():
        snapshots_dir = HF_CACHE_MODEL_DIR / "snapshots"
        snapshots = sorted(
            (candidate for candidate in snapshots_dir.iterdir() if candidate.is_dir()),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        for snapshot in snapshots:
            if (snapshot / "config.json").exists() and (snapshot / "model.safetensors").exists():
                return str(snapshot)

    return model_name_or_path


class SiglipImageScorer:
    def __init__(
        self,
        model_name_or_path: str = DEFAULT_SIGLIP_MODEL,
        device: str = "auto",
        dtype: str = "auto",
    ) -> None:
        import torch
        from transformers import AutoModel, AutoProcessor

        self.torch = torch
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ImageScoringError(
                "CUDA was requested, but this Python environment cannot use CUDA. "
                "Install a CUDA-enabled PyTorch build before using --siglip-device cuda."
            )
        self.dtype = self._resolve_dtype(dtype)
        self.model_path = resolve_local_model_path(model_name_or_path)
        self.processor = AutoProcessor.from_pretrained(self.model_path, local_files_only=True)
        self.model = AutoModel.from_pretrained(
            self.model_path,
            local_files_only=True,
            dtype=self.dtype,
        )
        self.model.to(self.device)
        self.model.eval()

    def _resolve_dtype(self, dtype: str):
        if dtype == "auto":
            return self.torch.float16 if self.device == "cuda" else self.torch.float32
        if dtype == "float16":
            return self.torch.float16
        if dtype == "bfloat16":
            return self.torch.bfloat16
        if dtype == "float32":
            return self.torch.float32
        raise ImageScoringError(f"unsupported dtype: {dtype}")

    def score(self, text: str, image_path: Path) -> float:
        return self.score_batch(text, [image_path])[0].score

    def score_batch(self, text: str, image_paths: list[Path]) -> list[ScoreResult]:
        if not image_paths:
            return []

        images = []
        for image_path in image_paths:
            try:
                with Image.open(image_path) as image:
                    images.append(image.convert("RGB").copy())
            except OSError as error:
                raise ImageScoringError(f"cannot open image for scoring: {image_path}") from error

        inputs = self.processor(
            text=[text],
            images=images,
            padding="max_length",
            return_tensors="pt",
        )
        inputs = {
            name: value.to(self.device) if hasattr(value, "to") else value
            for name, value in inputs.items()
        }

        with self.torch.no_grad():
            output = self.model(**inputs)
            scores = output.logits_per_text[0].detach().cpu().tolist()

        return [
            ScoreResult(image_path=image_path, score=float(score))
            for image_path, score in zip(image_paths, scores)
        ]
