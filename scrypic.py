#!/bin/env python3
import argparse
import re
import sys
import requests
from pathlib import Path
from scrython.cards import ById, Named, Object, Search


TEXT_HELP = """\x1b[36mscrypic\x1b[39m - fetch artworks for your MtG decks from Scryfall

To run this script on deck files, use one of either:
  \x1b[32mscrypic output/ "..." < deck.txt
  cat deck.txt | scrypic output/ "..."\x1b[39m

Running in interactive mode instead...

Pass MtG cards in Arena format line by line like this:
\x1b[33m1 Lightning Bolt
1 Llanowar Elves
1 Opt\x1b[39m
Type Ctrl+D to fetch them
"""


class FullHelpParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        sys.exit(2)


failed: list[str] = list()
token_failed: list[str] = list()


def printsucc(msg: str):
    print(f"\x1b[32m{msg}\x1b[39m", file=sys.stderr)


def printerr(msg: str):
    print(f"\x1b[31m{msg}\x1b[39m", file=sys.stderr)


def safe_search(query: str) -> Search|None:
    try:
        return Search(q=query)
    except Exception:
        return None


def parse_mtga_deck() -> list[str]:
    cardnames: set[str] = set()

    for line in sorted(sys.stdin.read().splitlines()):
        line = line.strip()
        if not line or line.lower().startswith(("sideboard", "deck")):
            continue

        # MTGA format: "4 Lightning Bolt"
        match = re.match(r"\d+\s+(.+)", line)
        if match:
            cardnames.add(match.group(1))

    return sorted(cardnames)


def all_printings(cardname: str, query: str|None, prefer: str|None) -> Search|None:
    cardname = cardname.replace('"', '\\"') # TODO REMOVE
    query = query or ""

    if prefer and (results := safe_search(f'!"{cardname}" {query} {prefer}')):
        return results

    if (results := safe_search(f'!"{cardname}" {query}')):
        return results

    printerr("    No results found!")
    failed.append(cardname)
    return None


def all_tokens_with_printings(cardname: str, query: bool|str|None) -> list[Search]|None:
    card = Named(exact=cardname)
    # TODO check for no internet
    if not card.all_parts:
        return None

    if query is True:
        query = ""

    searches: list[Search] = list()
    for card_part in card.all_parts:
        if card_part.component != "token":
            continue
        token = ById(id=card_part.id)
        # TODO check for no internet

        if (results := safe_search(f"oracleid:{token.oracle_id} {query}")):
            searches.append(results)
        else:
            printerr(f"    Token: No results found for '{token.name}'!")
            token_failed.append(token.name)
            continue

    return searches


def download_image(card: Object, cardpath: str) -> str|None:
    # TODO
    if not hasattr(card, "image_uris") or not card.image_uris:
        print(f">>> Skipping {card}")
        return None

    # TODO
    # TODO dfc
    if not (url := card.image_uris["png"]):
        return None

    name = (f'{card.name}_{card.set.upper()}_{card.collector_number}'
        .replace(" ", "_")
        .replace("'", "")
        .replace(",", ""))
    path = cardpath / f"{name}.png"

    # TODO
    if path.exists():
        return None

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    path.write_bytes(r.content)
    return path.name


def main(args: argparse.Namespace):
    if sys.stdin.isatty():
        print(TEXT_HELP)

    outpath = Path(args.outdir)
    outpath.mkdir(exist_ok=True)
    print(f"Made directory '{args.outdir}'!")

    if args.tokens:
        all_tokenspath = Path(outpath / "_tokens")
        all_tokenspath.mkdir(exist_ok=True)
        print(f"Made directory '{outpath}/_tokens'!")
        # TODO delete if empty

    cards: set[str] = parse_mtga_deck()

    print()
    for card in cards:
        print(card)
        cardpath = outpath / card
        cardpath.mkdir(exist_ok=True)

        printings = all_printings(card, args.query, args.prefer)
        if not printings:
            continue

        # TODO make it opt-in
        if args.tokens and (all_tokens := all_tokens_with_printings(card, args.tokens)):
            seen: set[str] = set()
            for token_printings in all_tokens:
                tokenpath = Path(all_tokenspath / token_printings.data[0].name)
                tokenpath.mkdir(exist_ok=True)

                for printing in token_printings.iter_all():
                    if (id := printing.card_id) in seen:
                        continue

                    seen.add(id)
                    filename = download_image(printing, tokenpath)
                    print(f"    Token: {filename or "(already there)"}")

        seen: set[str] = set()
        for printing in printings.iter_all():
            id = printing.card_id
            if id in seen:
                continue

            seen.add(id)
            filename = download_image(printing, cardpath)
            print(f"    {filename or "(already there)"}")

    stat = 0
    if failed:
        printerr("Failed to download the following cards:")
        for card in failed:
            printerr(f"    {card}")
        stat = 1
    if token_failed:
        printerr("Failed to download the following tokens:")
        for token in token_failed:
            printerr(f"    {token}")
        stat = 1

    sys.exit(stat)


if __name__ == "__main__":
    parser = FullHelpParser(
        prog="scrypic",
        description="fetch artworks for your MtG decks from Scryfall"
    )
    parser.add_argument("outdir", help="directory where artworks are stored to")
    parser.add_argument(
        "query",
        nargs="?",
        help="additional Scryfall query to filter results"
    )
    parser.add_argument(
        "--tokens",
        nargs="?",
        const=True,
        default=None,
        help="fetch related tokens too with an optional custom query"
    )
    parser.add_argument(
        "--prefer",
        help="secondary Scryfall query to apply wherever " +
            "the result pool would be non-empty"
    )
    args: argparse.Namespace = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        printerr("Interrupted.")
        sys.exit(130)

# TODO
# handle dfc cards
# README.md
