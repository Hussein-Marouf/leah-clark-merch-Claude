#!/usr/bin/env python3
"""Build the QR catalog from the current inventory DOCX and local catalog images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CATALOG_FIELDS = ["name", "image", "material", "size"]
AUDIT_FIELDS = [
    "name",
    "material",
    "size",
    "status",
    "image",
    "matched_image_name",
    "matched_image_format",
    "match_note",
]


def stable_id(name: str, material: str, size: str) -> int:
    digest = hashlib.sha1(f"{name}|{material}|{size}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def xml_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "t":
            parts.append(node.text or "")
        elif tag in {"br", "cr"}:
            parts.append("\n")
        elif tag == "tab":
            parts.append("\t")
    return "".join(parts)


def cell_text(cell: ET.Element) -> str:
    paragraphs = cell.findall(".//w:p", NS)
    return "\n".join(xml_text(paragraph) for paragraph in paragraphs).strip()


def iter_docx_blocks(docx_path: Path):
    with zipfile.ZipFile(docx_path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    body = root.find("w:body", NS)
    if body is None:
        return

    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = xml_text(child).strip()
            if text:
                yield [line.strip() for line in text.splitlines() if line.strip()]
        elif tag == "tbl":
            lines: list[str] = []
            for row in child.findall(".//w:tr", NS):
                for cell in row.findall("./w:tc", NS):
                    text = cell_text(cell)
                    lines.extend(line.strip() for line in text.splitlines() if line.strip())
            if lines:
                yield lines


def category_for(line: str) -> tuple[str, str] | None:
    text = line.lower().strip()
    if text.startswith("large metal prints"):
        return ("Metal print", "12x18")
    if text.startswith("medium metal prints"):
        return ("Metal print", "10x12")
    if text.startswith("small metal prints"):
        return ("Metal print", "6x9")
    if text.startswith("metal trading cards"):
        return ("Metal trading card", "trading card")
    if text.startswith("holograph"):
        return ("Holographic poster", "11x17")
    if text.startswith("poster 11x17"):
        return ("Paper poster", "11x17")
    if text.startswith("standard prints"):
        return ("Paper print", "8.5x11")
    return None


def should_skip_inventory_line(line: str) -> bool:
    text = line.lower().strip()
    return (
        not text
        or text == "toga photo op specials"
        or text.startswith("photo special")
        or text.startswith("text:")
        or text.startswith("prints:")
    )


def extract_inventory(docx_path: Path) -> list[dict]:
    inventory: list[dict] = []
    current_category: tuple[str, str] | None = None

    for lines in iter_docx_blocks(docx_path):
        for line in lines:
            category = category_for(line)
            if category:
                current_category = category
                continue
            if current_category is None or should_skip_inventory_line(line):
                continue

            material, size = current_category
            inventory.append({
                "name": line,
                "material": material,
                "size": size,
            })

    return inventory


NORMALIZE_REPLACEMENTS = {
    "&": " and ",
    "_": " ",
    "b/w": "black white",
    "wbg": "black white",
    "kobayashi": "koby",
    "koabayashi": "koby",
    "coby": "koby",
    "uraraka": "ochaco",
    "uraka": "ochaco",
    "manga panel": "panel",
    "seasonal": "",
    "og": "",
}


def normalize_name(value: str) -> str:
    text = value.lower().strip()
    for before, after in NORMALIZE_REPLACEMENTS.items():
        text = text.replace(before, after)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def name_tokens(value: str) -> tuple[str, ...]:
    return tuple(sorted(normalize_name(value).split()))


def image_name_from_filename(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"^\d+-", "", stem)
    prefixes = [
        "paper-print-11x17-",
        "paper-print-8-5x11-",
        "holographic-print-holographic-",
        "metal-print-large-metal-",
        "metal-print-medium-metal-",
        "metal-print-6x9-",
        "metal-trading-card-trading-card-",
    ]
    for prefix in prefixes:
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
            break
    return stem.replace("-", " ").strip()


def image_format(entry: dict) -> tuple[str, str]:
    image_type = str(entry.get("image_type") or "").lower()
    size = str(entry.get("size") or "").lower()
    if "holographic" in image_type:
        return ("Holographic poster", "11x17")
    if "trading" in image_type:
        return ("Metal trading card", "trading card")
    if "metal" in image_type:
        return ("Metal print", {
            "large metal": "12x18",
            "medium metal": "10x12",
            "6x9": "6x9",
        }.get(size, size))
    if "paper" in image_type:
        return ("Paper print" if size == "8.5x11" else "Paper poster", size)
    return (str(entry.get("image_type") or ""), str(entry.get("size") or ""))


def load_local_images(manifest_path: Path, catalog_dir: Path) -> list[dict]:
    images: list[dict] = []
    seen_urls: set[str] = set()

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest.get("images", []):
            local_url = entry.get("local_url")
            if not local_url:
                continue
            material, size = image_format(entry)
            image_name = str(entry.get("name") or image_name_from_filename(local_url)).strip()
            images.append({
                "name": image_name,
                "normalized_name": normalize_name(image_name),
                "tokens": name_tokens(image_name),
                "image": local_url,
                "material": material,
                "size": size,
            })
            seen_urls.add(local_url)

    for image_path in sorted(catalog_dir.iterdir() if catalog_dir.exists() else []):
        if not image_path.is_file() or image_path.name == "manifest.json":
            continue
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            continue
        local_url = f"/prints/catalog/{image_path.name}"
        if local_url in seen_urls:
            continue
        image_name = image_name_from_filename(image_path.name)
        images.append({
            "name": image_name,
            "normalized_name": normalize_name(image_name),
            "tokens": name_tokens(image_name),
            "image": local_url,
            "material": "",
            "size": "",
        })

    return images


def score_match(item: dict, image: dict) -> tuple[int, str]:
    item_normalized = normalize_name(item["name"])
    item_tokens = name_tokens(item["name"])

    if image["normalized_name"] == item_normalized:
        score = 100
        note = "exact name"
    elif image["tokens"] == item_tokens and item_tokens:
        score = 95
        note = "same words"
    else:
        return (0, "")

    if image["material"] == item["material"] and image["size"] == item["size"]:
        return (score + 30, f"{note}; exact format")
    if image["material"] == item["material"]:
        return (score + 20, f"{note}; same material")
    if image["size"] == item["size"]:
        return (score + 10, f"{note}; same size")
    return (score, note)


def correlate_inventory(inventory: list[dict], images: list[dict]) -> tuple[list[dict], list[dict]]:
    catalog: list[dict] = []
    audit: list[dict] = []
    seen_catalog_keys: set[tuple] = set()

    for item in inventory:
        candidates: list[tuple[int, str, dict]] = []
        for image in images:
            score, note = score_match(item, image)
            if score:
                candidates.append((score, note, image))

        if candidates:
            score, note, image = sorted(candidates, key=lambda value: (value[0], value[2]["image"]), reverse=True)[0]
            dedupe_key = (name_tokens(item["name"]), item["material"], item["size"])
            catalog_item = {
                "id": stable_id(item["name"], item["material"], item["size"]),
                "name": item["name"],
                "image": image["image"],
                "material": item["material"],
                "size": item["size"],
            }
            status = "matched"
            if dedupe_key in seen_catalog_keys:
                status = "duplicate skipped"
            else:
                seen_catalog_keys.add(dedupe_key)
                catalog.append(catalog_item)
            audit.append({
                **{field: catalog_item[field] for field in CATALOG_FIELDS},
                "status": status,
                "matched_image_name": image["name"],
                "matched_image_format": f"{image['material']} {image['size']}".strip(),
                "match_note": f"{note}; score {score}",
            })
        else:
            audit.append({
                "name": item["name"],
                "material": item["material"],
                "size": item["size"],
                "status": "missing image",
                "image": "",
                "matched_image_name": "",
                "matched_image_format": "",
                "match_note": "No exact normalized name or same-word image filename match",
            })

    catalog.sort(key=lambda item: (item["material"], item["size"], item["name"].lower()))
    audit.sort(key=lambda item: (item["status"] != "matched", item["status"], item["material"], item["size"], item["name"].lower()))
    return catalog, audit


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
    parser.add_argument("--manifest", type=Path, default=Path("prints/catalog/manifest.json"))
    parser.add_argument("--catalog-dir", type=Path, default=Path("prints/catalog"))
    parser.add_argument("--output", type=Path, default=Path("data/product-catalog.json"))
    parser.add_argument("--csv-output", type=Path, default=Path("documents/leah-indianapolis-popcon-catalog.csv"))
    parser.add_argument("--audit-output", type=Path, default=Path("documents/leah-inventory-image-match-audit.csv"))
    args = parser.parse_args()

    inventory = extract_inventory(args.inventory_docx)
    images = load_local_images(args.manifest, args.catalog_dir)
    catalog, audit = correlate_inventory(inventory, images)

    data = {
        "source": str(args.inventory_docx),
        "image_source": str(args.catalog_dir),
        "snapshot_date": date.today().isoformat(),
        "product_fields": CATALOG_FIELDS,
        "counts": {
            "inventory_items": len(inventory),
            "local_images": len(images),
            "visible": len(catalog),
            "missing_image": sum(1 for row in audit if row["status"] == "missing image"),
        },
        "products": catalog,
        "audit": audit,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv_output, catalog, CATALOG_FIELDS)
    write_csv(args.audit_output, audit, AUDIT_FIELDS)
    print(json.dumps(data["counts"], indent=2))


if __name__ == "__main__":
    main()
