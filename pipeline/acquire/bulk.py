"""Bulk fetch: stream a pinned download URL to Source.path (large kept sources, e.g. NPPES)."""

from __future__ import annotations

import requests

from pipeline.sources import Source


def fetch(src: Source) -> None:
    assert src.download_url, f"{src.key}: bulk fetch needs a download_url"
    src.path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(src.download_url, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        with open(src.path, "wb") as out:
            for chunk in resp.iter_content(chunk_size=1 << 20):  # 1 MB chunks
                out.write(chunk)
