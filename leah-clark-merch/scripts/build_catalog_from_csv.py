#!/usr/bin/env python3
"""Build the QR catalog JSON from a simplified catalog CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


CATALOG_FIELDS = ["name", "image", "material", "size"]


def stable_id(name: str, material: str, size: str) -> int:
    digest = hashlib.sha1(f"{name}|{material}|{size}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def clean_row(row: dict) -> dict:
    return {
        "name": str(row.get("name") or row.get("image_name") or "").strip(),
        "image": str(row.get("image") or "").strip(),
        "material": str(row.get("material") or "").strip(),
        "size": str(row.get("size") or "").strip(),
    }


def build_catalog(csv_path: Path) -> dict:
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [field for field in CATALOG_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        products = []
        for row in reader:
            product = clean_row(row)
            if not product["name"] or not product["material"] or not product["size"]:
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
            "products": len(products),
            "visible": sum(1 for product in products if product["image"]),
            "needs_image": sum(1 for product in products if not product["image"]),
        },
        "products": products,
        "audit": [product for product in products if not product["image"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("documents/leah-indianapolis-popcon-catalog.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("data/product-catalog.json"))
    args = parser.parse_args()

    catalog = build_catalog(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(catalog["counts"], indent=2))


if __name__ == "__main__":
    main()
