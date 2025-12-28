#!/bin/env python3
import re
import sys
import requests
from pathlib import Path
from scrython.cards import Object, Search


TEXT_HELP = """\x1b[36mscrypic\x1b[39m - fetch artworks for your MtG decks from Scryfall

To run this script on deck files, use one of either:
  \x1b[32mscrypic "..." < deck.txt
  cat deck.txt | scrypic "..."\x1b[39m
"""
TEXT_INTERACTIVE = """Running in interactive mode instead...

Pass MtG cards in Arena format line by line like this:
\x1b[33m1 Lightning Bolt
1 Llanowar Elves
1 Opt\x1b[39m
Type Ctrl+D to stop
"""


def die(msg: str):
    print(f"\x1b[31mError: {msg}\x1b[39m", file=sys.stderr)
    sys.exit(1)


def parse_mtga_deck() -> list[str]:
    card_names: set[str] = set()

    for line in sorted(sys.stdin.read().splitlines()):
        line = line.strip()
        if not line or line.lower().startswith(("sideboard", "deck")):
            continue

        # MTGA format: "4 Lightning Bolt"
        match = re.match(r"\d+\s+(.+)", line)
        if match:
            card_names.add(match.group(1))

    return sorted(card_names)


def all_printings(card_name: str, query: str) -> Search:
    card_name = card_name.replace('"', '\\"') # TODO REMOVE
    query = query or ""

    try:
        result = Search(
            q=f'!"{card_name}" {query}',
            unique="prints",
            order="released"
        )
        return result
    except:
        die(f"No results found for '{card_name}'!")


def download_image(card: Object, outdir: str):
    # TODO
    if not hasattr(card, "image_uris") or not card.image_uris:
        print(f">>> Skipping {card}")
        return

    # TODO
    # TODO dfc
    url = card.image_uris[IMAGE_TYPE]
    if not url:
        return

    name = (f'{card.name}_{card.set.upper()}_{card.collector_number}'
        .replace(" ", "_")
        .replace("'", "")
        .replace(",", ""))
    path = outdir / f"{name}.{IMAGE_TYPE}"

    # TODO
    if path.exists():
        return

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    path.write_bytes(r.content)
    print(f"• {path.name}")


def main(outdir: str, query: str|None):
    if sys.stdin.isatty():
        print(TEXT_HELP)
        print(TEXT_INTERACTIVE)

    outpath = Path(outdir)
    outpath.mkdir(exist_ok=True)

    cards: set[str] = parse_mtga_deck()

    for card in cards:
        print(card)
        carddir = outpath / card
        carddir.mkdir(exist_ok=True)

        printings = all_printings(card, query)
        seen = set()

        for printing in printings.iter_all():
            cid = printing.card_id
            if cid in seen:
                continue

            seen.add(cid)
            download_image(printing, carddir)


if __name__ == "__main__":
    outdir: str|None = None
    query: str|None = None
    match len(sys.argv):
        case 2:
            outdir = sys.argv[1]
        case 3:
            outdir = sys.argv[1]
            query = sys.argv[2]
        case _:
            print(TEXT_HELP)
            print("""Arguments: <output directory> (<optional scryfall query>)
Stdin: Deck in Arena format""")
            sys.exit(1)

    try:
        main(outdir, query)
    except KeyboardInterrupt:
        die("Interrupted.")

# TODO
# handle dfc cards
# support for order:released to automatically resolve ambiguities
