# My-thoughts Utilities

## cleanup_ignored.py

`cleanup_ignored.py` removes working-tree files that Git ignores through `.gitignore` (including nested excludes). It shells out to `git ls-files --others -i --exclude-standard` so Git must be installed and the script must run inside the repository.

### Usage

```bash
python cleanup_ignored.py --dry-run   # list ignored files, no deletions
python cleanup_ignored.py --yes       # delete after listing, skip prompt
python cleanup_ignored.py --repo path/to/repo
```

### Safety tips

- Start with `--dry-run` to double-check the list before deleting anything.
- Without `--yes`, the script asks for confirmation before it removes files.
- It only deletes regular files; directories stay untouched.
- If a file is unignored via `!pattern`, Git will not report it so it will never be deleted by this tool.
