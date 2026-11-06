# DDGS image search connectivity diagnosis — 2026-10-29

## Scope and environment

- Working tree: `main` at `c090eae8dd257b114898bb096bc9f51ab5bfd34c`; prior local modifications and assets were retained. No fetch, commit, push, reset, clean, system setting change, or dependency update.
- Interpreter: `D:\MULTIMEDIA - PROJECT 1\.venv\Scripts\python.exe`, Python 3.14.3. Installed `ddgs==9.16.0`, `primp==2.0.1`; `curl.exe` is curl 8.13.0 with Schannel.
- Installed `DDGS.images(self, query, **kwargs)` forwards to `_search_sync(..., backend="auto", ...)`. Its local engine registry includes `duckduckgo` and `bing` image backends. Explicit `backend=` is supported by this installed version.
- `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, lowercase variants, and `DDGS_PROXY` were absent. WinINet proxy enable/server/auto-config were absent. Only presence flags were inspected; no credential values were printed.

## Reproduction and bounded network probes

The earlier isolated run used:

```powershell
.\.venv\Scripts\python.exe 'collect data script/stage_image_replacements.py' --timeout 8 --retries 1 --retry-delay 1 --page-size 3 --rate-limit-delay 1 --siglip-device auto --siglip-dtype auto
```

It exited 1 with search timeouts for `cooked rice` at DuckDuckGo and `chicken meat` at Bing. The [original manifest](../baseline/media-staging/images/20261029T032618Z-c2a89e06/run_manifest.json) has no candidates or JPEGs. Its `search_seconds=0.0` on both failures was a reporting bug, not a zero-duration search.

| Probe | Command/configuration | Outcome | Elapsed | Layer |
|---|---|---|---:|---|
| DuckDuckGo DNS | `Resolve-DnsName duckduckgo.com -Type A -QuickTimeout` | 1 A address, exit 0 | 1.288 s | DNS works |
| Bing DNS | `Resolve-DnsName www.bing.com -Type A -QuickTimeout` | 9 A addresses, exit 0 | 1.230 s | DNS works |
| Sandbox TCP | Python `socket.create_connection((host, 443), timeout=5)` | First host raised `PermissionError [WinError 10013]`, exit 1 | immediate | Sandbox socket restriction; not a service diagnosis |
| Sandbox HTTPS | `curl.exe --head --connect-timeout 5 --max-time 10` | Both hosts returned curl exit 7 before TCP/TLS | <0.1 s | Same sandbox restriction |
| Direct DuckDuckGo HTTPS outside sandbox | `curl.exe --head --connect-timeout 5 --max-time 10 'https://duckduckgo.com/?q=cooked+rice'` | HTTP 202, exit 0; TLS verify result 0 | total 0.228 s; TCP 0.047 s; TLS 0.123 s | DNS, TCP and certificate-verified TLS work; HTTP response is not an image result |
| Direct Bing HTTPS outside sandbox | `curl.exe --head --connect-timeout 5 --max-time 10 'https://www.bing.com/images/async?q=chicken+meat&async=1&first=1&count=1'` | HTTP 200, exit 0; TLS verify result 0 | total 0.215 s; TCP 0.017 s; TLS 0.050 s | DNS, TCP and certificate-verified TLS work |
| DDGS DuckDuckGo outside sandbox | `DDGS(timeout=5).images(query="cooked rice", region="wt-wt", safesearch="moderate", max_results=1, backend="duckduckgo")` | `DDGSException`: `RequestError ... duckduckgo.com ... user error: malformed headers`; 1 attempt, 0 results | 0.344 s | DDGS/remote-response path after basic connectivity |
| DDGS Bing outside sandbox | Same call with `query="chicken meat", backend="bing"` | 1 result; 1 attempt | 0.696 s | DDGS Bing image retrieval works |

No probe disabled TLS verification. The original certificate-store warning did not recur in the explicit backend probes. A read-only `Cert:\CurrentUser\Root` count succeeded (53 entries), and default-verification DDGS Bing plus Schannel curl HTTPS succeeded. This does not identify why the earlier process emitted a warning; it does show that the warning alone cannot explain the current DuckDuckGo failure or the earlier Bing timeout.

## Classification

**Confirmed:** local DNS, TCP 443 and validated HTTPS work outside the sandbox for both hosts. The installed DDGS Bing image backend returned a result; the DuckDuckGo backend failed on a `malformed headers` request error. The former blanket network timeout is not currently reproducible on Bing. The earlier automatic backend choice is not recorded, but its error URLs identify the attempted hosts.

**Unresolved:** whether the DuckDuckGo error originates in a changed remote HTTP response, a transient block, or `primp`/DDGS parsing. HTTP 202 from a direct HEAD request is suggestive but does not prove blocking or rate limiting. No library upgrade, retry increase, proxy bypass or certificate change is justified by these probes. Repeated DuckDuckGo requests were stopped after one explicit failure.

## Minimal diagnostic change and recovery

- `imagecollector.search_images()` accepts an optional explicit backend. Its default stays `auto`. Exhausted failures now retain configured backend, attempt count, original exception type, sanitized message and actual elapsed time. Explicit-backend candidate metadata records `search_client="ddgs"` and `search_backend`; the existing `provider="duckduckgo"` field remains for current cache and dataset-builder compatibility.
- `process_word()` records `search_seconds` on failures and a `failure_stage` (`search`, `download`, `scoring`, `metadata` or `preflight`) with `failure_type`. The staging manifest includes those fields and the selected client/backend. Its `--search-backend` option defaults to `auto`.
- The earlier manifests and production metadata were not rewritten. Existing cache, Qwen, SigLIP ranking and normalization behavior remain in place.

After the one-result Bing probe succeeded, a single fresh two-target run used:

```powershell
.\.venv\Scripts\python.exe 'collect data script/stage_image_replacements.py' --search-backend bing --timeout 8 --retries 0 --retry-delay 0 --page-size 3 --rate-limit-delay 1 --siglip-device auto --siglip-dtype auto
```

Exit 0. The [new run manifest](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/run_manifest.json) records exact approved queries and `search_backend=bing`:

| ID | Query | Search / downloads | Staged JPEG | Review |
|---|---|---|---|---|
| `vocab-000004` rice | `cooked rice` | 3 raw/valid; 3 downloaded; search 1.017 s | [rice.jpg](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/rice.jpg), JPEG RGB 1024×1024, SHA-256 `f447aa26dc6ab0d4c22b46086a1f674b0c799273a3c73902c7c6aea1aeca3cd4` | Pending human approval and source/usage review. Visually shows cooked rice. |
| `vocab-000009` chicken | `chicken meat` | 3 raw/valid; 2 downloaded; 1 candidate HTTP 403; search 0.650 s | [chicken.jpg](../baseline/media-staging/images/20261029T035126Z-e1fcdb0e/chicken.jpg), JPEG RGB 1024×740, SHA-256 `433095d063e4c5e6802a5f54c937e2783989225af31514b1a8e00163e71c726d` | Pending human approval. Visually shows raw chicken meat, but carries Dreamstime watermarks and a copyright mark; do not promote this candidate as-is. |

Both staged metadata files validate with the exact query, `human_approved` query provenance, `ddgs`/`bing`, selected image URL and SigLIP score. A negative SigLIP logit for rice is a ranking score, not a probability or semantic rejection. Neither staged image was promoted.

## Verification and next action

- Before edits: offline suite 73/73 PASS, exit 0. New tests initially failed 5/5 on missing backend/timing/stage behavior; focused suite then passed 5/5. A separate test first exposed the mislabeled Bing download failure and passed after the message was corrected. The first full run after the behavior change found two outdated error-label assertions, which were updated from `DuckDuckGo` to `DDGS`; final full suite: **79/79 PASS**, exit 0 (`4.192 s`).
- Vocabulary validator: 100 physical rows, 0 structural issues, exit 0. Scoped `git diff --check` on modified tracked code/tests: exit 0. New code had no trailing whitespace.
- Post-run hashes matched the pre-run values for all 10 production JPEGs, all 10 metadata files, Qwen cache, 100-ID registry, semantic ledger and unified dataset. Saved dataset still equals a read-only `build_dataset(root)` result with 100 stable IDs. No production media or data was changed.
- Fresh DDGS image retrieval and SigLIP staging now work through Bing for the two approved meanings. This verifies the fresh retrieval path; it does not by itself close the broader Phase B Qwen pipeline gate or approve media for product use.

Next: obtain per-image owner review of the staged rice candidate. Treat the watermarked chicken candidate as unsuitable for promotion unless the owner can establish an acceptable licensed source or chooses a different candidate in a separate, bounded staging run. Keep the original production files and dataset unchanged until an explicit promotion decision and tested media-review rule exist. Revisit the DuckDuckGo backend only if needed, with a separate controlled investigation of the `malformed headers` response.
