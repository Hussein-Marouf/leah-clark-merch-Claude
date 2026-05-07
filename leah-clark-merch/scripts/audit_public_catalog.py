#!/usr/bin/env python3
"""Audit the public catalog for duplicate rows, duplicate art, and missing files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_products(catalog_path: Path) -> list[dict]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    products = data.get("products")
    if not isinstance(products, list):
        raise ValueError(f"{catalog_path} does not contain a products array")
    return products


def image_path(project_root: Path, product: dict) -> Path:
    image = str(product.get("image") or "").lstrip("/")
    return project_root / image


def product_label(product: dict) -> str:
    return f"{product.get('name')} | {product.get('material')} | {product.get('size')}"


def add_issue(issues: list[str], title: str, rows: list[dict]) -> None:
    issues.append(title)
    for row in rows:
        issues.append(f"  - {product_label(row)}")


def audit_catalog(project_root: Path, catalog_path: Path) -> list[str]:
    products = load_products(catalog_path)
    issues: list[str] = []

    by_product_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    by_category_image_hash: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    by_metal_print_name: dict[str, list[dict]] = defaultdict(list)

    for product in products:
        name = str(product.get("name") or "")
        material = str(product.get("material") or "")
        size = str(product.get("size") or "")

        by_product_key[(normalize(name), material, size)].append(product)
        if material == "Metal print":
            by_metal_print_name[normalize(name)].append(product)

        path = image_path(project_root, product)
        if not path.exists():
            issues.append(f"Missing image: {product_label(product)} -> {path}")
            continue

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        by_category_image_hash[(material, size, digest)].append(product)

    for rows in by_product_key.values():
        if len(rows) > 1:
            add_issue(issues, "Duplicate product row:", rows)

    for (material, size, _digest), rows in by_category_image_hash.items():
        if len(rows) > 1:
            add_issue(issues, f"Duplicate artwork inside {material} {size}:", rows)

    for rows in by_metal_print_name.values():
        if len(rows) > 1:
            add_issue(issues, "Duplicate name across metal print sizes:", rows)

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--catalog", type=Path, default=Path("data/product-catalog.json"))
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    catalog_path = args.catalog if args.catalog.is_absolute() else project_root / args.catalog
    issues = audit_catalog(project_root, catalog_path)

    if issues:
        print("Catalog audit failed:")
        print("\n".join(issues))
        raise SystemExit(1)

    product_count = len(load_products(catalog_path))
    print(
        f"Catalog audit passed: {product_count} products, no duplicate rows, "
        "no same-category duplicate artwork, no duplicate metal-print names, no missing images."
    )


if __name__ == "__main__":
    main()
