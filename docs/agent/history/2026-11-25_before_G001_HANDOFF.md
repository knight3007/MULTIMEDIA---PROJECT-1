# Latest handoff — DOCKER-MOVE-001 data disk relocation

Updated 2026-11-25 (Asia/Saigon) by Codex root. Repository `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `9f6c54e4b708b7cfb9c477f801875b1f460cc511`. No commit/push and no active write claim. Previous [DOCKER-001 handoff](history/2026-11-25_before_DOCKER_MOVE_HANDOFF.md) retains pipeline packaging and 15/100-word verification detail.

## Status: DOCKER-MOVE-001 DONE

The owner authorized moving Docker Desktop data from C to D and operated the supported Settings disk-location UI. Docker Desktop was updated from 4.72.0.225998 to 4.100.1.247138. Active WSL data disk: `D:/DockerDataFinal/DockerDesktopWSL/disk/docker_data.vhdx` (22,843,228,160 bytes, locked by Docker). Original `C:/Users/dotha/AppData/Local/Docker/wsl/disk/docker_data.vhdx` is absent. Two redundant D copies produced by failed moves under 4.72.0 were removed only after checking that the active D disk was in use. C free space rose from approximately 11.8 GB before the successful move to 34,742,034,432 bytes; D free space is 28,981,276,672 bytes. Docker Desktop's application remains installed on C; its WSL disk containing images, containers and volumes is on D.

Verification after relocation: `docker desktop status` running; `docker info` reports Docker Engine 29.9.3 Linux. Images retained with original IDs: `multimedia-project-1:local` `2f1e9cf63a3c`, `eousx-api:local` `e7ba02852d26`, `postgres:16-alpine` `4e6e670bb069`. Named volume `api-server_eousx_postgres_data` retained. `eousx_postgres` was healthy and `pg_isready -U postgres` accepted connections. A project-image container printed Python 3.14.3; `docker compose config --quiet` passed. No full Excel/media rerun was needed for the storage move. Canonical data and pipeline files were not edited in this task.

Repository changes in this task: this handoff, STATE, TASKS, archived previous handoff, and one obsolete C-location sentence corrected in `reports/DOCKER_001/verification_report.md`. Next owner action for pipeline use remains the [documented Docker commands](../DOCKER_PIPELINE.md) to build, run an Excel workbook and inspect its gallery. No automatic commit/push.
