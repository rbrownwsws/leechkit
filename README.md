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
- `--skip-reviews` - Specify the number of days with reviews to ignore to let the FSRS state stabilise Default : 3
- `--max-reviews` - Specify the maximum number of days with reviews to take into account. Default : 0 (all reviews)
- `--leech-threshold`
- `--dynamic-threshold` - Use `@Expertium`'s dynamic threshold correction
- `--incremental-check` - Check if card is a leech after every review. Mark as leech if card ever drops below threshold.
- `--write` - Add the leech tag to notes with detected leech cards
- `--tag` - Specify the tag applied to notes having leech cards. Default `maybe-leech`
- `--flag` - Flag the detected leech card red. Use with `--write`

Note : If you're using --skip-reviews and --max-reviews together, the most restrictive option will be applied on card
basis, based on the number of reviews the card has. For example, if you have a card with 10 reviews, and you set
--skip-reviews to 5 and --max-reviews to 3, only the last 3 reviews will be taken into account. If for the same card you
set --skip-reviews to 5 and --max-reviews to 10, only the last 5 will be considered.