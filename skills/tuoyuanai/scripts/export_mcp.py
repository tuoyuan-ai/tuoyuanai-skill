"""Export current MCP receipts without loading or forwarding platform credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

from _client import Client, SkillError, safe_url
from _downloads import download_items
from _treatment import build_treatment


class ReceiptClient(Client):
    def __init__(self, receipt):
        super().__init__()
        self.receipt = receipt

    def request(self, method, path, body=None, *, timeout=60):
        match = re.fullmatch(r"/session/([1-9][0-9]*)/nodes/([1-9][0-9]*)/download", path)
        if method != "GET" or not match or int(match[1]) != self.receipt["session"]["sessionId"]:
            raise SkillError("Export can only read original download receipts from the selected project.")
        result = self.receipt["downloads"].get(match[2])
        if not isinstance(result, dict) or not isinstance(result.get("url"), str):
            raise SkillError("Missing current original-file download receipt for this node.")
        return {"url": safe_url(result["url"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["treatment", "download"])
    parser.add_argument("--receipt-file", required=True)
    parser.add_argument("--outline-file")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--node-id", type=int, action="append")
    parser.add_argument("--studio", default="")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=5)
    parser.add_argument("--max-mb", type=int, default=512)
    args = parser.parse_args()
    try:
        if args.max_mb < 1 or args.max_mb > 2048:
            raise SkillError("--max-mb must be between 1 and 2048.")
        source = Path(args.receipt_file).expanduser()
        if source.stat().st_size > 16 * 1024 * 1024:
            raise SkillError("Receipt file is too large.")
        receipt = json.loads(source.read_text(encoding="utf-8-sig"))
        session = receipt["session"]
        if type(session["sessionId"]) is not int or session["sessionId"] < 1 or not isinstance(session["project"], dict):
            raise SkillError("Use the current session receipt returned by MCP.")
        if session["projectUrl"] != f'/assistant?session={session["sessionId"]}':
            raise SkillError("Project link does not match the selected session.")
        nodes = receipt["nodes"]
        if not isinstance(nodes, list) or len(nodes) > 10000 or not isinstance(receipt["downloads"], dict):
            raise SkillError("Receipt requires current canvas nodes and their download receipts.")
        selected = set(args.node_id or [])
        completed = []
        all_ids = set()
        for node in nodes:
            if type(node.get("id")) is not int or node["id"] < 1 or node["id"] in all_ids:
                raise SkillError("Invalid or repeated node ID in the receipt.")
            all_ids.add(node["id"])
            if selected and node["id"] not in selected:
                continue
            kind = node.get("node_type")
            if kind not in {"image", "video", "audio", "text"}:
                continue
            ready = bool(node.get("body")) and node.get("status") in {None, "idle", "done"} if kind == "text" else node.get("status") == "done"
            if not ready:
                if node["id"] in selected:
                    raise SkillError("Selected node is not complete; no files were downloaded.")
                continue
            completed.append(node)
        if selected and selected != {node["id"] for node in completed}:
            raise SkillError("Selected nodes do not all belong to the completed current canvas.")
        client = ReceiptClient(receipt)
        if args.command == "treatment":
            if not args.outline_file:
                raise SkillError("Treatment export requires --outline-file.")
            result = build_treatment(client, session, completed, args)
        else:
            if not completed:
                raise SkillError("No completed nodes selected.")
            result = download_items(client, completed, SimpleNamespace(**vars(args), session_id=session["sessionId"]), lambda item: print(json.dumps(item, ensure_ascii=False), flush=True))
        print(json.dumps(result, ensure_ascii=False))
        if result["type"] != "complete":
            raise SystemExit(2)
    except (OSError, ValueError, KeyError, TypeError, SkillError) as exc:
        message = str(exc) if isinstance(exc, SkillError) else "Invalid or unreadable export receipt or outline."
        print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
