"""Render captured terminal text (docs/run_outputs/*) as PNG screenshots.

The text is the real captured output; rendering masks the machine-specific workspace
path so screenshots do not publish a local username or download location.
    python scripts/render_terminal.py
    python scripts/render_terminal.py --ci-ingress 9  # render the saved hosted Ingress artifact
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
    lines = lines or ["No lint issues."]
    workspace = str(ROOT)
    lines = [line.replace(workspace, "<workspace>") for line in lines]
    width = max(len(line) for line in lines) * 10 + 2 * PAD
    height = len(lines) * LINE_H + 2 * PAD + 34
    img = Image.new("RGB", (max(width, 760), height), "#1e1e1e")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 30], fill="#30363d")
    d.text((PAD, 6), title, font=FONT, fill="#e6edf3")
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
    if len(sys.argv) == 3 and sys.argv[1] == "--ci-ingress":
        status = (ro / "ci_ingress_status.txt").read_text(encoding="utf-8", errors="replace").splitlines()
        smoke = (ro / "ci_ingress_smoke.txt").read_text(encoding="utf-8", errors="replace").splitlines()
        render([*status, "", *smoke], f"Hosted CI artifact (run #{sys.argv[2]}) - Ingress verification (rendered locally)",
               OUT / "ci_ingress_verification.png")
        return

    pt = (ro / "pytest_verbose.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    pt = [ln for ln in pt if not ln.startswith(("cachedir", "rootdir", "plugins"))]
    render(pt, "terminal - pytest (captured output)", OUT / "terminal_pytest.png")
    render((ro / "flake8_run.txt").read_text(encoding="utf-8", errors="replace").splitlines(),
           "terminal - flake8 (captured output)", OUT / "terminal_flake8.png")
    tl = [ln for ln in (ro / "train_log.txt").read_text(encoding="utf-8", errors="replace").splitlines()
          if "cv_auc=" in ln or ln.startswith(("Successfully", "Created version"))]
    render(["$ python -m src.train"] + tl, "terminal - training (captured output)",
           OUT / "terminal_train.png")

    def tail_lines(filename):
        return (ro / filename).read_text(encoding="utf-8", errors="replace").splitlines()
    render(tail_lines("docker_run.txt"), "terminal - docker build / run / smoke (captured output)",
           OUT / "docker_build_run.png")
    pods = [ln for ln in tail_lines("k8s_pods.txt")]
    pods = [re.sub(r"\s+<none>\s+<none>$", "", ln) for ln in pods]
    pods = [re.sub(r"\s{2,}", "  ", ln) for ln in pods]
    render(pods, "terminal - kubectl (kind cluster, captured output)",
           OUT / "k8s_pods_services.png")
    render(tail_lines("k8s_smoke.txt"), "terminal - smoke test via port-forward (captured output)",
           OUT / "k8s_smoke_test.png")


if __name__ == "__main__":
    main()
