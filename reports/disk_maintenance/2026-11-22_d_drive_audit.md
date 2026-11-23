# D: drive inventory — 2026-11-22

Initial inspection was read-only. Following the owner's instruction, one verified duplicate video was removed; no other existing D: files or partitions were changed. Sizes are binary GiB, rounded; directory totals are recursive and may include generated dependencies. Reparse points and protected system locations were excluded from the directory scan.

## Capacity and largest areas

- D: 202.70 GiB total, 143.64 GiB used, 59.06 GiB free.
- `D:/Riot Client` 47.19 GiB (installed games); `D:/IOT Hien Dai` 16.75 GiB; `D:/Ubuntu-22.04-2` 15.50 GiB (VM disk files); `D:/Android Enviroment` 8.40 GiB; `D:/Espressif` 8.25 GiB; `D:/Download` 7.90 GiB; `D:/huggingface-cache` 4.07 GiB; current repository 3.28 GiB (3.20 GiB `.venv`).
- `D:/pagefile.sys` is 11.00 GiB and Windows-managed. Do not manually remove it.

## Candidates for owner review before deletion

| Candidate | Size | Evidence and decision needed |
|---|---:|---|
| `D:/IOT Hien Dai/Project/NT532-BACKUPS/20261112-122413` | 6.58 GiB | Dated backup: `windows` 4.66 GiB, `pi` 1.91 GiB. Active `Project-NT532.R12` is 7.27 GiB, but its `pi` directory is only 0.20 GiB; do not assume the backup contains no unique recovery data. Delete only if this recovery point is no longer needed. |
| `D:/Download` top-level EXE/MSI installers | 4.84 GiB across 46 files | Examples: Anaconda 1.12 GiB, Docker Desktop 0.60 GiB, two Cisco Packet Tracer versions 0.57 GiB combined. Review installed versions and offline installer needs; downloaded documents and recordings are outside this set. |
| `D:/IOT Hien Dai/Project/Project-NT532.R12/build-output` | 3.51 GiB | Includes `node-ab-aim-hold-worktree` 1.18 GiB and several 0.45–0.46 GiB integrated build directories. Check whether worktrees contain unmerged work or unique test evidence before removing. |
| `D:/Espressif/dist` | 1.64 GiB | Downloaded toolchain archives. Likely reproducible, but retain if offline reinstall is needed. Do not remove installed tools under `D:/Espressif/tools` by this rule. |
| `D:/EousX-Movie-Booking-AI-git-backup-20260526143310` | 0.02 GiB | **Preserve:** this 25.4 MiB Git backup has four commits; all four are absent from the current EousX repository's 17 reachable commits. It contains unique history despite its small size. |

The first four candidates total about 16.6 GiB before any decision; they are not an approved deletion set. The EousX backup is listed for preservation, not deletion. Other large areas are installed games, a VMware Ubuntu VM, Android SDK images, models, source projects, or active caches. Remove games via their uninstallers; never delete individual VMware `.vmdk` segments or `pagefile.sys` manually.

## Completed owner-selected cleanup

On 2026-11-22, SHA-256 was rechecked for both 780,310,106-byte copies of `editthis.mp4`; both hashes were `62A9DC5C1DF6591F35FB4AB2EF47912EE7DA21921FB3D244534096F424CE4B1A`. Removed only `D:/OBS output/editthis.mp4` (744.2 MiB). Confirmed the copy at `D:/IOT Hien Dai/nop project/Ảnh và video mô phỏng + minh chứng/editthis.mp4` still exists and the outside copy is absent. D: free space was 59.78 GiB afterward.

## C: expansion feasibility for a later stage

C: and D: are on disk 0 (Intel SSD). Partition order is C: (200.70 GiB), partition 8 (50.00 GiB, GPT Linux filesystem type, hidden/no drive letter), then D: (202.70 GiB). D: already has more than 20 GiB free, but shrinking D: alone would not create free space adjacent to C: because the 50 GiB Linux-type partition lies between them. The role and contents of partition 8 must be confirmed before any resize or movement plan. No partition action was taken.

Next action: owner selects specific deletion candidates after reviewing this inventory; then separately plan and verify the partition operation with a backup and exact partition map. Project A-001/B-002 status is unchanged.
