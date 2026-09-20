import re
import sys


def clean_search_query(text: str) -> str:
    text = re.sub(r"[^a-z\s]", " ", text.lower())
    return " ".join(text.split()[:16])


def self_test():
    assert clean_search_query('  "Green-Apple"  among RED apples! ') == "green apple among red apples"
    assert clean_search_query("\n\t!!!") == ""
    assert len(clean_search_query("apple " * 20).split()) == 16
    assert query_error(clean_search_query("ring-ring"), ended=True)
    assert query_error(clean_search_query("visual evidence showing a person"), ended=True)
    for query in (
        "apple fruit", "wristwatch", "calendar date", "bank building", "tin can",
        "two cups side by side with different amounts of steam",
        "a person pointing at a distant apple",
        "chicken eggs", "eggs in a tray", "eggs in an egg tray", "glass vase",
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
    assert query_error(" ".join(["small", "large"] * 9), ended=True)
    print("Query validation checks passed.")


def query_error(query, *, ended):
    """Check format only; semantic correctness still needs human review."""
    if not ended:
        return "generation reached token limit without EOS"
    if not re.fullmatch(r"[a-z]+(?: [a-z]+){0,15}", query):
        return "use 1-16 lowercase English words separated by single spaces"
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


system_prompt = """Write a short stock photo search query illustrating the supplied English word.
Return only the query: 1-12 lowercase English words separated by spaces.

Name the subject directly for objects, foods, animals, and technology.
For verbs, describe a person doing the action, including the object of the action.
For adjectives, name visible evidence of the quality. A comparison is allowed.
For mental actions, use a familiar everyday activity associated with that action.
Keep the word's meaning. Do not replace the subject with its container or accessory.
Do not invent materials or decorative details. Do not repeat a noun in singular and plural.
Do not output an explanation, grammatical label, or vague words like thing or situation.

This is the photo search stage. Do not output icon, symbol, logo, or clipart.
If a word has no reasonable concrete illustration, output exactly no photo.

Examples:
Word: bicycle
Query: bicycle
Word: kindness
Query: person helping elderly neighbor
Word: tall
Query: tall person beside short person
Word: repair
Query: mechanic fixing car
"""


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    # Fixed seed makes comparisons easier on the same hardware and batch.
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, dtype=torch.float16, device_map="auto",
    )
    model.eval()
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
    if isinstance(eos_ids, int):
        eos_ids = [eos_ids]

    for attempt in range(2):
        if not pending:
            break
        texts = [tokenizer.apply_chat_template(
            conversations[i], tokenize=False, add_generation_prompt=True,
            enable_thinking=True,
        ) for i in pending]
        inputs = tokenizer(texts, return_tensors="pt", padding=True,
                           add_special_tokens=False)
        input_device = model.get_input_embeddings().weight.device
        inputs = {key: value.to(input_device) for key, value in inputs.items()}
        with torch.inference_mode():
            outputs = model.generate(
                **inputs, max_new_tokens=768,
                do_sample=True, temperature=0.6, top_p=0.95, top_k=20,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=eos_ids,
            )
        retry = []
        for row, index in enumerate(pending):
            tokens = outputs[row, inputs["input_ids"].shape[1]:].tolist()
            decoded = tokenizer.decode(tokens, skip_special_tokens=True)
            raw = decoded.rsplit("</think>", 1)[-1].strip() if "</think>" in decoded else ""
            query = clean_search_query(raw)
            if query != raw:
                print(f"attempt {attempt + 1} | {samples[index]} | "
                      f"raw={raw!r} | cleaned={query!r}")
            error = query_error(query, ended=any(t in eos_ids for t in tokens))
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

    print("\nFORMAT_OK checks syntax only; review meaning before downloading images.")
    for word, query, error in zip(samples, results, errors):
        status = "FORMAT_OK" if query is not None else "REJECTED"
        print(f"{word:10s} -> {query or '-'} | {status}"
              + (f" ({error})" if error else ""))


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
