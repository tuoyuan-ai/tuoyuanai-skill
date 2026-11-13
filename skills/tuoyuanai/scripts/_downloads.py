"""Bounded parallel downloads with per-file outcomes and exclusive destinations."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes
from pathlib import Path
import time
import urllib.parse

from _client import SkillError, safe_url


def output_directory(value, prefix):
    if len(prefix) > 80 or any(c in prefix for c in '/\\\x00<>:"|?*') or any(ord(c) < 32 for c in prefix) or prefix in {".", ".."}:
        raise SkillError("--prefix must be a filename prefix without path separators.")
    directory = Path(value).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_item(client, item, directory, prefix, max_mb, session_id=None):
    node_id = item.get("id")
    stem = f"{prefix}node-{node_id}" if node_id is not None else f'{prefix}url-{item["index"]}'
    if item.get("node_type") == "text":
        destination = directory / (stem + ".txt")
        body = item["body"].encode("utf-8")
        if len(body) > max_mb * 1024 * 1024:
            raise SkillError("Text output exceeded --max-mb.")
        with destination.open("xb") as handle:
            handle.write(body)
        return {"node_id": node_id, "path": str(destination), "bytes": len(body)}
    if node_id is not None:
        media = client.request("GET", f"/session/{session_id}/nodes/{node_id}/download")
        source = media.get("url")
        if not source:
            raise SkillError("Node has no current media URL.")
        url = safe_url(urllib.parse.urljoin(client.base + "/", source))
    else:
        url = safe_url(item["url"])
    started = time.monotonic()
    # Never forward the platform Access Key to media URLs, even on the same host.
    with client.open("GET", url, timeout=120) as response:
        content_type = response.headers.get_content_type()
        expected = item.get("node_type")
        if expected and content_type != "application/octet-stream" and not content_type.startswith(expected + "/"):
            raise SkillError("Download did not return the expected media type.")
        if not expected and content_type not in {"application/octet-stream", "text/plain", "application/pdf"} and not content_type.startswith(("image/", "video/", "audio/")):
            raise SkillError("URL did not return a media file or supported document.")
        extension = mimetypes.guess_extension(item.get("mime_type") or content_type) or ".bin"
        destination = directory / (stem + extension)
        expected_length = response.headers.get("Content-Length")
        if expected_length and int(expected_length) > max_mb * 1024 * 1024:
            raise SkillError("Download exceeded --max-mb.")
        handle = destination.open("xb")
        try:
            with handle:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > max_mb * 1024 * 1024 or time.monotonic() - started > 120:
                        raise SkillError("Download exceeded the size or time limit.")
                    handle.write(chunk)
                if total == 0 or (expected_length is not None and total != int(expected_length)):
                    raise SkillError("Download was empty or incomplete.")
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    return {"node_id": node_id, "index": item.get("index"), "path": str(destination), "bytes": total}


def download_items(client, items, args, on_result):
    directory = output_directory(args.output_dir, args.prefix)
    downloaded, failed = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(save_item, client, item, directory, args.prefix, args.max_mb, args.session_id): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                outcome = future.result()
                downloaded.append(outcome)
                on_result({"type": "downloaded", **outcome})
            except Exception as exc:
                message = str(exc) if isinstance(exc, SkillError) else ("Output already exists; choose another directory or prefix." if isinstance(exc, FileExistsError) else f"File or transport error ({type(exc).__name__}).")
                outcome = {"node_id": item.get("id"), "index": item.get("index"), "error": message}
                failed.append(outcome)
                on_result({"type": "download_failed", **outcome})
    downloaded.sort(key=lambda item: item.get("node_id") or item.get("index") or 0)
    failed.sort(key=lambda item: item.get("node_id") or item.get("index") or 0)
    return {"type": "partial" if failed and downloaded else "failed" if failed else "complete", "downloaded": downloaded, "failed": failed}
