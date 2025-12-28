#!/bin/env python3
import re
import sys
import requests
from pathlib import Path
from scrython.cards import ById, Named, Object, Search


TEXT_HELP = """\x1b[36mscrypic\x1b[39m - fetch artworks for your MtG decks from Scryfall

To run this script on deck files, use one of either:
  \x1b[32mscrypic output/ "..." < deck.txt
  cat deck.txt | scrypic output/ "..."\x1b[39m
"""
TEXT_INTERACTIVE = """Running in interactive mode instead...

Pass MtG cards in Arena format line by line like this:
\x1b[33m1 Lightning Bolt
1 Llanowar Elves
1 Opt\x1b[39m
Type Ctrl+D to stop
"""


failed: list[str] = list()
token_failed: list[str] = list()


def printerr(msg: str):
    print(f"\x1b[31m{msg}\x1b[39m", file=sys.stderr)


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


def all_printings(card_name: str, query: str) -> Search|None:
    card_name = card_name.replace('"', '\\"') # TODO REMOVE
    query = query or ""

    try:
        return Search(
            q=f'!"{card_name}" {query}',
            unique="prints",
            order="released"
        )
    except Exception:
        printerr("    No results found!")
        failed.append(card_name)
        return None


def all_tokens_with_printings(card_name: str) -> list[Search]|None:
    card = Named(exact=card_name)
    if not card.all_parts:
        return None

    result: list[Search] = list()
    for card_part in card.all_parts:
        if card_part.component != "token":
            continue
        token = ById(id=card_part.id)
        try:
            result.append(Search(q=f"oracleid:{token.oracle_id}"))
        except:
            printerr(f"    Token: No results found for '{token.name}'!")
            token_failed.append(token.name)
            continue

    return result


def download_image(card: Object, outdir: str):
    # TODO
    if not hasattr(card, "image_uris") or not card.image_uris:
        print(f">>> Skipping {card}")
        return

    # TODO
    # TODO dfc
    url = card.image_uris["png"]
    if not url:
        return

    name = (f'{card.name}_{card.set.upper()}_{card.collector_number}'
        .replace(" ", "_")
        .replace("'", "")
        .replace(",", ""))
    path = outdir / f"{name}.png"

    # TODO
    if path.exists():
        return

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    path.write_bytes(r.content)


def main(outdir: str, query: str|None):
    if sys.stdin.isatty():
        print(TEXT_HELP)
        print(TEXT_INTERACTIVE)

    outpath = Path(outdir)
    outpath.mkdir(exist_ok=True)

    cards: set[str] = parse_mtga_deck()

    print()
    for card in cards:
        print(card)
        carddir = outpath / card
        carddir.mkdir(exist_ok=True)

        printings = all_printings(card, query)
        if not printings:
            continue

        # TODO make it opt-in
        all_tokens = all_tokens_with_printings(card)
        if all_tokens:
            for token_printings in all_tokens:
                seen: set[str] = set()
                for printing in token_printings.iter_all():
                    id = printing.card_id
                    if id in seen:
                        continue

                    seen.add(id)
                    download_image(printing, carddir)
                    print(f"    Token: {printing.name}")

        seen: set[str] = set()
        for printing in printings.iter_all():
            id = printing.card_id
            if id in seen:
                continue

            seen.add(id)
            download_image(printing, carddir)
            print(f"    {printing.name}")

    stat = 0
    if len(failed) > 0:
        printerr("Failed to download the following cards:")
        for card in failed:
            printerr(f"    {card}")
        stat = 1
    if len(token_failed) > 0:
        printerr("Failed to download the following tokens:")
        for token in token_failed:
            printerr(f"    {token}")
        stat = 1

    sys.exit(stat)


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
        printerr("Interrupted.")
        sys.exit(130)

# TODO
# DEBUG token support
# --tokens: include its tokens
# --bonus <query>: if both queries combined dont 404, take them, otherwise just query
# handle dfc cards
# support for order:released to automatically resolve ambiguities
# README.md
