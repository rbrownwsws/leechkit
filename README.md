# leechkit

An experimental tool for finding leeches in Anki

## ⚠ Warning ⚠

Back up your Anki collection before using this tool.

This will directly modify your Anki collection.
If things go wrong you may experience data loss.

## How to run

**N.B. Close Anki first**

**Just list found leeches**
```shell
uv run -m leechkit <ANKI_HOME>/<PROFILE>/collection.anki2
```

**Tag and flag leeches in the deck "foo"**
```shell
uv run -m leechkit <ANKI_HOME>/<PROFILE>/collection.anki2 --query "deck:foo" --flag --write
```

### Optional arguments:

- `--query` - The Anki search query used to select cards to check. Default `deck:current`
- `--skip_reviews` - The number of days with reviews to ignore to let the FSRS state stabilise
- `--leech-threshold`
- `--dynamic-threshold` - Use `@Expertium`'s dynamic threshold correction
- `--tag` - The tag to apply to notes that have leech cards. Default `maybe-leech`
- `--flag` - Will also flag the specific leech card red
- `--write` - Will write the leech tag and flag to notes that have detected leech cards
