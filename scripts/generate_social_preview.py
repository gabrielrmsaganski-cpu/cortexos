#!/usr/bin/env python3
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT = ROOT / "screenshots" / "dashboard.png"
OUTPUT = ROOT / "screenshots" / "cortexos-social-preview.png"


def main() -> None:
    if not SCREENSHOT.exists():
        raise SystemExit(f"Missing screenshot source: {SCREENSHOT}")

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <style>
      :root {{
        color-scheme: dark;
        --bg: #050b13;
        --panel: rgba(6, 13, 22, 0.74);
        --line: rgba(255, 255, 255, 0.10);
        --text: #f3f7fb;
        --muted: rgba(223, 231, 240, 0.84);
        --accent: #86cbff;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(58, 132, 208, 0.22), transparent 32%),
          radial-gradient(circle at bottom right, rgba(29, 83, 138, 0.18), transparent 30%),
          linear-gradient(180deg, #071120 0%, #03060d 100%);
      }}
      .frame {{
        width: 1280px;
        height: 640px;
        position: relative;
        overflow: hidden;
        background: var(--bg);
      }}
      .bg {{
        position: absolute;
        inset: 0;
        background:
          linear-gradient(90deg, rgba(3, 8, 16, 0.92) 0%, rgba(3, 8, 16, 0.84) 42%, rgba(3, 8, 16, 0.34) 100%),
          url("{SCREENSHOT.as_uri()}") center center / cover no-repeat;
        transform: scale(1.02);
      }}
      .grid {{
        position: absolute;
        inset: 0;
        background-image:
          linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
        background-size: 64px 64px;
        mask-image: linear-gradient(180deg, rgba(0,0,0,0.5), transparent 85%);
      }}
      .content {{
        position: absolute;
        inset: 0;
        padding: 52px;
        display: flex;
        justify-content: space-between;
        align-items: stretch;
      }}
      .left {{
        width: 62%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }}
      .eyebrow {{
        width: fit-content;
        padding: 10px 15px;
        border: 1px solid var(--line);
        border-radius: 999px;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        background: rgba(5, 10, 18, 0.42);
        backdrop-filter: blur(10px);
      }}
      h1 {{
        margin: 22px 0 10px;
        font-size: 88px;
        line-height: 0.96;
        letter-spacing: -0.055em;
        color: var(--text);
      }}
      .tagline {{
        max-width: 740px;
        font-size: 30px;
        line-height: 1.22;
        letter-spacing: -0.03em;
        color: var(--muted);
      }}
      .chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 28px;
      }}
      .chip {{
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(5, 10, 18, 0.42);
        font-size: 18px;
        color: #dfe7f0;
      }}
      .foot {{
        display: flex;
        align-items: center;
        gap: 16px;
      }}
      .play {{
        width: 74px;
        height: 74px;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: linear-gradient(180deg, rgba(146, 213, 255, 0.98), rgba(103, 185, 250, 0.9));
        box-shadow: 0 14px 42px rgba(21, 99, 167, 0.34);
      }}
      .triangle {{
        width: 0;
        height: 0;
        border-left: 20px solid #03111d;
        border-top: 13px solid transparent;
        border-bottom: 13px solid transparent;
        margin-left: 5px;
      }}
      .foot strong {{
        display: block;
        font-size: 32px;
        line-height: 1.05;
        color: var(--text);
        letter-spacing: -0.03em;
      }}
      .foot span {{
        display: block;
        margin-top: 4px;
        font-size: 19px;
        color: var(--muted);
      }}
      .right {{
        width: 27%;
        display: flex;
        align-items: flex-end;
      }}
      .panel {{
        width: 100%;
        padding: 22px 24px;
        border-radius: 28px;
        border: 1px solid var(--line);
        background: var(--panel);
        box-shadow: 0 22px 56px rgba(0, 0, 0, 0.28);
        backdrop-filter: blur(18px);
      }}
      .panel-title {{
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 15px;
        margin-bottom: 14px;
      }}
      .panel-copy {{
        color: var(--text);
        font-size: 26px;
        line-height: 1.16;
        letter-spacing: -0.03em;
      }}
      .panel-copy small {{
        display: block;
        margin-top: 14px;
        color: var(--muted);
        font-size: 18px;
        line-height: 1.3;
        letter-spacing: 0;
      }}
    </style>
  </head>
  <body>
    <div class="frame">
      <div class="bg"></div>
      <div class="grid"></div>
      <div class="content">
        <div class="left">
          <div>
            <div class="eyebrow">Explainable memory platform for agents</div>
            <h1>CortexOS</h1>
            <div class="tagline">
              Temporal reasoning, conflict-aware retrieval, and product-grade explainability.
            </div>
            <div class="chips">
              <div class="chip">FastAPI</div>
              <div class="chip">Qdrant</div>
              <div class="chip">Hybrid retrieval</div>
              <div class="chip">Reranking</div>
              <div class="chip">Local-first</div>
            </div>
          </div>
          <div class="foot">
            <div class="play"><div class="triangle"></div></div>
            <div>
              <strong>Watch the intro</strong>
              <span>13.76s product presentation for GitHub visitors</span>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="panel">
            <div class="panel-title">What stands out</div>
            <div class="panel-copy">
              Query Studio, Explain Center, Conflict Center, Timeline, and operations visibility.
              <small>
                Built for real agent memory workflows instead of thin vector search wrappers.
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""

    tmp_html = ROOT / "screenshots" / ".cortexos-social-preview.html"
    tmp_html.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path="/usr/bin/google-chrome",
                headless=True,
                args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1280, "height": 640})
            page.goto(tmp_html.as_uri(), wait_until="load", timeout=60_000)
            page.screenshot(path=str(OUTPUT))
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    print(OUTPUT)


if __name__ == "__main__":
    main()
