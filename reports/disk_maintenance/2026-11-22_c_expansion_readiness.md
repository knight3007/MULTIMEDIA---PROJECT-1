# C: expansion readiness — 2026-11-22

Requested change: add 20 GiB of partition capacity to C: while keeping D: and Ubuntu/Linux. **No partition was resized, moved, formatted, or deleted.**

## Verified layout

Disk 0 is an Intel 512 GB GPT SSD, reported Healthy/Online. In physical order: EFI 0.25 GiB, MSR 0.02 GiB, C: 200.70 GiB (NTFS, boot), partition 8 50.00 GiB (GPT Linux filesystem type; user confirms Linux dual boot is still used), D: 202.70 GiB (NTFS), Recovery 1.07 GiB, RESTORE 22.00 GiB, Recovery 0.20 GiB. D: has about 59.78 GiB free. Disk 1 is a separate Patriot SSD; E: has 209.27 GiB free and a separate 150 GiB Linux-type partition.

There is no unallocated space between C: and the intervening Linux partition. Shrinking D: alone cannot extend C:. [Microsoft's volume extension guidance](https://learn.microsoft.com/en-us/windows-server/storage/disk-management/extend-a-basic-volume) requires unallocated space immediately after C: on the same disk. A partition tool would have to move data-bearing partitions, including the Linux partition, to place 20 GiB next to C:. [DiskGenius documents](https://www.diskgenius.com/manual/resize-partition.php) that this may require WinPE and that backup is necessary because resizing can fail or lose data.

## Unmet safety gates

1. User is unsure whether a restorable backup exists. No full disk image was found in the inspected E: file inventory. Disk 0 is about 477 GiB raw; E:'s 209 GiB free is insufficient to guarantee a full uncompressed image. Use a separate backup destination with at least 500 GiB free, or establish a verified recovery plan covering C:, D:, the 50 GiB Linux partition, EFI, and restore partitions before changing the layout.
2. BCD, Windows Recovery and BitLocker checks were denied in this tool session because it lacks administrator privileges. DiskGenius prompted for UAC; after user approval, no DiskGenius process/window was available to inspect. Do not infer these statuses.
3. The Linux partition's actual filesystem, used space and boot role have not been inspected from Linux or an elevated partition tool. Its GPT type and the user's dual-boot confirmation establish that it must be preserved.

## Next stage

Prepare and test a restorable backup on an independent disk, verify Windows and Linux boot media/recovery access, inspect the Linux partition and boot configuration with administrator access, and then choose an offline partition movement plan. Check both operating systems and exact C:/D: sizes afterward. If a restorable backup cannot be established, offer to free about 20 GiB *within* C: by relocating non-system data to E:/D:; that changes free space, not C:'s partition capacity.

Status: **BLOCKED before partition mutation** pending verified backup and administrative inspection. This is a safety gate, not a completed 20 GiB allocation.
