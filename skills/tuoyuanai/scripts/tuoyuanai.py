#!/usr/bin/env python3
"""TuoyuanAI: submit, query and download server-owned creative sessions."""
from __future__ import annotations
import argparse
import http.client
import json
import mimetypes
from pathlib import Path
import sys
import time
import urllib.parse
import uuid
from _client import Client, SkillError, emit, safe_url
from _downloads import download_items
from _treatment import build_treatment


def positive(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("Expected a positive integer.")
    return value


def submit(client, args):
    request_id = str(args.request_id or uuid.uuid4())
    message = args.message or ""
    if args.message_file:
        message = Path(args.message_file).expanduser().read_text(encoding="utf-8-sig")
    body = {"requestId": request_id}
    if args.command == "send":
        if not message.strip():
            raise SkillError("send requires a nonempty message.")
        body["sessionId"] = args.session_id
    if message:
        body["message"] = message
    if args.settings_json:
        settings = json.loads(args.settings_json)
        if not isinstance(settings, dict):
            raise SkillError("--settings-json must be an object.")
        body["settings"] = settings
    if args.creation_type:
        body["creationType"] = args.creation_type
    if args.attachment_id:
        body["attachmentIds"] = args.attachment_id
    if args.allow_media:
        body["allowMedia"] = True
    # Printed before admission so callers can recover an uncertain response
    # using the same identity/body, without automatically resubmitting work.
    emit({"type": "request", "request_id": request_id}, stream=sys.stderr)
    result = client.request("POST", "/session", body)
    emit({"type": "accepted", "request_id": request_id, **result,
          "project_url": client.base + result["projectUrl"]})


def query(client, args):
    deadline = time.monotonic() + args.wait
    cursor = args.after_seq
    while True:
        result = client.session(args.session_id, after_seq=cursor, limit=args.limit)
        emit(result)
        cursor = result["nextSeq"]
        if result["hasMore"]:
            if not args.wait:
                return
            continue
        if not args.wait or result["status"] not in {"queued", "running", "waiting"}:
            return
        if time.monotonic() >= deadline:
            emit({"type": "wait_timeout", "session_id": args.session_id, "after_seq": cursor,
                  "message": "Server execution continues. Query again for progress."})
            return
        time.sleep(min(3, max(0, deadline - time.monotonic())))

def upload(client, args):
    path = Path(args.path).expanduser().resolve()
    if not path.is_file():
        raise SkillError("Upload path must be a regular file.")
    size = path.stat().st_size
    if not 0 < size <= 200 * 1024 * 1024:
        raise SkillError("Files must be nonempty and at most 200 MiB; server purpose limits also apply.")
    content_type = args.content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    client.session(args.session_id)
    prepared = client.request("POST", "/uploads", {
        "purpose": "assistant_attachment", "filename": path.name,
        "content_type": content_type, "size_bytes": size,
        "context": {"session_id": args.session_id},
    })
    emit({"type": "upload_prepared", "upload_id": prepared["upload_id"]})
    if prepared["method"] != "PUT":
        raise SkillError("Unsupported upload method.")
    if prepared["transport"] == "multipart":
        part_size = prepared.get("part_size")
        if type(part_size) is not int or not 1024 * 1024 <= part_size <= 16 * 1024 * 1024:
            raise SkillError("Unsupported multipart size.")
        parts, deadline = [], time.monotonic() + 600
        with path.open("rb") as payload:
            number = 0
            while block := payload.read(part_size):
                number += 1
                for attempt in range(3):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise SkillError("Multipart upload reached its ten-minute limit; use cancel-upload with the returned upload_id.")
                    try:
                        target = client.request("POST", f'/uploads/{prepared["upload_id"]}/parts/{number}', {}, timeout=min(60, remaining))
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise SkillError("Multipart upload reached its ten-minute limit.")
                        with client.open("PUT", target["url"], body=block,
                                         headers={**target.get("headers", {}), "Content-Length": str(len(block))},
                                         timeout=min(60, remaining)) as response:
                            etag = response.headers.get("ETag")
                        if not etag:
                            raise SkillError("Object storage did not acknowledge the uploaded part.")
                        parts.append({"part_number": number, "etag": etag})
                        emit({"type": "upload_progress", "part": number, "bytes": min(number * part_size, size), "total_bytes": size})
                        break
                    except SkillError as error:
                        if not error.retryable or attempt == 2:
                            raise
                        time.sleep(min(2 ** attempt, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SkillError("Multipart upload reached its ten-minute limit.")
        client.request("POST", f'/uploads/{prepared["upload_id"]}/complete', {"parts": parts}, timeout=min(60, remaining))
    else:
        if prepared["transport"] == "api":
            relative = prepared["url"]
            if not relative.startswith("/openapi/uploads/"):
                raise SkillError("Unexpected API upload path.")
            url, auth = client.base + relative, True
        elif prepared["transport"] == "direct":
            url, auth = prepared["url"], False
        else:
            raise SkillError("Unsupported upload transport.")
        with path.open("rb") as payload:
            with client.open("PUT", url, body=payload, headers={**prepared["headers"], "Content-Length": str(size)},
                             auth=auth, timeout=120):
                pass
    result = client.request("POST", "/attachments", {
        "session_id": args.session_id, "upload_id": prepared["upload_id"],
    })
    emit({"type": "attachment", **result})


def results(client, session):
    graph = client.canvas(session)
    # Current canvas content, not links extracted from chat or stale previews.
    # Imported materials can also be image/audio/text nodes: callers select IDs.
    items = [{key: node.get(key) for key in
              ("id", "node_key", "node_type", "generation_kind", "knowledge_doc_id", "asset_role",
               "label", "status", "error", "url", "mime_type", "body")}
             for node in graph["nodes"] if node["node_type"] in {"image", "video", "audio", "text"}]
    return {**client.links(session), "nodes": items, "generation_runs": graph["generation_runs"]}


def exportable(node):
    if node["node_type"] == "text":
        return bool(node["body"]) and node["status"] in {None, "idle", "done"}
    return node["status"] == "done"


def download(client, args):
    if bool(args.session_id) == bool(args.urls):
        raise SkillError("Provide either a session ID or --urls.")
    if args.urls:
        if args.node_id:
            raise SkillError("--node-id requires a session ID.")
        if len(args.urls) > 200:
            raise SkillError("At most 200 URLs per download request.")
        items = [{"index": index, "url": safe_url(url)} for index, url in enumerate(dict.fromkeys(args.urls), 1)]
        links = {}
    else:
        session = client.session(args.session_id)
        items = results(client, session)["nodes"]
        if args.node_id:
            requested = set(args.node_id)
            items = [node for node in items if node["id"] in requested]
            if {node["id"] for node in items} != requested:
                raise SkillError("One or more requested nodes do not belong to this canvas.")
            if any(not exportable(node) for node in items):
                raise SkillError("Requested nodes are not complete; no files were downloaded.")
        else:
            items = [node for node in items if exportable(node)]
        links = client.links(session)
    if not items:
        raise SkillError("No completed output nodes in this canvas.")
    outcome = download_items(client, items, args, emit)
    emit({**outcome, **links})
    if outcome["failed"]:
        raise SystemExit(2)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    s = sub.add_parser("sessions")
    s.add_argument("--before-id", type=positive)
    s.add_argument("--limit", type=positive, default=50)
    for cmd in ("create", "send"):
        s = sub.add_parser(cmd)
        if cmd == "send":
            s.add_argument("session_id", type=positive)
        message = s.add_mutually_exclusive_group()
        message.add_argument("--message")
        message.add_argument("--message-file")
        s.add_argument("--request-id", type=uuid.UUID)
        s.add_argument("--creation-type", choices=["graphic", "storyboard"])
        s.add_argument("--settings-json")
        s.add_argument("--attachment-id", action="append", type=positive)
        s.add_argument("--allow-media", action="store_true")
    s = sub.add_parser("query")
    s.add_argument("session_id", type=positive)
    s.add_argument("--after-seq", type=int, default=0)
    s.add_argument("--limit", type=positive, default=100)
    s.add_argument("--wait", type=int, default=0, choices=range(0, 1801), metavar="0..1800")
    s = sub.add_parser("upload")
    s.add_argument("session_id", type=positive)
    s.add_argument("path")
    s.add_argument("--content-type", help="Explicit MIME type, for example audio/webm for an audio-only WebM.")
    for cmd in ("attachments", "results", "stop"):
        s = sub.add_parser(cmd)
        s.add_argument("session_id", type=positive)
    s = sub.add_parser("cancel-upload")
    s.add_argument("upload_id", type=uuid.UUID)
    s = sub.add_parser("treatment")
    s.add_argument("session_id", type=positive)
    s.add_argument("--outline-file", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--studio", default="")
    s.add_argument("--workers", type=int, choices=range(1, 9), default=5, metavar="1..8")
    s.add_argument("--max-mb", type=positive, default=512)
    s = sub.add_parser("download")
    s.add_argument("session_id", type=positive, nargs="?")
    s.add_argument("--urls", nargs="+")
    s.add_argument("--node-id", action="append", type=positive)
    s.add_argument("--output-dir", default="~/Downloads/tuoyuanai_results")
    s.add_argument("--prefix", default="")
    s.add_argument("--workers", type=int, choices=range(1, 9), default=5, metavar="1..8")
    s.add_argument("--max-mb", type=positive, default=512)
    return p


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args()
    try:
        client = Client(require_auth=not (args.command == "download" and args.urls and not args.session_id))
        if args.command in {"create", "send"}:
            submit(client, args)
        elif args.command in {"query", "upload", "download"}:
            {"query": query, "upload": upload, "download": download}[args.command](client, args)
        elif args.command == "treatment":
            session = client.session(args.session_id)
            nodes = [node for node in results(client, session)["nodes"] if exportable(node)]
            result = build_treatment(client, session, nodes, args)
            emit(result)
            if result["type"] != "complete":
                raise SystemExit(2)
        elif args.command == "sessions":
            params = {"limit": args.limit}
            if args.before_id:
                params["beforeId"] = args.before_id
            emit(client.request("GET", "/sessions?" + urllib.parse.urlencode(params)))
        elif args.command == "results":
            emit(results(client, client.session(args.session_id)))
        else:
            method, path = {
                "capabilities": ("GET", "/capabilities"),
                "attachments": ("GET", f'/session/{getattr(args, "session_id", "")}/attachments'),
                "stop": ("POST", f'/session/{getattr(args, "session_id", "")}/stop'),
                "cancel-upload": ("DELETE", f'/uploads/{getattr(args, "upload_id", "")}'),
            }[args.command]
            emit(client.request(method, path))
    except KeyboardInterrupt:
        emit({"error": "Client interrupted; server tasks continue. Query or explicitly stop the session."}, stream=sys.stderr)
        sys.exit(130)
    except SkillError as exc:
        emit({"error": str(exc)}, stream=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:
        emit({"error": f"Local file, transport or API contract error ({type(exc).__name__}); no retry performed."}, stream=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
