#!/usr/bin/env python3
"""Build the QR catalog JSON from a catalog CSV.

The preferred public catalog shape is:

    name,image,material,size

This script also accepts the older image snapshot shape:

    size,image,image_name

For snapshot rows, material and display size are inferred from the source size
category and local image filename.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


CATALOG_FIELDS = ["name", "image", "material", "size"]
SNAPSHOT_NAME_FIELDS = ("name", "image_name")


def display_format(row: dict) -> tuple[str, str]:
    raw_size = str(row.get("size") or "").strip()
    image = str(row.get("image") or "").lower()
    normalized_size = raw_size.lower()

    if row.get("material"):
        return (str(row.get("material") or "").strip(), raw_size)

    if "trading-card" in image or normalized_size == "trading card":
        return ("Metal trading card", "trading card")
    if "large-metal" in image or normalized_size == "large metal":
        return ("Metal print", "12x18")
    if "medium-metal" in image or normalized_size == "medium metal":
        return ("Metal print", "10x12")
    if "metal-print-6x9" in image:
        return ("Metal print", "6x9")
    if "holographic-print" in image or normalized_size == "holographic":
        return ("Holographic print", "11x17")
    if normalized_size == "11x17":
        return ("Paper poster", "11x17")
    if normalized_size == "8.5x11":
        return ("Paper print", "8.5x11")
    if normalized_size == "6x9":
        return ("Metal print", "6x9")
    return ("", raw_size)


def stable_id(name: str, material: str, size: str) -> int:
    digest = hashlib.sha1(f"{name}|{material}|{size}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def clean_row(row: dict) -> dict:
    material, size = display_format(row)
    return {
        "name": str(row.get("name") or row.get("image_name") or "").strip(),
        "image": str(row.get("image") or "").strip(),
        "material": material,
        "size": size,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CATALOG_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CATALOG_FIELDS})


def build_catalog(csv_path: Path) -> dict:
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        has_name = any(field in fieldnames for field in SNAPSHOT_NAME_FIELDS)
        missing = [field for field in ("image", "size") if field not in fieldnames]
        if not has_name:
            missing.append("name or image_name")
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        products = []
        source_rows = 0
        for row in reader:
            source_rows += 1
            product = clean_row(row)
            if not product["name"] or not product["image"] or not product["material"] or not product["size"]:
                continue
            products.append({
                "id": stable_id(product["name"], product["material"], product["size"]),
                **product,
            })

    return {
        "source": str(csv_path),
        "snapshot_date": date.today().isoformat(),
        "product_fields": CATALOG_FIELDS,
        "counts": {
            "source_rows": source_rows,
            "products": len(products),
            "visible": len(products),
            "needs_image": 0,
        },
        "products": products,
        "audit": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("documents/leah-indianapolis-popcon-catalog.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("data/product-catalog.json"))
    parser.add_argument("--csv-output", type=Path)
    args = parser.parse_args()

    catalog = build_catalog(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    if args.csv_output:
        write_csv(args.csv_output, catalog["products"])
    print(json.dumps(catalog["counts"], indent=2))


if __name__ == "__main__":
    main()
