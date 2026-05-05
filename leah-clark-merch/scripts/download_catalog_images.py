#!/usr/bin/env python3
"""Download locally cached catalog images from snapshot image links."""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def slugify(value: object, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return slug[:80] or fallback


def file_extension(content_type: str, data: bytes, url: str) -> str:
    content_type = content_type.split(";", 1)[0].strip().lower()
    if content_type in IMAGE_EXTENSIONS:
        return IMAGE_EXTENSIONS[content_type]
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return ".webp"
    guessed = mimetypes.guess_extension(content_type)
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if guessed == ".jpeg" else guessed
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".bin"


def looks_like_html(data: bytes, content_type: str) -> bool:
    sample = data[:512].lstrip().lower()
    return "text/html" in content_type.lower() or sample.startswith(b"<!doctype html") or sample.startswith(b"<html")


def download(url: str, timeout: int) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 LeahCatalogImageDownloader/1.0",
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "")
        final_url = response.geturl()
    return data, content_type, final_url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("data/product-catalog.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("prints/catalog"))
    parser.add_argument("--manifest", type=Path, default=Path("prints/catalog/manifest.json"))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--rewrite-catalog", action="store_true")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--local-only-availability", action="store_true", dest="local_only")
    parser.add_argument("--csv-output", type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    products = catalog.get("products", [])
    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    success_count = 0
    failure_count = 0

    for product in products:
        image_url = str(product.get("image") or "").strip()
        if not image_url:
            continue

        if image_url.startswith("/"):
            local_path = Path(image_url.lstrip("/"))
            entry = {
                "id": product.get("id"),
                "image_name": product.get("image_name") or product.get("name"),
                "size": product.get("size"),
                "remote_image": image_url,
                "status": "already local",
                "local_url": image_url,
            }
            if local_path.exists():
                entry["bytes"] = local_path.stat().st_size
                success_count += 1
            else:
                entry["status"] = "failed"
                entry["error"] = "local image path does not exist"
                failure_count += 1
                if args.rewrite_catalog and args.local_only:
                    product["image"] = None
                    product["image_url"] = ""
            manifest.append(entry)
            continue

        product_id = product.get("id")
        filename_base = "-".join([
            str(product_id),
            slugify(product.get("size"), "size"),
            slugify(product.get("image_name") or product.get("name"), "image"),
        ])

        entry = {
            "id": product_id,
            "image_name": product.get("image_name") or product.get("name"),
            "size": product.get("size"),
            "remote_image": image_url,
            "status": "pending",
        }

        try:
            data, content_type, final_url = download(image_url, args.timeout)
            if looks_like_html(data, content_type):
                raise ValueError("download returned HTML, likely Google sign-in or permission page")

            ext = file_extension(content_type, data, final_url)
            if ext == ".bin":
                raise ValueError(f"download was not recognized as an image ({content_type or 'unknown content type'})")

            output_path = args.out_dir / f"{filename_base}{ext}"
            output_path.write_bytes(data)
            local_url = f"/prints/catalog/{output_path.name}"

            entry.update({
                "status": "downloaded",
                "local_path": str(output_path),
                "local_url": local_url,
                "content_type": content_type,
                "bytes": len(data),
            })
            success_count += 1

            if args.rewrite_catalog:
                product["image"] = local_url
                product["image_url"] = local_url
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            entry.update({
                "status": "failed",
                "error": str(error),
            })
            failure_count += 1

            if args.rewrite_catalog and args.local_only:
                product["image"] = None
                product["image_url"] = ""

        manifest.append(entry)
        time.sleep(args.sleep)

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({
        "catalog": str(args.catalog),
        "attempted": len(manifest),
        "downloaded": success_count,
        "failed": failure_count,
        "images": manifest,
    }, indent=2) + "\n", encoding="utf-8")

    if args.rewrite_catalog:
        products_by_id = {product.get("id"): product for product in products}
        for audit_entry in catalog.get("audit", []):
            product = products_by_id.get(audit_entry.get("id"))
            if not product:
                continue
            for field in (
                "size",
                "image",
                "image_name",
            ):
                if field in product:
                    audit_entry[field] = product[field]

        catalog["audit"] = [
            entry for entry in catalog.get("audit", [])
            if not products_by_id.get(entry.get("id"), {}).get("image")
        ]
        catalog["counts"] = {
            "products": len(products),
            "visible": sum(1 for product in products if product.get("image")),
            "needs_image": sum(1 for product in products if not product.get("image")),
        }
        args.catalog.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    if args.csv_output:
        product_fields = catalog.get("product_fields") or [
            "size",
            "image",
            "image_name",
        ]
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=product_fields, lineterminator="\n")
            writer.writeheader()
            for product in products:
                writer.writerow({field: product.get(field) for field in product_fields})

    print(json.dumps({
        "attempted": len(manifest),
        "downloaded": success_count,
        "failed": failure_count,
        "manifest": str(args.manifest),
    }, indent=2))


if __name__ == "__main__":
    main()
