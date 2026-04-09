#!/usr/bin/env python3
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT = ROOT / "screenshots" / "dashboard.png"
OUTPUT = ROOT / "screenshots" / "cortexos-intro-cover.png"


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
        --bg: #07111d;
        --panel: rgba(8, 15, 25, 0.86);
        --line: rgba(255, 255, 255, 0.12);
        --text: #f5f7fb;
        --muted: rgba(231, 238, 247, 0.78);
        --accent: #8fd3ff;
      }}
      * {{
        box-sizing: border-box;
      }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(44, 126, 221, 0.18), transparent 36%),
          linear-gradient(180deg, #061120 0%, #03070e 100%);
      }}
      .frame {{
        width: 1600px;
        height: 900px;
        position: relative;
        overflow: hidden;
        background: var(--bg);
      }}
      .bg {{
        position: absolute;
        inset: 0;
        background:
          linear-gradient(180deg, rgba(3, 9, 18, 0.28), rgba(3, 9, 18, 0.72)),
          url("{SCREENSHOT.as_uri()}") center center / cover no-repeat;
        filter: saturate(1.05);
        transform: scale(1.03);
      }}
      .noise {{
        position: absolute;
        inset: 0;
        background:
          linear-gradient(180deg, rgba(255,255,255,0.03), transparent 22%),
          linear-gradient(90deg, rgba(255,255,255,0.02), transparent 20%, transparent 80%, rgba(255,255,255,0.02));
      }}
      .content {{
        position: absolute;
        inset: 0;
        display: flex;
        align-items: stretch;
        justify-content: space-between;
        padding: 56px;
      }}
      .left {{
        width: 52%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 28px 28px 28px 0;
      }}
      .left-panel {{
        width: fit-content;
        max-width: 760px;
        padding: 26px 28px 28px;
        border-radius: 30px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(4, 10, 18, 0.72), rgba(4, 10, 18, 0.56));
        box-shadow: 0 28px 60px rgba(0, 0, 0, 0.26);
        backdrop-filter: blur(14px);
      }}
      .eyebrow {{
        width: fit-content;
        padding: 10px 16px;
        border: 1px solid var(--line);
        border-radius: 999px;
        font-size: 18px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
        background: rgba(5, 11, 18, 0.52);
        backdrop-filter: blur(10px);
      }}
      h1 {{
        margin: 18px 0 12px;
        font-size: 76px;
        line-height: 0.96;
        letter-spacing: -0.05em;
        color: var(--text);
      }}
      .tagline {{
        max-width: 680px;
        font-size: 24px;
        line-height: 1.28;
        color: var(--muted);
      }}
      .meta {{
        display: flex;
        gap: 14px;
        margin-top: 28px;
        flex-wrap: wrap;
      }}
      .pill {{
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(5, 11, 18, 0.5);
        color: #dde7f0;
        font-size: 18px;
      }}
      .cta {{
        display: flex;
        align-items: center;
        gap: 18px;
        padding-left: 8px;
      }}
      .play {{
        width: 96px;
        height: 96px;
        border-radius: 999px;
        background: linear-gradient(180deg, rgba(152, 216, 255, 0.92), rgba(107, 191, 255, 0.82));
        box-shadow: 0 18px 50px rgba(18, 106, 179, 0.34);
        display: grid;
        place-items: center;
      }}
      .triangle {{
        width: 0;
        height: 0;
        border-left: 24px solid #04111f;
        border-top: 15px solid transparent;
        border-bottom: 15px solid transparent;
        margin-left: 6px;
      }}
      .cta-copy {{
        display: flex;
        flex-direction: column;
        gap: 4px;
      }}
      .cta-copy strong {{
        font-size: 34px;
        color: var(--text);
        letter-spacing: -0.03em;
      }}
      .cta-copy span {{
        font-size: 22px;
        color: var(--muted);
      }}
      .right {{
        width: 34%;
        display: flex;
        align-items: flex-end;
        justify-content: flex-end;
      }}
      .card {{
        width: 100%;
        max-width: 430px;
        padding: 26px 28px;
        border-radius: 28px;
        border: 1px solid var(--line);
        background: var(--panel);
        box-shadow: 0 28px 60px rgba(0, 0, 0, 0.32);
        backdrop-filter: blur(18px);
      }}
      .card-title {{
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent);
        margin-bottom: 18px;
      }}
      .card-copy {{
        font-size: 30px;
        line-height: 1.18;
        color: var(--text);
        letter-spacing: -0.03em;
      }}
      .card-copy small {{
        display: block;
        margin-top: 16px;
        font-size: 20px;
        line-height: 1.35;
        color: var(--muted);
        letter-spacing: 0;
      }}
    </style>
  </head>
  <body>
    <div class="frame">
      <div class="bg"></div>
      <div class="noise"></div>
      <div class="content">
        <div class="left">
          <div class="left-panel">
            <div class="eyebrow">GitHub Product Intro</div>
            <h1>CortexOS</h1>
            <div class="tagline">
              An Explainable Memory Operating System for AI Agents.
            </div>
            <div class="meta">
              <div class="pill">13.76s</div>
              <div class="pill">1080p</div>
              <div class="pill">Dashboard + Product Walkthrough</div>
            </div>
          </div>
          <div class="cta">
            <div class="play"><div class="triangle"></div></div>
            <div class="cta-copy">
              <strong>Watch the intro</strong>
              <span>Short product presentation for GitHub visitors</span>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="card">
            <div class="card-title">What It Shows</div>
            <div class="card-copy">
              Memory retrieval with explainability, timeline, conflicts, and product UI.
              <small>
                Local-first operation with temporal reasoning and conflict-aware retrieval.
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""

    tmp_html = ROOT / "screenshots" / ".cortexos-intro-cover.html"
    tmp_html.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path="/usr/bin/google-chrome",
                headless=True,
                args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(tmp_html.as_uri(), wait_until="load", timeout=60_000)
            page.screenshot(path=str(OUTPUT))
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    print(OUTPUT)


if __name__ == "__main__":
    main()
