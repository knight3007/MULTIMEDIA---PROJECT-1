import re
import sys
import time


MAX_QUERY_WORDS = 12
MAX_NEW_TOKENS = 32


def clean_search_query(text: str) -> str:
    text = re.sub(r"[^a-z\s]", " ", text.lower())
    return " ".join(text.split()[:MAX_QUERY_WORDS])


def final_query(word, query):
    return word if query is None else query


def self_test():
    assert final_query("eggs", None) == "eggs"
    assert final_query("eggs", "eggs in carton") == "eggs in carton"
    assert clean_search_query('  "Green-Apple"  among RED apples! ') == "green apple among red apples"
    assert clean_search_query("\n\t!!!") == ""
    assert len(clean_search_query("apple " * 20).split()) == 12
    assert query_error(clean_search_query("ring-ring"), ended=True)
    assert query_error(clean_search_query("visual evidence showing a person"), ended=True)
    for query in (
        "apple fruit", "wristwatch", "calendar date", "bank building", "tin can",
        "two cups side by side with different amounts of steam",
        "a person pointing at a distant apple",
        "chicken eggs", "eggs in a tray", "eggs in an egg tray", "glass vase",
        "software application icon", "password lock icon", "notification bell icon",
    ):
        assert query_error(query, ended=True) is None, query
    for query in (
        "", "ring-ring", "ring ring", "always always", "watch đồng hồ đeo tay",
        "dateYou can search for images of", "apple fruit\nExplanation",
        "you can search for images", '"apple fruit"',
        "eggs egg tray", "egg eggs", "apples apple fruit",
        "important thing", "impossible situation",
    ):
        assert query_error(query, ended=True), repr(query)
    assert query_error("apple fruit", ended=False)
    assert query_error("one two three four five six seven eight nine ten eleven twelve thirteen",
                       ended=True)
    assert query_error(" ".join(["small", "large"] * 9), ended=True)
    print("Query validation checks passed.")


def query_error(query, *, ended):
    """Check format only; semantic correctness still needs human review."""
    if not ended:
        return "generation reached token limit without EOS"
    if not re.fullmatch(r"[a-z]+(?: [a-z]+){0,11}", query):
        return "use 1-12 lowercase English words separated by single spaces"
    words = query.split()
    if any(left == right for left, right in zip(words, words[1:])):
        return "do not repeat consecutive words"
    # ponytail: catch adjacent regular -s forms only; no general English lemmatizer.
    if any(left == right + "s" or right == left + "s"
           for left, right in zip(words, words[1:])):
        return "do not place singular and plural forms of the same word next to each other"
    if set(words) & {"you", "here"} or "search for" in query:
        return "return the subject only, without instructions or commentary"
    if set(words) & {"show", "showing", "image", "meaning", "verb", "visual", "evidence", "concept"}:
        return "use concrete search terms without meta words or explanations"
    if words[-1] in {"thing", "things", "situation", "situations"}:
        return "name a specific subject or action instead of a vague thing or situation"
    return None


MODEL_NAME = "Qwen/Qwen3-1.7B"

samples = [
    "eggs", "understand", "remember", "receive", "software",
    "important", "impossible", "dangerous", "different", "password",
]


system_prompt = """Turn one English vocabulary word into the shortest clear image search query.
Output only 1-12 lowercase English words separated by spaces. No punctuation or explanation.

Prefer: real object, human action, real scene, comparison, then familiar icon. Name objects directly, not their containers or accessories. Show verbs as actions, adjectives as visible evidence or comparison, and mental verbs through a related everyday scene.

Use icon only when it shows the exact meaning more clearly than a normal photograph. If a photograph works, use it. Never add icon merely because a word is abstract. Last resort: no photo. Avoid visual, concept, meaning, image, evidence, vague thing or situation, and singular-plural repeats.

Examples:
apple -> apple fruit
repair -> mechanic repairing car
different -> two different shirts side by side
remember -> person looking at old family photo
software -> software application icon
password -> password lock icon
"""


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    def synchronize_cuda():
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    load_started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    model.eval()
    synchronize_cuda()
    model_load_seconds = time.perf_counter() - load_started
    conversations = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Input Word: {word}\nQuery:"},
        ]
        for word in samples
    ]
    results = [None] * len(samples)
    errors = [None] * len(samples)
    pending = list(range(len(samples)))
    eos_ids = model.generation_config.eos_token_id
    if eos_ids is None:
        eos_ids = tokenizer.eos_token_id
    if eos_ids is None:
        raise RuntimeError("Model and tokenizer do not define an EOS token")
    if isinstance(eos_ids, int):
        eos_ids = [eos_ids]
    eos_id_set = set(eos_ids)

    synchronize_cuda()
    inference_started = time.perf_counter()
    generation_seconds = 0.0
    attempt_times = []
    retry_count = 0

    for attempt in range(2):
        if not pending:
            break
        if attempt:
            retry_count += len(pending)
        texts = [tokenizer.apply_chat_template(
            conversations[i], tokenize=False, add_generation_prompt=True,
            enable_thinking=False,
        ) for i in pending]
        inputs = tokenizer(texts, return_tensors="pt", padding=True,
                           add_special_tokens=False)
        input_device = model.get_input_embeddings().weight.device
        inputs = {key: value.to(input_device) for key, value in inputs.items()}
        synchronize_cuda()
        attempt_started = time.perf_counter()
        with torch.inference_mode():
            outputs = model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=eos_ids,
            )
        synchronize_cuda()
        attempt_seconds = time.perf_counter() - attempt_started
        attempt_times.append(attempt_seconds)
        generation_seconds += attempt_seconds
        generated = outputs[:, inputs["input_ids"].shape[1]:]
        retry = []
        for row, index in enumerate(pending):
            tokens = generated[row].tolist()
            raw = tokenizer.decode(tokens, skip_special_tokens=True).strip()
            query = clean_search_query(raw)
            if query != raw:
                print(f"attempt {attempt + 1} | {samples[index]} | "
                      f"raw={raw!r} | cleaned={query!r}")
            error = query_error(query, ended=any(t in eos_id_set for t in tokens))
            errors[index] = error
            if error is None:
                results[index] = query
            else:
                print(f"attempt {attempt + 1} | {samples[index]} | "
                      f"rejected={query!r} | raw={raw!r} | {error}")
                # Keep the same meaning constraints for the repair attempt.
                conversations[index] = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content":
                     f"Input Word: {samples[index]}\nCorrection required: {error}. "
                     "Keep the original meaning. Do not invent attributes to avoid repetition.\nQuery:"},
                ]
                retry.append(index)
        pending = retry

    synchronize_cuda()
    total_inference_seconds = time.perf_counter() - inference_started

    print("\nFORMAT_OK checks syntax only; review meaning before downloading images.")
    for word, query, error in zip(samples, results, errors):
        status = "FORMAT_OK" if query is not None else "FALLBACK"
        print(f"{word:10s} -> {final_query(word, query)} | {status}"
              + (f" ({error})" if error else ""))

    print("\nPERFORMANCE")
    print(f"model load: {model_load_seconds:.3f} s")
    print("generation attempts: " + ", ".join(
        f"{seconds:.3f} s" for seconds in attempt_times))
    print(f"generation: {generation_seconds:.3f} s")
    print(f"total inference: {total_inference_seconds:.3f} s")
    print(f"words processed: {len(samples)}")
    print(f"average: {total_inference_seconds * 1000 / len(samples):.1f} ms per word")
    print(f"retries: {retry_count}")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
