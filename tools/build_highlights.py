"""Build colour-highlighted copies of the reading documents.

Usage:
    python -I tools/build_highlights.py <app_dir> [<render_dir>]

Reads reading.json (the plan) and seed.json (team names and colours), finds every
phrase on its stated PDF page in docs/src/<doc>.pdf, highlights it in the reader's
colour (Everyone = highlighter yellow), adds a name tag in the page corner, and
writes static/hl/<doc>.pdf plus static/hl/report.json.

Safety: if any phrase is not found on its page, nothing is published and the
script exits with code 1, listing what is missing. Optional <render_dir> gets a
PNG of every highlighted page so a person can check the result by eye.
"""
import io
import json
import os
import sys

import fitz  # PyMuPDF

YELLOW = "#FFF200"


def rgb(hexcode):
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tint(c, k=0.45):
    """Lighter version of a colour so the text under a highlight stays readable."""
    return tuple(1 - (1 - x) * k for x in c)


def main(app, render_dir=None):
    plan = json.load(io.open(os.path.join(app, "reading.json"), encoding="utf-8"))
    seed = json.load(io.open(os.path.join(app, "seed.json"), encoding="utf-8"))
    team = {m["id"]: m for m in seed["meta"]["team"]["members"]}
    src, out = os.path.join(app, "docs", "src"), os.path.join(app, "static", "hl")

    def who(pid):
        if pid == "all":
            return "Everyone", rgb(YELLOW), rgb(YELLOW)
        m = team[pid]
        c = rgb(m["color"])
        return m["name"], tint(c), c

    report, missing, opened = [], [], {}
    for part in plan["parts"]:
        doc = opened.setdefault(part["doc"], fitz.open(os.path.join(src, part["doc"] + ".pdf")))
        page = doc[part["page"] - 1]
        name, fill, solid = who(part["who"])
        found = []
        for ph in part["phrases"]:
            quads = page.search_for(ph, quads=True)
            found.append({"phrase": ph, "hits": len(quads)})
            if not quads:
                missing.append(f'{part["id"]}: "{ph}" not on {part["doc"]} page {part["page"]}')
                continue
            a = page.add_highlight_annot(quads)
            a.set_colors(stroke=fill)
            a.set_info(title=name, content=f'{part["phase"]} · {part["title"]}: {part["why"]}')
            a.update()
        report.append({"id": part["id"], "doc": part["doc"], "page": part["page"], "who": name, "found": found})

    if missing:
        print("NOT PUBLISHED. Missing phrases:")
        for m in missing:
            print("  -", m)
        return 1

    # name tags in the top-right corner of each highlighted page
    tags = {}
    for part in plan["parts"]:
        tags.setdefault((part["doc"], part["page"]), []).append(part)
    for (d, p), parts in tags.items():
        page = opened[d][p - 1]
        w = page.rect.width
        for i, part in enumerate(parts):
            name, fill, solid = who(part["who"])
            r = fitz.Rect(w - 270, 8 + i * 18, w - 8, 23 + i * 18)
            light = (0.299 * solid[0] + 0.587 * solid[1] + 0.114 * solid[2]) > 0.62
            text_col = (0.1, 0.1, 0.11) if light else (1, 1, 1)
            a = page.add_freetext_annot(r, f'{name} · {part["phase"]} · {part["title"]}', fontsize=7.5,
                                        text_color=text_col, fill_color=solid, align=0)
            a.set_info(title=name)
            a.update()

    os.makedirs(out, exist_ok=True)
    for d, doc in opened.items():
        doc.save(os.path.join(out, d + ".pdf"), garbage=3, deflate=True)
        if render_dir:
            os.makedirs(render_dir, exist_ok=True)
            for (dd, p) in tags:
                if dd == d:
                    doc[p - 1].get_pixmap(dpi=70).save(os.path.join(render_dir, f"{d}_p{p}.png"))
    io.open(os.path.join(out, "report.json"), "w", encoding="utf-8").write(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"OK: {len(report)} parts highlighted in {len(opened)} documents, nothing missing.")
    for r in report:
        print(f'  {r["id"]:<3} {r["doc"]:<9} p.{r["page"]:<4} {r["who"]:<11} ' + ", ".join(str(f["hits"]) for f in r["found"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
