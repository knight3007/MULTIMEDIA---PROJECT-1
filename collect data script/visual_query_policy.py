"""Image pipeline v2 policy: word-type routing, query styling, technical rejection and selection proposal.

Derived from the owner-reviewed A-004R selection (see docs/IMAGE_PIPELINE_V2.md):
concrete nouns keep Qwen's "<word> <class>" photo query; actions, states and social words use a
descriptive "... icon" query; time and abstract words use a "... illustration" scene query;
connectors are never searched automatically (manual curation or NO_SUITABLE_IMAGE).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from query_generator import QueryGenerationError, normalize_query

POLICY_VERSION = "image-pipeline-v2"
WORD_TYPES = ("CONCRETE", "ACTION", "STATE", "SOCIAL", "TIME", "ABSTRACT", "CONNECTOR")
ROUTES = {"CONCRETE": "PHOTO", "ACTION": "ICON", "STATE": "ICON", "SOCIAL": "ICON",
          "TIME": "SCENE", "ABSTRACT": "SCENE", "CONNECTOR": "CURATE"}
SUFFIX = {"ICON": "icon", "SCENE": "illustration"}
# Tokens that caused brand/word collisions or sense drift in A-003/A-004R (Action store/rifles,
# "Being Single" quotes, "<word> object" posters). Allowed only in CONCRETE photo queries.
NON_PHOTO_BANNED = {"action", "object", "single", "logo", "brand", "word", "text", "letters"}
# Words normalize_query treats as meta text; stripped from descriptive queries instead of failing.
META_TOKENS = {"show", "showing", "image", "meaning", "verb", "visual", "evidence", "concept", "here", "you", "query"}
# A CONCRETE answer whose class is one of these is a misclassified verb/abstract noun -> corrective retry.
NON_PHYSICAL_CLASSES = {"action", "activity", "abstract", "abstraction", "organization", "concept", "process",
                        "idea", "quality", "feeling", "emotion", "state", "phenomenon", "verb", "adjective"}

TYPED_PROMPT = """Classify one English vocabulary word and write one image search query for a picture that teaches it to a language learner.

Answer in exactly this format: TYPE | query

TYPE is one of:
CONCRETE = any noun for something you can see or photograph. This includes every animal, food, meal, drink, plant, natural feature such as a river or lake, place, building, institution such as a school or bank, room, vehicle, device, tool, clothing, and every person: jobs, roles, and family members such as uncle or cousin.
ACTION = a verb, something a person does.
STATE = an adjective, feeling, or quality.
SOCIAL = a greeting, polite phrase, thanks, apology, question word, or a word about people being together.
TIME = a word for a day, a period, or how often something happens.
ABSTRACT = a noun for something you cannot touch, such as an activity, plan, field, or system.
CONNECTOR = a grammar word that links clauses, such as although, therefore, but, or if.
When a word is a noun you can see, always choose CONCRETE. A verb is never CONCRETE, and a noun you cannot touch is never CONCRETE.

Query rules:
CONCRETE: the word exactly once followed by one broad class, such as fruit, food, meal, drink, animal, plant, vehicle, building, place, device, clothing, person.
ACTION: a person doing exactly this action, ending with icon.
STATE: one simple visible sign of exactly this quality, ending with icon.
SOCIAL: a person gesture or a simple symbol for exactly this phrase, ending with icon.
TIME: a calendar page or a clock that shows exactly this time idea, ending with illustration.
ABSTRACT: one familiar everyday scene of exactly this concept, ending with illustration.
CONNECTOR: the query is none.
Describe the given word itself; do not reuse the example scenes. Use 2 to 8 lowercase English words. Never use the words action, object, single, logo, brand, word, text. No digits, no punctuation, no explanation.

Examples:
Input: pear
CONCRETE | pear fruit
Input: uncle
CONCRETE | uncle person
Input: pilot
CONCRETE | pilot person
Input: park
CONCRETE | park place
Input: lunch
CONCRETE | lunch meal
Input: cook
ACTION | person cooking food icon
Input: quiet
STATE | finger on lips quiet icon
Input: goodbye
SOCIAL | person waving goodbye icon
Input: who
SOCIAL | person silhouette with question mark icon
Input: run
ACTION | person running fast icon
Input: weekend
TIME | calendar with saturday sunday marked illustration
Input: often
TIME | clock with repeating arrows illustration
Input: holiday
ABSTRACT | family on beach vacation illustration
Input: although
CONNECTOR | none
"""


@dataclass(frozen=True)
class TypedQuery:
    word: str
    word_type: str
    route: str
    query: str | None  # None for CURATE


def parse_typed_output(word: str, text: str) -> TypedQuery:
    """Parse 'TYPE | query' and enforce the route's query style."""
    if not isinstance(text, str):
        raise QueryGenerationError("typed output is not text")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1 or lines[0].count("|") != 1:
        raise QueryGenerationError(f"expected 'TYPE | query', got {text!r}")
    raw_type, raw_query = (part.strip() for part in lines[0].split("|"))
    word_type = raw_type.upper()
    if word_type not in ROUTES:
        raise QueryGenerationError(f"unknown word type {raw_type!r}")
    route = ROUTES[word_type]
    if route == "CURATE":
        return TypedQuery(word, word_type, route, None)
    return TypedQuery(word, word_type, route, style_query(word, route, raw_query))


def _clean(text: str) -> list[str]:
    """Lowercase, turn "o'clock" into "clock", and drop tokens containing digits or other non-letters."""
    text = text.lower().replace("o'clock", "clock")
    return [t for t in (re.sub(r"[^a-z]", "", tok) if not re.search(r"\d", tok) else "" for tok in text.split()) if t]


def style_query(word: str, route: str, query: str) -> str:
    if route == "PHOTO":
        query = normalize_query(query)
        words = query.split()
        if word.lower() not in words or words[-1] in {"icon", "illustration"}:
            raise QueryGenerationError(f"concrete query must name the word and stay a photo query: {query!r}")
        if set(words[words.index(word.lower()) + 1:]) & NON_PHYSICAL_CLASSES:
            raise QueryGenerationError(f"{word!r} is not a physical noun ({query!r}); choose ACTION, STATE, SOCIAL, TIME or ABSTRACT")
        return query
    # Collision-prone and meta tokens, digits and punctuation are stripped (not fatal).
    suffix = SUFFIX[route]
    words = [w for w in _clean(query) if w not in NON_PHOTO_BANNED | META_TOKENS | {"icon", "illustration"}]
    seen = set()
    words = [w for w in words if not (w in seen or seen.add(w))] + [suffix]
    if len(words) < 2:
        raise QueryGenerationError(f"query too short: {query!r}")
    return normalize_query(" ".join(words))


def generate_typed_raw(generator, words: list[str], correction: str | None = None) -> list[tuple[str, bool]]:
    """Greedy Qwen generation with TYPED_PROMPT. Mirrors QwenQueryGenerator._generate_raw (whose source is
    hash-pinned by historical benchmarks and therefore not modified)."""
    texts = []
    for word in words:
        user = f"Input: {word}" + (f"\n\n{correction}" if correction else "")
        messages = [{"role": "system", "content": TYPED_PROMPT}, {"role": "user", "content": user}]
        texts.append(generator.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False))
    inputs = generator.tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=False)
    device = generator._input_device()
    inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
    eos_ids = generator.model.generation_config.eos_token_id or generator.tokenizer.eos_token_id
    eos_ids = [eos_ids] if isinstance(eos_ids, int) else list(eos_ids)
    with generator.torch.inference_mode():
        outputs = generator.model.generate(**inputs, max_new_tokens=TYPED_MAX_NEW_TOKENS, do_sample=False,
                                           pad_token_id=generator.tokenizer.pad_token_id, eos_token_id=eos_ids)
    rows = outputs[:, inputs["input_ids"].shape[1]:].cpu().tolist()
    return [(generator.tokenizer.decode(t, skip_special_tokens=True), any(x in set(eos_ids) for x in t)) for t in rows]


TYPED_MAX_NEW_TOKENS = 32


def classify_words(words: list[str], generator, raw_fn=None) -> list[TypedQuery]:
    """Run prompt v2 through a QwenQueryGenerator (lazy-loaded) with one corrective retry.
    `raw_fn(generator, words, correction)` is injectable for tests."""
    raw_fn = raw_fn or generate_typed_raw
    generator._load()
    results = []
    for start in range(0, len(words), generator.batch_size):
        batch = words[start:start + generator.batch_size]
        raw = raw_fn(generator, batch, None)
        for word, (text, ended) in zip(batch, raw):
            for attempt in range(2):
                try:
                    if not ended:
                        raise QueryGenerationError("typed output reached the token limit")
                    results.append(parse_typed_output(word, text))
                    break
                except QueryGenerationError as error:
                    if attempt:
                        raise QueryGenerationError(f"typed query for {word!r} failed after one retry: {error}") from error
                    correction = ("The previous answer was invalid. Answer exactly 'TYPE | query' following the rules. "
                                  f"Problem: {error}")
                    text, ended = raw_fn(generator, [word], correction)[0]
    return results


# ---------- candidate rejection and proposal ----------

MIN_SIDE_PX = 100
MIN_LUMA_STDDEV = 6.0
CHECKERBOARD_MIN = 0.2


def technical_rejection(jpeg_path: Path) -> str | None:
    """Reason a normalized candidate is technically unusable, or None. Semantic checks stay with the reviewer."""
    from PIL import Image, ImageStat
    with Image.open(jpeg_path) as image:
        if min(image.size) < MIN_SIDE_PX:
            return f"too small ({image.width}x{image.height})"
        grey = image.convert("L")
        stat = ImageStat.Stat(grey)
        if stat.stddev[0] < MIN_LUMA_STDDEV:
            return f"near-uniform image (mean {stat.mean[0]:.0f}, stddev {stat.stddev[0]:.1f})"
        if checkerboard_score(grey) > CHECKERBOARD_MIN:
            return "baked-in checkerboard transparency pattern"
    return None


def checkerboard_score(grey) -> float:
    """Evidence of a baked-in 'transparency' checkerboard: two light grey levels that both cover much of
    the image and alternate along rows AND columns. Returns 0..1 (min of row/column alternation density)."""
    small = grey.copy()
    small.thumbnail((256, 256))
    width, height = small.size
    data = list(small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata())
    bins = {}
    for v in data:
        if v > 170:
            bins[v // 12] = bins.get(v // 12, 0) + 1
    levels = sorted(bins, key=bins.get, reverse=True)[:2]
    if len(levels) < 2 or abs(levels[0] - levels[1]) < 2:
        return 0.0
    major, minor = bins[levels[0]], bins[levels[1]]
    # A checkerboard has two near-equal light levels covering most of the image (patterns such as mazes,
    # paper lines or a slide background are unbalanced or cover too little).
    if minor / major < 0.5 or (major + minor) < 0.45 * len(data):
        return 0.0
    a, b = levels

    def alternation(lines):
        changes = pairs = 0
        for line in lines:
            prev = None
            for v in line:
                level = v // 12
                if level not in (a, b):
                    prev = None
                    continue
                if prev is not None:
                    pairs += 1
                    changes += level != prev
                prev = level
        return changes / pairs if pairs else 0.0

    rows = [data[y * width:(y + 1) * width] for y in range(height)]
    cols = [data[x::width] for x in range(width)]
    row_alt, col_alt = alternation(rows), alternation(cols)
    # Real cells (8-24 px at 256 px) give ~0.04-0.15 changes per step on both axes; flat backgrounds give ~0.
    return min(row_alt, col_alt) * 4 if min(row_alt, col_alt) >= 0.02 else 0.0


def propose(candidates: list[dict], top_k: int = 5) -> dict:
    """Pick the best-scored usable candidate as a PROPOSAL; keep alternatives for the reviewer.

    Each candidate dict needs: candidate_id, score (float or None), rejection (str or None).
    """
    usable = sorted((c for c in candidates if not c.get("rejection") and c.get("score") is not None),
                    key=lambda c: c["score"], reverse=True)
    if not usable:
        return {"status": "NO_SUITABLE_IMAGE", "proposed_candidate_id": None, "alternatives": [],
                "review_status": "needs_review"}
    return {"status": "PROPOSED", "proposed_candidate_id": usable[0]["candidate_id"],
            "alternatives": [c["candidate_id"] for c in usable[1:top_k]], "review_status": "needs_review"}


def lookup_key(english: str, japanese: str, vietnamese: str) -> str:
    """Exact-match key for reusing an owner-approved image; all three languages must match."""
    return "␟".join(" ".join(s.casefold().split()) for s in (english, japanese, vietnamese))
