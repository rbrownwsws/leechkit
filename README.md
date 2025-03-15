# leechkit

An experimental tool for finding leeches in Anki

## ⚠ Warning ⚠

Back up your Anki collection before using this tool.

This will directly modify your Anki collection.
If things go wrong you may experience data loss.

## How to run

Prerequisite: Install `uv` from https://docs.astral.sh/uv/getting-started/installation/

**N.B. Close Anki before proceeding**

Open Terminal, `cd` to a local copy of the repo and run the desired command:

**Just list the leeches found**
```shell
uv run -m leechkit <ANKI_HOME>/<PROFILE>/collection.anki2
```

**Tag and flag leeches in the deck "foo"**
```shell
uv run -m leechkit <ANKI_HOME>/<PROFILE>/collection.anki2 --query "deck:foo" --flag --write
```

### Optional arguments:

- `--query` - Specify the Anki search query used to select cards to check. Default `deck:current`
- `--skip_reviews` - Specify the number of days with reviews to ignore to let the FSRS state stabilise
- `--leech-threshold`
- `--dynamic-threshold` - Use `@Expertium`'s dynamic threshold correction
- `--write` - Add the leech tag to notes with detected leech cards
- `--tag` - Specify the tag applied to notes having leech cards. Default `maybe-leech`
- `--flag` - Flag the detected leech card red. Use with `--write`
