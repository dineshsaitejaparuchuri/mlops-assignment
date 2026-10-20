"""Render captured terminal text (docs/run_outputs/*) as PNG screenshots.

The text is the real captured output; only the rendering to an image is synthetic.
    python scripts/render_terminal.py
    python scripts/render_terminal.py --ci-ingress  # render the saved hosted Ingress artifact
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path("/System/Library/Fonts/Menlo.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
]
FONT = next((ImageFont.truetype(str(path), 16) for path in FONT_CANDIDATES
             if path.exists()), ImageFont.load_default())
LINE_H = 22
PAD = 18


def render(lines: list[str], title: str, dest: Path) -> None:
    width = max(len(line) for line in lines) * 10 + 2 * PAD
    height = len(lines) * LINE_H + 2 * PAD + 34
    img = Image.new("RGB", (max(width, 760), height), "#1e1e1e")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 30], fill="#3a3a3a")
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse([12 + i * 22, 9, 24 + i * 22, 21], fill=c)
    d.text((100, 6), title, font=FONT, fill="#cccccc")
    y = 30 + PAD
    for line in lines:
        color = "#ffffff"
        if line.startswith("$"):
            color = "#7ee787"
        elif "PASSED" in line or "passed" in line or "exit code 0" in line:
            color = "#a5d6ff"
        elif "WARN" in line or "Warning" in line:
            color = "#e3b341"
        d.text((PAD, y), line, font=FONT, fill=color)
        y += LINE_H
    img.save(dest)
    print("wrote", dest)


def main() -> None:
    ro = ROOT / "docs" / "run_outputs"
    if sys.argv[1:] == ["--ci-ingress"]:
        status = (ro / "ci_run4_ingress_status.txt").read_text().splitlines()
        smoke = (ro / "ci_run4_ingress_smoke.txt").read_text().splitlines()
        lines = [*status, "", *smoke]
        render(lines, "GitHub Actions run #4 - Ingress verification (captured output)",
               OUT / "ci_ingress_verification.png")
        return

    pt = (ro / "pytest_verbose.txt").read_text().splitlines()
    pt = [ln for ln in pt if not ln.startswith(("cachedir", "rootdir", "plugins"))]
    render(pt, "terminal - pytest (captured output)", OUT / "terminal_pytest.png")
    render((ro / "flake8_run.txt").read_text().splitlines(),
           "terminal - flake8 (captured output)", OUT / "terminal_flake8.png")
    tl = [ln for ln in (ro / "train_log.txt").read_text().splitlines()
          if "cv_auc=" in ln or ln.startswith(("Successfully", "Created version"))]
    render(["$ python -m src.train"] + tl, "terminal - training (captured output)",
           OUT / "terminal_train.png")

    tail_lines = lambda f: (ro / f).read_text().splitlines()
    render(tail_lines("docker_run.txt"), "terminal - docker build / run / smoke (captured output)",
           OUT / "docker_build_run.png")
    pods = [ln for ln in tail_lines("k8s_pods.txt")]
    pods = [re.sub(r"\s+<none>\s+<none>$", "", ln) for ln in pods]
    pods = [re.sub(r"\s{2,}", "  ", ln) for ln in pods]
    render(pods, "terminal - kubectl (kind cluster, captured output)",
           OUT / "k8s_pods_services.png")
    render(tail_lines("k8s_smoke.txt"), "terminal - smoke test via port-forward (captured output)",
           OUT / "k8s_smoke_test.png")
    ci = [ln for ln in tail_lines("act_ci_full.txt")
          if re.search(r"(✅|❌|🏁|passed|smoke test)", ln) and "unable to get git" not in ln
          and "Pre " not in ln and "Post " not in ln and "dest=" not in ln]
    ci = [ln.replace("[ci/build-test-train]", "").replace("✅", "[ok]").replace("❌", "[FAIL]").replace("🏁", "[done]").replace("  |", " |").strip() for ln in ci]
    render(["$ scripts/run_ci_local.sh   # act runs .github/workflows/ci.yml"] + ci,
           "local run of the CI workflow (act, captured output)", OUT / "ci_run.png")


if __name__ == "__main__":
    main()
