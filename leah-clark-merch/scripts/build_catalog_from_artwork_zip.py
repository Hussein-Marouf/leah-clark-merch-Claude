#!/usr/bin/env python3
"""Build the convention catalog from the current inventory DOCX and artwork ZIP.

The ZIP contains print-resolution artwork. This builder only extracts artwork
that can be matched to the current inventory list, then writes web-friendly
catalog images so the public QR page stays fast on phones.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image, ImageOps

from build_catalog_from_inventory_docx import CATALOG_FIELDS, extract_inventory, image_name_from_filename


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIT_FIELDS = [
    "name",
    "material",
    "size",
    "status",
    "image",
    "matched_artwork",
    "source",
    "score",
    "match_note",
]

STOPWORDS = {
    "art",
    "bleed",
    "card",
    "copy",
    "dpi",
    "file",
    "files",
    "fullbleed",
    "jpg",
    "jpeg",
    "metal",
    "of",
    "png",
    "poster",
    "print",
    "redraw",
    "size",
    "trading",
    "ultrarez",
    "vector",
    "webp",
    "with",
}

PHRASE_REPLACEMENTS = [
    ("aimeenyx", "aimee ny"),
    ("asia closeup", "asia closeup"),
    ("asiacloseup", "asia closeup"),
    ("asianun", "asia nun"),
    ("blair maka manga", "blair maka panel"),
    ("blair maka", "blair maka panel"),
    ("cardart", "card art"),
    ("deathcard", "death card"),
    ("dragon maid", "dragon maid"),
    ("dxdhug", "dxd hug"),
    ("koba kabob", "kobayashi kabob"),
    ("kob kabob", "kobayashi kabob"),
    ("kob tohru nap", "dragon maid nap"),
    ("kob tohru omurice", "kobayashi omurice"),
    ("kobayashi tohru gift", "kobayashi gift"),
    ("koby tribute", "koby tribute"),
    ("kobymop", "koby mopping"),
    ("maron not bulma", "maron not bulma"),
    ("minami69queen", "minami queen wands"),
    ("minami8511", "minami"),
    ("minamitcqueen", "minami queen wands"),
    ("nami df", "nami doublefinger"),
    ("orangekiss", "orange kiss"),
    ("pink manga cover", "pink manga cover toga"),
    ("rarestab", "rare stab"),
    ("rarecard", "rare card"),
    ("toga cami", "toga cammie"),
    ("toga camie", "toga cammie"),
    ("toga neon", "toga neon"),
    ("toga ocha", "toga ochaco"),
    ("togachaco", "toga ochaco"),
    ("togaochaco", "toga ochaco"),
    ("togacard6", "toga 6 coat"),
    ("togapower", "power toga"),
    ("togawpower", "power toga"),
    ("togarare", "toga rare"),
    ("togatwice", "toga twice"),
    ("uraka", "ochaco"),
    ("uraraka", "ochaco"),
]

TOKEN_REPLACEMENTS = {
    "coby": "koby",
    "df": "doublefinger",
    "konoko": "konako",
    "lvl": "level",
    "lvl4": "level4",
    "manga": "",
    "nyx": "ny",
    "ocha": "ochaco",
    "temperence": "temperance",
    "tc": "",
    "tcsize": "",
    "wands": "wand",
}

# Exact overrides are used only where the artwork label is a known shorthand for
# a current inventory item. Values are filename fragments, so they can match
# either the top-level ZIP or a nested ZIP entry.
OVERRIDES: dict[str, dict[str, str] | str] = {
    "asia argento nun": "asiaNUN-85x11",
    "asia closeup card art": "AsiaCLOSEUP_card",
    "asia clover": "Asia_Clovers",
    "asia clovers": "Asia_Clovers",
    "asia konako card art": "Asia_Konako_CardART",
    "asia lvl 4 card": "Asia_Lvl4-Card",
    "asia swimsuit": "Asia_BloodArtisan",
    "asia xenovia dxd": "Asia_Xenovia-DXD",
    "asia xenovia leash": "Asia_Xenovia_Leash",
    "asia xenovia sparkly": "Asia_Xenovia_Sparkly",
    "baka and test minami": "Minami_8511",
    "blair maka mangapanel": "Blair_Maka_Panel_Page_",
    "blair maka panel": "Blair_Maka_Panel_Page_",
    "blair orange kiss": "Blair_OrangeKiss",
    "blood artisan asia": "Asia_BloodArtisan",
    "blood artisan blair": "Blair_BloodArtisan",
    "coby tribute card": "koby_tribute_trading_card",
    "death minatsuki": "Minatsuki_DeathCard",
    "devil toga": "Toga_TC_6Power",
    "dragon maid nap": "Kob_Tohru_NAP",
    "dxd hug": "Asia_DXDHUG",
    "ecchi asia sitting": "Asia_Konoko_SittingCard",
    "elze smartphone": "elze_8.5x11",
    "elze the sun": "elze_sun_trading_card",
    "fairytail cast": "mavisposter",
    "forest mavis": "Mavis_Forest",
    "future diary murmur": "Murmur",
    "homura seven of wands": "homura_seven_of_wands_tradingcard",
    "kob tohru omurice": "Kob_Tohru_Omurice",
    "kobayashi gift": "kobayashiGift_11x17_fullbleed",
    "kobayashi kabob": "Koba_Kabob",
    "kobayashi omurice": "Kob_Tohru_Omurice",
    "kobayashi tohru gift": "Kobayashi_w_dragons",
    "lisa frank toga": "Toga_LisaFrank",
    "maron not bulma": {
        "8.5x11": "maron_not_bulma_8.5x11",
        "6x9": "maron_not_bulma_6x9",
        "trading card": "maron_not_bulma_6x9",
    },
    "mavis adventure": "Mavis_Adventure",
    "mavis and zeref close": "Mavis_Zeref_Close",
    "mavis forest": "Mavis_Forest",
    "mavis zeref scene": "Mavis_Zeref_Scene",
    "mavis zeref touch": "Mavis_Zeref_Touch",
    "minami queen of wands": "MinamiTCQueen",
    "minatsuki death": "Minatsuki_DeathCard",
    "miss doublefinger card art": {
        "6x9": "miss_doublefinger_6x9",
        "trading card": "miss_doublefinger_trading_card",
    },
    "nami vs doublefinger": {
        "6x9": "nami_vs_miss_doublefinger",
        "trading card": "Nami_DF_Card",
    },
    "one piece duo": "one-piece-duo",
    "pink manga cover toga": "Toga_Manga_Cover",
    "pink shadows mavis": "forest-mavis",
    "power and toga": "TogawPower_CARD",
    "red black white toga": "Himiko Toga  Mask 2",
    "ruby moonlight": "ruby_moonlight_8.5x11",
    "spice and wolf": "spice-and-wolf",
    "saki the world": "Saki_Micha",
    "star mavis": "Mavis_Star",
    "sylvie hntsdl": "Sylvie_HNSDL",
    "toga 6 coat": {
        "6x9": "TogaCard6_6x9",
        "trading card": "TogaCard6_TCsize",
    },
    "toga aimee nix poster": "Toga_AimeeNyx",
    "toga black mask": "toga-black-mask",
    "toga cammie pink": "TOGA.CAMI",
    "toga dabi black white": "toga-dabi-black-white",
    "toga dabi city": "toga_Dabi_City",
    "toga daylon pink": "Toga_Daylon_pink",
    "toga daylon red": "Toga_daylon_Red",
    "toga dolls": "TOGA.DOLLS",
    "toga devil": "Toga_TC_6Power",
    "toga in the middle": "Toga_SPLIT",
    "toga manga cover": "Toga_Manga_Cover",
    "toga mva cover": "Toga_Manga_Cover",
    "toga neon": "Toga_Neon_11x17",
    "toga ochaco awk hug": "Toga_Ocha_AwkHug",
    "toga ochaco fight knife": "Toga_Ocha_Fight_Knife",
    "toga ochaco point": "TogaChaco_insert",
    "toga pink aimee ny": "Toga_AimeeNyx",
    "toga pink hearts": "Toga_Pink",
    "toga red neon": "Toga_Neon",
    "toga rare card": {
        "6x9": "TogaRAREcard_6x9",
        "trading card": "TogaRARE_ENG_TC",
    },
    "toga rare stab": {
        "6x9": "Toga_RareStab_6x9",
        "trading card": "Toga_RareStab_TC",
    },
    "toga rarestab": {
        "6x9": "Toga_RareStab_6x9",
        "trading card": "Toga_RareStab_TC",
    },
    "toga sparkle": "Toga_Sparkle.jpg",
    "toga sparkle purple": "Toga_Sparkle_Purple",
    "toga trail": "toga_trail_6x9",
    "toga tsu grayscale": "Toga_Tsu_grayscale",
    "toga twice dance": "TogaTwice_dance_11x17_fix",
    "toga v ochaco purple": "TogaOchaco_bi_85x11",
    "tt toga": "ecchi-toga-flash",
    "uraka v toga cover red bg": "TogaOcha_Cover_WhiteBG",
    "spy family girls": "spyxfamily_selfie_trading_card",
    "blair purple paws og": "purple-paws-blair",
}

_NORMALIZED_OVERRIDES: dict[str, dict[str, str] | str] | None = None


@dataclass
class Artwork:
    key: str
    filename: str
    label: str
    source: str
    suffix: str
    data: bytes | None
    path: Path | None
    normalized: str
    tokens: set[str]


def stable_id(name: str, material: str, size: str) -> int:
    digest = hashlib.sha1(f"{name}|{material}|{size}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "artwork"


def normalize(value: str) -> str:
    text = Path(str(value)).stem.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"([a-z])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([a-z])", r"\1 \2", text)
    text = text.replace("_", " ").replace("-", " ").replace(".", " ")
    for before, after in PHRASE_REPLACEMENTS:
        text = text.replace(before, after)
    text = text.replace("8 5x11", "8.5x11").replace("8 5 11", "8.5x11")
    text = text.replace("85x11", "8.5x11").replace("8-5x11", "8.5x11")
    text = text.replace("8511", "8.5x11").replace("811", "8.5x11")
    text = text.replace("2 5x3 5", "trading card").replace("2 5 3 5", "trading card")
    text = re.sub(r"[^a-z0-9.]+", " ", text)

    parts: list[str] = []
    for raw_token in text.split():
        token = TOKEN_REPLACEMENTS.get(raw_token, raw_token)
        if not token:
            continue
        for part in token.split():
            if part and part not in STOPWORDS:
                parts.append(part)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def normalized_tokens(value: str) -> set[str]:
    return set(normalize(value).split())


def item_key(name: str) -> str:
    return normalize(name)


def override_fragment(name: str, size: str) -> str | None:
    global _NORMALIZED_OVERRIDES
    if _NORMALIZED_OVERRIDES is None:
        _NORMALIZED_OVERRIDES = {normalize(key): value for key, value in OVERRIDES.items()}

    override = _NORMALIZED_OVERRIDES.get(item_key(name))
    if isinstance(override, dict):
        return override.get(size) or override.get("default")
    return override


def format_bonus(item: dict, artwork: Artwork) -> int:
    file_text = artwork.filename.lower()
    bonus = 0

    if item["size"] == "trading card" and any(token in file_text for token in ("trading", "tc", "card", "2.5x3.5")):
        bonus += 22
    if item["size"] == "6x9" and any(token in file_text for token in ("6x9", "69", "6.25x9.25")):
        bonus += 22
    if item["size"] == "8.5x11" and any(token in file_text for token in ("8.5x11", "8-5x11", "85x11", "8511", "811")):
        bonus += 22
    if item["size"] == "11x17" and "11x17" in file_text:
        bonus += 22
    if item["size"] == "11x17" and any(token in file_text for token in ("holographic", "paper-print-11x17", "poster")):
        bonus += 10

    if "holographic" in item["material"].lower():
        bonus += 2
        if "holographic" in file_text:
            bonus += 12
    if item["material"] == "Paper poster" and "paper-print-11x17" in file_text:
        bonus += 12
    if item["material"] == "Paper print" and "paper-print-8-5x11" in file_text:
        bonus += 12
    if item["material"] == "Metal trading card" and any(token in file_text for token in ("metal-trading-card", "trading_card", "tcsize")):
        bonus += 12
    return bonus


def score_match(item: dict, artwork: Artwork) -> tuple[float, str]:
    fragment = override_fragment(item["name"], item["size"])
    if fragment and fragment.lower() in artwork.filename.lower():
        return (160 + format_bonus(item, artwork), f"override match: {fragment}")

    item_norm = normalize(item["name"])
    item_tokens = set(item_norm.split())
    if not item_norm or not item_tokens or not artwork.tokens:
        return (0, "")

    shared = item_tokens & artwork.tokens
    if not shared:
        return (0, "")

    union = item_tokens | artwork.tokens
    jaccard = len(shared) / len(union)
    seq = SequenceMatcher(None, item_norm, artwork.normalized).ratio()
    score = max(jaccard * 100, seq * 88)

    if item_tokens <= artwork.tokens:
        score = max(score, 96)
    elif artwork.tokens <= item_tokens and len(artwork.tokens) >= 2 and seq > 0.55:
        score = max(score, 82)

    if len(shared) == 1 and len(item_tokens) > 1 and seq < 0.7:
        score -= 30

    score += format_bonus(item, artwork)
    note = f"tokens {len(shared)}/{len(item_tokens)}; sequence {seq:.2f}"
    return (score, note)


def iter_zip_artwork(zip_path: Path) -> list[Artwork]:
    artworks: list[Artwork] = []

    def add_artwork(filename: str, source: str, data: bytes) -> None:
        path = Path(filename)
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            return
        label = image_name_from_filename(path.name)
        artworks.append(Artwork(
            key=f"{source}:{filename}",
            filename=path.name,
            label=label,
            source=source,
            suffix=path.suffix.lower(),
            data=data,
            path=None,
            normalized=normalize(path.name),
            tokens=normalized_tokens(path.name),
        ))

    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix in IMAGE_SUFFIXES:
                add_artwork(info.filename, "artwork zip", archive.read(info))
            elif suffix == ".zip":
                nested_data = archive.read(info)
                with zipfile.ZipFile(io.BytesIO(nested_data)) as nested:
                    for nested_info in nested.infolist():
                        if nested_info.is_dir():
                            continue
                        nested_suffix = Path(nested_info.filename).suffix.lower()
                        if nested_suffix in IMAGE_SUFFIXES:
                            add_artwork(
                                nested_info.filename,
                                f"nested zip: {Path(info.filename).name}",
                                nested.read(nested_info),
                            )

    return artworks


def iter_corrections_artwork(corrections_dir: Path) -> list[Artwork]:
    artworks: list[Artwork] = []
    if not corrections_dir.exists():
        return artworks

    def add_artwork(filename: str, source: str, data: bytes | None, path: Path | None) -> None:
        art_path = Path(filename)
        if art_path.suffix.lower() not in IMAGE_SUFFIXES:
            return
        label = image_name_from_filename(art_path.name)
        artworks.append(Artwork(
            key=f"{source}:{filename}",
            filename=art_path.name,
            label=label,
            source=source,
            suffix=art_path.suffix.lower(),
            data=data,
            path=path,
            normalized=normalize(art_path.name),
            tokens=normalized_tokens(art_path.name),
        ))

    for path in sorted(corrections_dir.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            add_artwork(path.name, f"corrections: {path.parent.name}", None, path)
        elif suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    nested_suffix = Path(info.filename).suffix.lower()
                    if nested_suffix in IMAGE_SUFFIXES:
                        add_artwork(
                            info.filename,
                            f"corrections zip: {path.name}",
                            archive.read(info),
                            None,
                        )

    return artworks


def iter_fallback_artwork(catalog_dir: Path) -> list[Artwork]:
    artworks: list[Artwork] = []
    if not catalog_dir.exists():
        return artworks

    for path in sorted(catalog_dir.iterdir()):
        if not path.is_file() or path.name == "manifest.json" or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        label = image_name_from_filename(path.name)
        artworks.append(Artwork(
            key=f"fallback:{path.name}",
            filename=path.name,
            label=label,
            source="existing catalog image",
            suffix=path.suffix.lower(),
            data=None,
            path=path,
            normalized=normalize(path.name),
            tokens=normalized_tokens(path.name),
        ))
    return artworks


def read_artwork_bytes(artwork: Artwork) -> bytes:
    if artwork.data is not None:
        return artwork.data
    if artwork.path:
        return artwork.path.read_bytes()
    raise ValueError(f"No artwork data for {artwork.filename}")


def crop_for_catalog(image: Image.Image, item: dict) -> Image.Image:
    if item_key(item["name"]) != "toga trail":
        return image

    width, height = image.size
    # The source file includes a blurred print-bleed surround. Keep the clean
    # inner artwork for the phone catalog view.
    left = int(width * 0.03)
    top = int(height * 0.214)
    right = int(width * 0.971)
    bottom = int(height * 0.842)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def write_web_image(artwork: Artwork, item: dict, output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"{stable_id(item['name'], item['material'], item['size'])}-{slugify(item['material'])}-{slugify(item['size'])}-{slugify(item['name'])}.jpg"
    output_path = output_dir / output_name

    with Image.open(io.BytesIO(read_artwork_bytes(artwork))) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {"RGB", "L"}:
            background = Image.new("RGB", image.size, "white")
            if "A" in image.mode:
                background.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
            else:
                background.paste(image.convert("RGB"))
            image = background
        else:
            image = image.convert("RGB")
        image = crop_for_catalog(image, item)
        image.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        image.save(output_path, "JPEG", quality=82, optimize=True, progressive=True)

    return f"/prints/current-inventory/{output_name}"


def correlate(inventory: list[dict], artworks: list[Artwork], output_dir: Path, threshold: float) -> tuple[list[dict], list[dict]]:
    products: list[dict] = []
    audit: list[dict] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_image in output_dir.glob("*.jpg"):
        stale_image.unlink()

    for item in inventory:
        scored = [(score_match(item, artwork), artwork) for artwork in artworks]
        scored = [entry for entry in scored if entry[0][0] > 0]
        scored.sort(key=lambda entry: (entry[0][0], format_bonus(item, entry[1]), entry[1].filename), reverse=True)

        best = scored[0] if scored else None
        if best and best[0][0] >= threshold:
            (score, note), artwork = best
            image = write_web_image(artwork, item, output_dir)
            product = {
                "id": stable_id(item["name"], item["material"], item["size"]),
                "name": item["name"],
                "image": image,
                "material": item["material"],
                "size": item["size"],
            }
            products.append(product)
            audit.append({
                **product,
                "status": "matched",
                "matched_artwork": artwork.filename,
                "source": artwork.source,
                "score": f"{score:.1f}",
                "match_note": note,
            })
        else:
            score = best[0][0] if best else 0
            artwork = best[1] if best else None
            audit.append({
                "name": item["name"],
                "material": item["material"],
                "size": item["size"],
                "status": "needs artwork review",
                "image": "",
                "matched_artwork": artwork.filename if artwork else "",
                "source": artwork.source if artwork else "",
                "score": f"{score:.1f}" if best else "",
                "match_note": best[0][1] if best else "No candidate artwork",
            })

    products.sort(key=lambda row: (format_sort(row), row["name"].lower()))
    audit.sort(key=lambda row: (row["status"] != "matched", format_sort(row), row["name"].lower()))
    return products, audit


def format_sort(row: dict) -> tuple[int, str]:
    order = {
        ("Paper poster", "11x17"): 0,
        ("Paper print", "8.5x11"): 1,
        ("Holographic poster", "11x17"): 2,
        ("Metal print", "12x18"): 3,
        ("Metal print", "10x12"): 4,
        ("Metal print", "6x9"): 5,
        ("Metal trading card", "trading card"): 6,
    }
    return (order.get((row.get("material"), row.get("size")), 99), str(row.get("size") or ""))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-docx", type=Path, default=Path("documents/Current_Inventory_Lst with Photos to USe.docx"))
    parser.add_argument("--artwork-zip", type=Path, default=Path("ALL ARTWORK /Merch_Art LeahClark-20260505T183511Z-3-001.zip"))
    parser.add_argument("--corrections-dir", type=Path, default=Path("../Corrections"))
    parser.add_argument("--fallback-catalog-dir", type=Path, default=Path("prints/catalog"))
    parser.add_argument("--image-output-dir", type=Path, default=Path("prints/current-inventory"))
    parser.add_argument("--output", type=Path, default=Path("data/product-catalog.json"))
    parser.add_argument("--csv-output", type=Path, default=Path("documents/leah-indianapolis-popcon-catalog.csv"))
    parser.add_argument("--audit-output", type=Path, default=Path("documents/leah-current-inventory-artwork-audit.csv"))
    parser.add_argument("--threshold", type=float, default=76)
    args = parser.parse_args()

    inventory = extract_inventory(args.inventory_docx)
    artworks = (
        iter_corrections_artwork(args.corrections_dir)
        + iter_zip_artwork(args.artwork_zip)
        + iter_fallback_artwork(args.fallback_catalog_dir)
    )
    products, audit = correlate(inventory, artworks, args.image_output_dir, args.threshold)

    data = {
        "source": str(args.inventory_docx),
        "artwork_source": str(args.artwork_zip),
        "corrections_source": str(args.corrections_dir),
        "snapshot_date": date.today().isoformat(),
        "product_fields": CATALOG_FIELDS,
        "counts": {
            "inventory_items": len(inventory),
            "artwork_candidates": len(artworks),
            "visible": len(products),
            "needs_artwork_review": sum(1 for row in audit if row["status"] != "matched"),
        },
        "products": products,
        "audit": audit,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv_output, products, CATALOG_FIELDS)
    write_csv(args.audit_output, audit, AUDIT_FIELDS)
    print(json.dumps(data["counts"], indent=2))


if __name__ == "__main__":
    main()
