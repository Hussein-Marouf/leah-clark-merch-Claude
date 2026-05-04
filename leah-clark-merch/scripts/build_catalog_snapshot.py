#!/usr/bin/env python3
"""Build a sanitized product catalog from the convention inventory workbook.

The source workbook can contain private logistics columns. This script only
exports the product fields needed by the app: quantity, image type, name, image,
size, price, and availability, plus an internal id for order stability.
"""

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


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

SOURCE_URL = "https://docs.google.com/spreadsheets/d/16zOCNXmvol34Cw0Hgz3YCSbBuFkFN2zakv1mXInQQdw/edit?usp=sharing"

PRICE_BY_TYPE_SIZE = {
    ("paper print", "8.5x11"): 15.0,
    ("paper print", "11x17"): 25.0,
}


def normalize_name(value: object) -> str:
    text = str(value or "").lower().strip().replace("&", "and")
    replacements = {
        "coby": "koby",
        "kobayashi": "koby",
        "koabayashi": "koby",
        "uraraka": "ochaco",
        "uraka": "ochaco",
        "b/w": "black white",
        "wbg": "black white",
        "aimee ny": "aimee nix",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)

    text = re.sub(
        r"\b(lg|large|standard|std|small|med|medium|metal|metals|print|prints|"
        r"card|cards|holo|holographic|art|poster|seasonal|new|og)\b",
        " ",
        text,
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def product_shape(sheet_name: str) -> tuple[str, str]:
    sheet = sheet_name.lower()
    if "holographic" in sheet:
        return "holographic print", "holographic"
    if "trading" in sheet:
        return "metal trading card", "trading card"
    if "metal" in sheet:
        if "large" in sheet:
            return "metal print", "large metal"
        if "medium" in sheet:
            return "metal print", "medium metal"
        if "6x9" in sheet:
            return "metal print", "6x9"
        return "metal print", "metal"
    if "11x17" in sheet:
        return "paper print", "11x17"
    if "8.5x11" in sheet or "standard" in sheet:
        return "paper print", "8.5x11"
    return "other", ""


def drive_file_id(url: str) -> str:
    match = re.search(r"/d/([^/]+)|id=([^&]+)", str(url))
    if not match:
        return ""
    return match.group(1) or match.group(2) or ""


def col_row(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)(\d+)", ref)
    if not match:
        raise ValueError(f"Invalid cell reference: {ref}")

    col = 0
    for char in match.group(1):
        col = col * 26 + ord(char) - 64
    return col, int(match.group(2))


def stable_id(*parts: str) -> int:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def clean_number(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def cell_value(cell: ET.Element, shared_strings: list[str]) -> object:
    value_type = cell.attrib.get("t")
    value_node = cell.find("main:v", NS)

    if value_type == "s" and value_node is not None:
        return shared_strings[int(value_node.text or "0")]

    if value_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//main:t", NS))

    if value_node is None:
        return ""

    raw = value_node.text or ""
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def load_workbook_rows(path: Path) -> tuple[list[dict], list[dict]]:
    product_rows: list[dict] = []
    art_links: list[dict] = []

    with zipfile.ZipFile(path) as archive:
        archive_names = archive.namelist()

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive_names:
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", NS):
                shared_strings.append(
                    "".join(text.text or "" for text in item.findall(".//main:t", NS))
                )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        workbook_rels = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels_root
        }

        sheets_node = workbook.find("main:sheets", NS)
        if sheets_node is None:
            return product_rows, art_links

        for sheet in sheets_node:
            sheet_name = sheet.attrib["name"]
            image_type, size = product_shape(sheet_name)
            if image_type == "other":
                continue

            relation_id = sheet.attrib[f"{{{NS['r']}}}id"]
            sheet_path = "xl/" + workbook_rels[relation_id]
            sheet_root = ET.fromstring(archive.read(sheet_path))

            rel_path = str(Path(sheet_path).parent / "_rels" / (Path(sheet_path).name + ".rels"))
            sheet_rels: dict[str, str] = {}
            if rel_path in archive_names:
                rel_root = ET.fromstring(archive.read(rel_path))
                sheet_rels = {
                    rel.attrib["Id"]: rel.attrib.get("Target", "")
                    for rel in rel_root
                }

            rows: dict[int, dict[int, object]] = {}
            for row in sheet_root.findall(".//main:sheetData/main:row", NS):
                row_number = int(row.attrib["r"])
                rows[row_number] = {}
                for cell in row.findall("main:c", NS):
                    col, _ = col_row(cell.attrib["r"])
                    rows[row_number][col] = cell_value(cell, shared_strings)

            hyperlinks_by_row: dict[int, list[str]] = {}
            for hyperlink in sheet_root.findall(".//main:hyperlink", NS):
                ref = hyperlink.attrib.get("ref", "")
                _, row_number = col_row(ref)
                target = sheet_rels.get(hyperlink.attrib.get(f"{{{NS['r']}}}id"), "")
                if target:
                    hyperlinks_by_row.setdefault(row_number, []).append(target)

            headers = rows.get(1, {})

            def find_header(*needles: str) -> int | None:
                for col, header in headers.items():
                    header_text = str(header or "").lower()
                    if any(needle in header_text for needle in needles):
                        return col
                return None

            item_col = 1
            preferred_col = find_header("preferred")
            current_col = find_header("current")
            bring_col = find_header("bring")

            for row_number, cells in sorted(rows.items()):
                if row_number == 1:
                    continue

                name = str(cells.get(item_col, "") or "").strip()
                if not name:
                    continue

                preferred = clean_number(cells.get(preferred_col)) if preferred_col else None
                current = clean_number(cells.get(current_col)) if current_col else None
                bring = clean_number(cells.get(bring_col)) if bring_col else None

                if bring_col and bring is not None:
                    quantity = max(0, int(bring))
                elif current is not None:
                    quantity = max(0, int(current))
                elif preferred is not None:
                    quantity = max(0, int(preferred))
                else:
                    quantity = 0

                if quantity <= 0:
                    continue

                direct_links = hyperlinks_by_row.get(row_number, [])
                row = {
                    "sheet": sheet_name,
                    "row": row_number,
                    "name": name,
                    "normalized_name": normalize_name(name),
                    "image_type": image_type,
                    "size": size,
                    "quantity": quantity,
                    "direct_links": direct_links,
                }
                product_rows.append(row)

                for link in direct_links:
                    file_id = drive_file_id(link)
                    if file_id:
                        art_links.append({
                            "sheet": sheet_name,
                            "row": row_number,
                            "name": name,
                            "normalized_name": row["normalized_name"],
                            "url": link,
                            "file_id": file_id,
                        })

    return product_rows, art_links


def build_catalog(workbook_path: Path) -> dict:
    product_rows, art_links = load_workbook_rows(workbook_path)

    art_by_name: dict[str, list[dict]] = {}
    for link in art_links:
        art_by_name.setdefault(link["normalized_name"], []).append(link)

    products: list[dict] = []
    audit: list[dict] = []

    for row in product_rows:
        direct_file_id = drive_file_id(row["direct_links"][0]) if row["direct_links"] else ""
        match = None
        image_resolution = "missing"
        if direct_file_id:
            match = {
                "file_id": direct_file_id,
                "url": row["direct_links"][0],
            }
            image_resolution = "direct"
        elif row["normalized_name"] in art_by_name:
            match = art_by_name[row["normalized_name"]][0]
            image_resolution = "same-name"

        price = PRICE_BY_TYPE_SIZE.get((row["image_type"], row["size"]))
        image = (
            f"https://drive.google.com/thumbnail?id={match['file_id']}&sz=w1000"
            if match else None
        )

        if not image:
            availability = "needs image"
        elif price is None:
            availability = "needs price"
        elif row["quantity"] <= 0:
            availability = "sold out"
        else:
            availability = "available"

        product = {
            "id": stable_id(row["image_type"], row["size"], row["name"]),
            "quantity": row["quantity"],
            "image_type": row["image_type"],
            "name": row["name"],
            "image": image,
            "size": row["size"],
            "price": price,
            "availability": availability,
        }

        products.append(product)

        if availability != "available":
            audit.append({
                **product,
                "source_tab": row["sheet"],
                "source_row": row["row"],
                "image_resolution": image_resolution,
            })

    products.sort(key=lambda item: (
        item["availability"] != "available",
        item["image_type"],
        item["size"],
        item["name"].lower(),
    ))
    audit.sort(key=lambda item: (item["availability"], item["image_type"], item["size"], item["name"].lower()))

    return {
        "source": SOURCE_URL,
        "snapshot_date": date.today().isoformat(),
        "product_fields": ["quantity", "image_type", "name", "image", "size", "price", "availability"],
        "price_notes": {
            "paper print 8.5x11": 15.0,
            "paper print 11x17": 25.0,
            "other product types": "needs price in the snapshot before becoming orderable",
        },
        "counts": {
            "products": len(products),
            "available": sum(1 for product in products if product["availability"] == "available"),
            "needs_image": sum(1 for product in products if product["availability"] == "needs image"),
            "needs_price": sum(1 for product in products if product["availability"] == "needs price"),
        },
        "products": products,
        "audit": audit,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/product-catalog.json"))
    parser.add_argument("--csv-output", type=Path)
    args = parser.parse_args()

    catalog = build_catalog(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    if args.csv_output:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=catalog["product_fields"],
                lineterminator="\n",
            )
            writer.writeheader()
            for product in catalog["products"]:
                writer.writerow({field: product.get(field) for field in catalog["product_fields"]})

    print(json.dumps(catalog["counts"], indent=2))


if __name__ == "__main__":
    main()
