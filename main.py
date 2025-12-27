import re
import sys
import requests
from pathlib import Path
from scrython.cards import Search
from scrython.base import ScryfallError

# ---------- config ----------
# TODO make it user-configurable
IMAGE_TYPE = "png"  # png | large | normal | small | art_crop | border_crop
OUTPUT_DIR = "out"
# ----------------------------


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
    card_name = card_name.replace('"', '\\"')
    # TODO handle 404
    return Search(
        q=f'{query} !"{card_name}"',
        unique="prints",
        order="released"
    )


def download_image(card: str, outdir: str):
    # TODO
    if not hasattr(card, "image_uris") or not card.image_uris:
        print(f">>> Skipping {card}")
        return

    # TODO
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Arguments: <scryfall query>\nStdin: Deck in Arena format")
        sys.exit(1)

    query = sys.argv[1]

    outdir = Path(OUTPUT_DIR)
    outdir.mkdir(exist_ok=True)

    cards: set[str] = parse_mtga_deck()

    for name in cards:
        print(name)
        carddir = outdir / name
        carddir.mkdir(exist_ok=True)

        try:
            printings = all_printings(name, query)
        # TODO
        except ScryfallError as e:
            print(f"Skipping {name}: {e}")
            continue

        seen = set()

        for printing in printings.iter_all():
            cid = printing.card_id
            if cid in seen:
                continue

            seen.add(cid)
            download_image(printing, carddir)

# TODO
# parallel downloads
# proper 404 handling
# handle dfc cards
# support for order:released to automatically resolve ambiguities
