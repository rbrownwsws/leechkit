from pathlib import Path
from typing import Sequence, Final
import typer

from anki.collection import Collection
from anki.cards import CardId
from rich import print
from rich.progress import Progress
from rich.table import Table

from .detector import card_is_leech
from .utils import SuppressPrint

LEECH_FLAG: Final[int] = 1


def main(
    collection: Path,
    query: str = "deck:current",
    tag: str = "maybe-leech",
    skip_reviews: int = 3,
    leech_threshold: float = 0.05,
    dynamic_threshold: bool = False,
    incremental_check: bool = False,
    flag: bool = False,
    write: bool = False,
):
    options_table = Table()
    options_table.add_column("Option")
    options_table.add_column("Value")

    options_table.add_row("query", f"{query}")
    options_table.add_row("skip_reviews", f"{skip_reviews}")
    options_table.add_row("leech_threshold", f"{leech_threshold}")
    options_table.add_row("dynamic_threshold", f"{dynamic_threshold}")
    options_table.add_row("incremental_check", f"{incremental_check}")
    options_table.add_row("tag", f"{tag}")
    options_table.add_row("flag", f"{flag}")
    options_table.add_row("write", f"{write}")

    print(options_table)

    col = Collection(path=str(collection.absolute()))

    next_day_starts_at_hour = col.get_preferences().scheduling.rollover

    selected_card_ids: Sequence[CardId] = col.find_cards(query=query)
    leech_count = 0

    print("")
    print("[bold]Searching for leeches[/bold]")
    print("")

    with Progress() as progress:
        task = progress.add_task("Checking cards", total=len(selected_card_ids))

        for card_id in selected_card_ids:
            with SuppressPrint():
                card = col.get_card(card_id)
                note = col.get_note(card.nid)
                revlogs = col.card_stats_data(card_id).revlog
            # Reverse the revlog so we are going from oldest->newest
            revlogs.reverse()

            is_leech, metadata = card_is_leech(
                card=card,
                reviews=revlogs,
                skip_reviews=skip_reviews,
                leech_threshold=leech_threshold,
                dynamic_threshold=dynamic_threshold,
                incremental_check=incremental_check,
                next_day_starts_at_hour=next_day_starts_at_hour,
            )

            if is_leech:
                if write:
                    note.add_tag(tag)
                    col.update_note(note)

                    if flag:
                        card.flags |= LEECH_FLAG
                        col.update_card(card)

                progress.console.print(
                    f"[green]Found leech - cid:{card_id} - metadata:{metadata}[/green]",
                    highlight=False,
                )

                leech_count += 1

            progress.update(task, advance=1)

    print("")
    print(f"Processed {len(selected_card_ids)} cards")
    print(f"Found {leech_count} leeches")


typer.run(main)
