"""Content contract. Standard-library only; this module never writes files."""

from datetime import date
import json
import re
from urllib.parse import unquote_plus

SCHEMA_VERSION = 1
SLUG = r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*"
NODE_ID = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
RECORD_KEYS = set("schema_version slug title speaker published duration duration_seconds video_id video_url caption_source verified sermon_start sermon_end card_summary section_intro page_title description subtitle kicker disclaimer figcaption footer_paragraphs outline_heading ledger_heading ledger_intro ledger_caption movements ledger".split())
NODE_KEYS = set("id start heading scripture_mentions bullets children".split())
ROW_KEYS = set("id reference reference_query treatment time phrase anchor_node_id version version_source reference_note".split())
RESERVED_IDS = {"main-content", "outline-heading", "scripture-ledger", "ledger-heading", "page-title"}


class InvalidRecord(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidRecord(message)


def timestamp(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def seconds(value):
    require(isinstance(value, str) and bool(re.fullmatch(r"\d{1,3}:[0-5]\d", value)), "Expected a minutes:seconds string")
    minutes, remainder = map(int, value.split(":"))
    return minutes * 60 + remainder


def flatten(nodes):
    for node in nodes:
        yield node
        yield from flatten(node["children"])


def plain_values(value):
    """Reject presentation markup, CSS, and project paths anywhere in content."""
    if isinstance(value, str):
        require(not re.search(r"[<>{}]|style\s*=|(?:^|[\s/])(?:site|assets|sermons|archive|content)/|(?:index|archive)\.html|\b(?:color|background|display|font-size|margin|padding)\s*:\s*[^;]+;", value, re.I), "Content must be prose/data, without HTML, CSS, or site paths")
    elif isinstance(value, dict):
        for key, item in value.items():
            plain_values(key)
            plain_values(item)
    elif isinstance(value, list):
        for item in value:
            plain_values(item)
    else:
        require(value is None or type(value) in (int, bool), "Unexpected content value")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")


def rich_text(parts):
    require(isinstance(parts, list) and bool(parts), "Expected text segments")
    for part in parts:
        require(isinstance(part, dict) and set(part) == {"kind", "text"}, "Invalid text segment")
        require(part["kind"] in ("text", "strong", "source_link"), "Invalid text segment kind")
        text(part["text"], "segment")


def validate(record):
    require(isinstance(record, dict) and set(record) == RECORD_KEYS, "Unexpected or missing record fields")
    plain_values(record)
    require(type(record["schema_version"]) is int and record["schema_version"] == SCHEMA_VERSION, "Unsupported schema version")
    for key in RECORD_KEYS - {"schema_version", "duration_seconds", "sermon_start", "sermon_end", "figcaption", "footer_paragraphs", "movements", "ledger"}:
        text(record[key], key)
    require(bool(re.fullmatch(SLUG, record["slug"])), "Invalid slug")
    for key in ("published", "verified"):
        try:
            require(date.fromisoformat(record[key]).isoformat() == record[key], f"Invalid {key}")
        except ValueError as error:
            raise InvalidRecord(f"Invalid {key}") from error
    require(record["slug"].startswith(record["published"] + "-"), "Slug must begin with published date")
    duration = record["duration_seconds"]
    require(type(duration) is int and duration > 0 and seconds(record["duration"]) == duration, "Duration mismatch")
    require(bool(re.fullmatch(r"[A-Za-z0-9_-]{11}", record["video_id"])), "Invalid video ID")
    require(record["video_url"] == "https://www.youtube.com/watch?v=" + record["video_id"], "Video URL mismatch")
    for key in ("sermon_start", "sermon_end"):
        value = record[key]
        require((key == "sermon_end" and value is None) or (type(value) is int and 0 <= value <= duration), f"Invalid {key}")
    require(record["sermon_end"] is None or record["sermon_end"] >= record["sermon_start"], "Reversed sermon boundaries")
    rich_text(record["figcaption"])
    require(isinstance(record["footer_paragraphs"], list) and bool(record["footer_paragraphs"]), "Missing footer")
    for paragraph in record["footer_paragraphs"]:
        rich_text(paragraph)
    nodes = {}
    starts = []

    def visit(items, depth=1):
        require(isinstance(items, list), "Movements/children must be lists")
        require(not items or depth <= 3, "Outline exceeds depth 3")
        for node in items:
            require(isinstance(node, dict) and set(node) == NODE_KEYS, "Unexpected or missing node fields")
            node_id = node["id"]
            require(isinstance(node_id, str) and bool(re.fullmatch(NODE_ID, node_id)), "Invalid node ID")
            require(node_id not in nodes and node_id not in RESERVED_IDS and not node_id.startswith("ledger-"), "Duplicate/reserved node ID")
            nodes[node_id] = node
            require(type(node["start"]) is int and record["sermon_start"] <= node["start"] <= (record["sermon_end"] or duration), "Node timestamp outside sermon/video")
            starts.append(node["start"])
            text(node["heading"], "heading")
            require(isinstance(node["bullets"], list) and bool(node["bullets"]), "Node needs bullets")
            for bullet in node["bullets"]:
                text(bullet, "bullet")
            mentions = node["scripture_mentions"]
            require(isinstance(mentions, list) and all(isinstance(x, str) for x in mentions), "Invalid Scripture mention set")
            require(len(set(mentions)) == len(mentions), "Duplicate Scripture mention in node")
            visit(node["children"], depth + 1)

    visit(record["movements"])
    require(bool(nodes) and starts == sorted(starts), "Outline must be chronological (ties permitted)")
    require(starts[0] == record["sermon_start"], "First node must match sermon start")
    require(isinstance(record["ledger"], list) and bool(record["ledger"]), "Missing Scripture ledger")
    rows = {}
    times = []
    for row in record["ledger"]:
        require(isinstance(row, dict) and set(row) == ROW_KEYS, "Unexpected or missing ledger fields")
        row_id = row["id"]
        require(isinstance(row_id, str) and bool(re.fullmatch(r"SCR-\d{3,}", row_id)) and row_id not in rows, "Invalid/duplicate Scripture ID")
        rows[row_id] = row
        for key in ("reference", "reference_query", "phrase", "anchor_node_id", "version", "version_source"):
            text(row[key], key)
        require(row["reference_note"] is None or isinstance(row["reference_note"], str), "Invalid reference note")
        require(row["treatment"] in ("read/quoted", "exposited", "referenced"), "Invalid treatment")
        require(bool(re.fullmatch(r"[A-Z][A-Z0-9-]*", row["version"])), "Invalid translation code")
        require(row["version_source"] in ("default", "speaker-named"), "Invalid translation provenance")
        require(row["version_source"] != "default" or row["version"] == "NIV", "Default translation must be NIV; other versions require speaker-named provenance")
        query = row["reference_query"]
        require(bool(re.fullmatch(r"(?:[A-Za-z0-9_.~+-]|%[0-9A-Fa-f]{2})+", query)) and unquote_plus(query) == row["reference"], "Encoded Bible reference mismatch")
        require(type(row["time"]) is int and 0 <= row["time"] <= duration, "Ledger timestamp outside video")
        times.append(row["time"])
        require(row["anchor_node_id"] in nodes, "Unknown canonical outline anchor")
        require(row_id in nodes[row["anchor_node_id"]]["scripture_mentions"], "Canonical anchor must mention its Scripture row")
    require(times == sorted(times), "Ledger must be chronological (ties permitted)")
    mentions = {mention for node in nodes.values() for mention in node["scripture_mentions"]}
    require(mentions == set(rows), "Outline mentions and ledger IDs must match")
    return record


def loads(source):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return validate(json.loads(source, object_pairs_hook=unique_keys))


def dumps(record):
    return json.dumps(validate(record), ensure_ascii=False, indent=2) + "\n"
