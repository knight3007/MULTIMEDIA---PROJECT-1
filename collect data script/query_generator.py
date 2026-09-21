"""Lazy Qwen query generation and an inspectable, vocabulary-bound query cache."""
from __future__ import annotations

import gc
import hashlib
import json
import re
from pathlib import Path

from collector_common import PROJECT_ROOT, CollectionError

DEFAULT_QWEN_MODEL = "Qwen/Qwen3-1.7B"
DEFAULT_BATCH_SIZE = 2
DEFAULT_QUERY_CACHE = PROJECT_ROOT / "data" / "query" / "generated_qwen.json"
MAX_NEW_TOKENS = 32
SYSTEM_PROMPT = """Turn one English vocabulary word into one concise image search query while preserving the exact referent.

The output must describe the same thing denoted by the input word. Choose one common everyday sense. Prefer a concrete physical noun sense when one exists. Avoid brands, companies, proper nouns, and computing senses when a common physical meaning exists.

For a concrete noun, output the input word exactly once followed by exactly one broad semantic class that answers what kind of thing the input itself is. Choose a class such as animal, bird, insect, fruit, food, beverage, substance, vehicle, furniture, plant, organism, device, tool, clothing, jewelry, building, institution, place, container, timepiece, illumination, meal, season, event, or object. This short noun phrase is disambiguation because it still names the target.

Do not name something the target has, contains, causes, uses, does, or is found near. Never substitute a related object, part, effect, action, place, tool, environment, accessory, or infrastructure. That is association, not disambiguation.

Examples:
Input: pear
Query: pear fruit
Input: dog
Query: dog animal
Input: ant
Query: ant insect
Input: bus
Query: bus vehicle
Input: sofa
Query: sofa furniture
Input: juice
Query: juice beverage
Input: cheese
Query: cheese food
Input: moss
Query: moss organism
Input: autumn
Query: autumn season
Input: clock
Query: clock timepiece
Input: lamp
Query: lamp illumination
Input: tablet
Query: tablet device

If the input has no concrete noun sense, show a verb as a person doing the action, an adjective as a visible comparison, or a nonphysical concept as a familiar icon only as a last resort.
Return exactly one natural query of 1-12 lowercase English words. Use each word at most once. No punctuation, explanation, definition, alternatives, list, synonyms, enumeration, keyword stuffing, or arbitrary attributes.
"""




class QueryGenerationError(CollectionError):
    """A vocabulary, model, output, or query-cache error that the CLI can report."""


def normalize_query(text: str) -> str:
    """Normalize case and spacing, then enforce the production query contract."""
    if not isinstance(text, str) or not text.strip():
        raise QueryGenerationError("Qwen returned an empty or non-text query")
    # Multiple nonempty lines may be alternatives or explanations, not one query.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise QueryGenerationError(f"Qwen must return one query, not multiple lines: {text!r}")
    query = " ".join(lines[0].lower().split())
    if not re.fullmatch(r"[a-z]+(?: [a-z]+){0,11}", query):
        raise QueryGenerationError(f"Invalid Qwen query (expected 1-12 English words): {text!r}")
    words = query.split()
    if len(words) != len(set(words)):
        raise QueryGenerationError(f"Repeated words in Qwen query: {text!r}")
    if any(a == b + "s" or b == a + "s"
           for index, a in enumerate(words) for b in words[index + 1:]):
        raise QueryGenerationError(f"Singular/plural forms repeated in Qwen query: {text!r}")
    if set(words) & {"here", "you", "query"} or "search for" in query:
        raise QueryGenerationError(f"Qwen returned commentary instead of a query: {text!r}")
    if set(words) & {"show", "showing", "image", "meaning", "verb", "visual", "evidence", "concept"}:
        raise QueryGenerationError(f"Qwen returned meta text instead of concrete search terms: {text!r}")
    if words[-1] in {"thing", "things", "situation", "situations"}:
        raise QueryGenerationError(f"Qwen returned a vague query: {text!r}")
    return query


class QwenQueryGenerator:
    def __init__(self, model_name: str = DEFAULT_QWEN_MODEL, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        if batch_size < 1:
            raise QueryGenerationError("Qwen batch size must be at least 1")
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.tokenizer = None
        self.torch = None

    def _load(self) -> None:
        if self.model is not None:
            return
        stage = "dependencies (torch, transformers, accelerate)"
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self.torch = torch
            stage = "tokenizer"
            print(f"[QWEN] loading {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, padding_side="left")
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            stage = "model with automatic CUDA/CPU placement"
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, device_map="auto",
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            self.model.eval()
        except Exception as error:
            self.close()
            raise QueryGenerationError(f"Qwen {stage} load failed ({self.model_name}): {error}") from error

    def _input_device(self):
        embeddings = self.model.get_input_embeddings()
        # Offloaded embeddings can have meta weights; Accelerate's hook knows
        # the execution device on which those weights will be materialized.
        for module in (embeddings, self.model):
            hook = getattr(module, "_hf_hook", None)
            execution_device = getattr(hook, "execution_device", None)
            if execution_device is not None:
                return execution_device
        device = embeddings.weight.device
        if device.type == "meta":
            raise QueryGenerationError("Cannot resolve Qwen input execution device for offloaded embeddings")
        return device

    def generate(self, word: str) -> str:
        return self.generate_batch([word])[0]

    def generate_batch(self, words: list[str]) -> list[str]:
        if any(not isinstance(word, str) or not word.strip() for word in words):
            raise QueryGenerationError("Qwen requires a nonempty English word")
        if not words:
            return []
        self._load()
        queries = []
        for start in range(0, len(words), self.batch_size):
            batch = words[start:start + self.batch_size]
            try:
                queries.extend(self._generate_chunk(batch))
            except QueryGenerationError:
                raise
            except Exception as error:
                raise QueryGenerationError(
                    f"Qwen inference failed for {batch[0]!r} (batch size {len(batch)}); "
                    f"check CUDA/CPU memory or lower --qwen-batch-size: {error}"
                ) from error
        return queries

    def _generate_chunk(self, words: list[str]) -> list[str]:
        raw_outputs = self._generate_raw(words)
        queries = []
        for word, (text, ended) in zip(words, raw_outputs):
            for attempt in range(2):
                try:
                    if not ended:
                        raise QueryGenerationError("query reached the token limit without EOS")
                    queries.append(normalize_query(text))
                    break
                except QueryGenerationError as error:
                    if attempt:
                        raise QueryGenerationError(
                            f"Qwen output for {word!r} after one retry: {error}"
                        ) from error
                    print(f"[QWEN] retry {word!r}: {error}")
                    correction = (
                        "The previous answer failed validation. Start over without copying it. "
                        "Preserve the input as the target. For a concrete noun, use the input "
                        "exactly once followed only by one broad semantic class. "
                        "Do not enumerate alternatives, synonyms, or related objects. Do not "
                        "repeat words or place singular and plural forms together; use no icon for a physical subject. "
                        "Output only lowercase English words."
                    )
                    text, ended = self._generate_raw([word], correction=correction)[0]
        return queries

    def _generate_raw(
        self, words: list[str], *, correction: str | None = None,
    ) -> list[tuple[str, bool]]:
        # Keep tensors scoped to this call so they are released before any retry.
        texts = []
        for word in words:
            user_content = f"Input: {word}"
            if correction:
                user_content += f"\n\n{correction}"
            user_content += "\nQuery:"
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
            texts.append(self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False,
            ))
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        device = self._input_device()
        inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
        eos_ids = self.model.generation_config.eos_token_id
        if eos_ids is None:
            eos_ids = self.tokenizer.eos_token_id
        if isinstance(eos_ids, int):
            eos_ids = [eos_ids]
        if not eos_ids:
            raise QueryGenerationError("Qwen tokenizer/model has no EOS token")
        eos_id_set = set(eos_ids)
        with self.torch.inference_mode():
            outputs = self.model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id, eos_token_id=eos_ids,
            )
        rows = outputs[:, inputs["input_ids"].shape[1]:].cpu().tolist()
        if len(rows) != len(words):
            raise QueryGenerationError("Qwen output count does not match input batch")
        return [
            (self.tokenizer.decode(tokens, skip_special_tokens=True), any(token in eos_id_set for token in tokens))
            for tokens in rows
        ]

    def close(self) -> None:
        """Release Qwen before the image phase can load SigLIP; safe to call twice."""
        self.model = None
        self.tokenizer = None
        gc.collect()
        if self.torch is not None and self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
        self.torch = None


def prepare_queries(
    words: list[str], *, limit: int,
    model_name: str = DEFAULT_QWEN_MODEL, batch_size: int = DEFAULT_BATCH_SIZE,
    cache_path: Path = DEFAULT_QUERY_CACHE,
) -> list[str]:
    """Persist a generated prefix, bound to the entire ordered vocabulary and prompt."""
    if limit < 1 or batch_size < 1:
        raise QueryGenerationError("Qwen limit and batch size must be at least 1")
    identity = json.dumps(
        [words, model_name, SYSTEM_PROMPT, MAX_NEW_TOKENS, False], ensure_ascii=False,
    ).encode("utf-8")
    signature = hashlib.sha256(identity).hexdigest()
    cache = {
        "version": 2, "model": model_name, "signature": signature,
        "vocabulary_count": len(words), "records": [],
    }
    if cache_path.exists():
        try:
            saved = json.loads(cache_path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict) or any(saved.get(key) != cache[key] for key in
                                                 ("version", "model", "signature", "vocabulary_count")):
                raise QueryGenerationError("vocabulary, model, or prompt changed")
            records = saved.get("records")
            if not isinstance(records, list) or len(records) > len(words):
                raise QueryGenerationError("invalid cached record count")
            for index, record in enumerate(records):
                if not isinstance(record, dict) or record.get("word") != words[index]:
                    raise QueryGenerationError(f"record {index + 1} is not aligned")
                if normalize_query(record.get("query")) != record["query"]:
                    raise QueryGenerationError(f"record {index + 1} has a noncanonical query")
            cache = saved
        except (OSError, UnicodeError, ValueError, QueryGenerationError) as error:
            raise QueryGenerationError(
                f"Invalid Qwen query cache {cache_path}: {error}. "
                "Move it aside or choose a new --qwen-cache path to regenerate."
            ) from error
    records = cache["records"]
    count = min(limit, len(words))
    print(f"[QWEN] cache reuse: {min(len(records), count)}/{count} queries")
    if len(records) < count:
        generator = QwenQueryGenerator(model_name, batch_size=batch_size)
        try:
            for start in range(len(records), count, batch_size):
                batch = words[start:min(start + batch_size, count)]
                queries = generator.generate_batch(batch)
                if len(queries) != len(batch):
                    raise QueryGenerationError("Qwen output count does not match requested batch")
                normalized = [normalize_query(query) for query in queries]
                records.extend({"word": word, "query": generated_query}
                               for word, generated_query in zip(batch, normalized))
                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
                    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    temporary.replace(cache_path)
                except OSError as error:
                    raise QueryGenerationError(f"Cannot save Qwen query cache {cache_path}: {error}") from error
                print(f"[QWEN] prepared {len(records)}/{count} queries")
        finally:
            generator.close()
    return [record["query"] for record in records[:count]]
