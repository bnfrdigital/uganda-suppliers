import json, os, sys, urllib.request, urllib.error

TOKEN = os.environ["NOTION_TOKEN"].strip()
DB_ID = os.environ["NOTION_DB_ID"].strip()

# Team-only fields: kept in Notion, left out of the public file.
# Add or remove names here (they must match the Notion property names exactly).
EXCLUDE = {"Status", "Contributor", "Source"}

def query(cursor=None):
    body = {"page_size": 100}
    if cursor:
        body["start_cursor"] = cursor
    req = urllib.request.Request(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("Notion said:", e.read().decode())
        sys.exit(1)

def text(prop):
    t = prop["type"]
    v = prop[t]
    if t in ("title", "rich_text"):
        return "".join(x["plain_text"] for x in v)
    if t in ("select", "status"):
        return v["name"] if v else ""
    if t == "multi_select":
        return ", ".join(x["name"] for x in v)
    if t == "date":
        return v["start"] if v else ""
    if t == "people":
        return ", ".join(x.get("name", "") for x in v)
    if t == "unique_id":
        if not v or v.get("number") is None:
            return ""
        return f'{v["prefix"]}-{v["number"]:04d}' if v.get("prefix") else str(v["number"])
    if t in ("number", "checkbox", "url", "email", "phone_number"):
        return "" if v is None else str(v)
    return ""

rows, cursor = [], None
while True:
    data = query(cursor)
    rows += data["results"]
    if not data["has_more"]:
        break
    cursor = data["next_cursor"]

def title_of(row):
    return next((text(p) for p in row["properties"].values() if p["type"] == "title"), "")

rows.sort(key=lambda r: title_of(r).lower())

lines = ["# Uganda responsible tourism suppliers", f"{len(rows)} entries", ""]
for row in rows:
    props = row["properties"]
    title = next((text(p) for p in props.values() if p["type"] == "title"), "Untitled")
    lines.append(f"## {title}")
    for name, p in props.items():
        if p["type"] != "title" and name not in EXCLUDE:
            val = text(p)
            if val:
                lines.append(f"- {name}: {val}")
    lines.append("")

with open("ideas.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
