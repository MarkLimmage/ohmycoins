# Database Snapshots

This directory contains PostgreSQL database snapshots created with `./scripts/db-snapshot.sh`.

## Usage

**Create a snapshot:**
```bash
./scripts/db-snapshot.sh my-snapshot-name
```

**List snapshots:**
```bash
ls -lh backups/
```

**Restore from snapshot:**
```bash
./scripts/db-restore.sh my-snapshot-name
```

## Snapshot Format

- **Files**: `{snapshot-name}.sql.gz` (compressed PostgreSQL dump)
- **Metadata**: `{snapshot-name}.meta` (JSON with creation date, size, etc.)
- **Compression**: gzip (typically 5-10x reduction in size)

## Git Ignore

Snapshots are excluded from version control by default (see `.gitignore`).

To share snapshots with your team:
1. Use Git LFS for large files
2. Upload to shared cloud storage
3. Include in release artifacts

## See Also

- [PERSISTENT_DEV_DATA.md](../PERSISTENT_DEV_DATA.md) - Complete workflow guide
- [scripts/db-snapshot.sh](../scripts/db-snapshot.sh) - Snapshot creation script
- [scripts/db-restore.sh](../scripts/db-restore.sh) - Restore script
