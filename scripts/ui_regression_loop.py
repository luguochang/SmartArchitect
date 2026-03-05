#!/usr/bin/env python3
"""
Playwright CLI based full-path UI regression loop.

Outputs:
- screenshots and logs under output/playwright/regression/<timestamp>/
- structured report json + markdown summary
- optional visual diff artifacts against output/playwright/baseline/
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT_CACHE_DIR = ROOT / ".playwright-cli"
OUTPUT_ROOT = ROOT / "output" / "playwright" / "regression"
BASELINE_ROOT = ROOT / "output" / "playwright" / "baseline"

RESULT_RE = re.compile(r"### Result\s*(.*?)\s*### Ran Playwright code", re.S)
ERROR_RE = re.compile(r"### Error\s*(.*?)(?:\n### |\Z)", re.S)
ARTIFACT_RE = re.compile(r"\((\.playwright-cli[\\/][^)]+)\)")
NETWORK_LINE_RE = re.compile(r"\[(?P<method>[A-Z]+)\]\s+(?P<url>\S+)\s+=>\s+\[(?P<status>\d+)\]\s*(?P<reason>.*)")


@dataclass
class CliResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


class PlaywrightCliSession:
    def __init__(self, session_name: str, timeout_seconds: int = 180) -> None:
        self.session_name = session_name
        self.timeout_seconds = timeout_seconds

    def run(self, args: List[str], check: bool = True, timeout_seconds: Optional[int] = None) -> CliResult:
        cmd = [
            "npx.cmd",
            "-y",
            "@playwright/cli",
            f"-s={self.session_name}",
            *args,
        ]
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds or self.timeout_seconds,
        )
        result = CliResult(
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        return result

    def close(self) -> None:
        try:
            self.run(["close"], check=False, timeout_seconds=20)
        except Exception:
            pass


def parse_eval_result(stdout: str) -> Any:
    error_match = ERROR_RE.search(stdout)
    if error_match:
        return {"__error__": error_match.group(1).strip()}
    match = RESULT_RE.search(stdout)
    if not match:
        return None
    payload = match.group(1).strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def normalize_eval_source(func_src: str) -> str:
    return " ".join(line.strip() for line in func_src.strip().splitlines() if line.strip())


def find_artifact_path(stdout: str) -> Optional[Path]:
    match = ARTIFACT_RE.search(stdout)
    if not match:
        return None
    relative = match.group(1).replace("\\", "/")
    return ROOT / relative


def copy_artifact(stdout: str, destination: Path) -> Optional[Path]:
    src = find_artifact_path(stdout)
    if not src or not src.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, destination)
    return destination


def js_click(selector: str) -> str:
    selector_json = json.dumps(selector)
    return (
        "() => {"
        f" const selector = {selector_json};"
        " const el = document.querySelector(selector);"
        " if (!el) return { ok: false, selector, reason: 'missing' };"
        " el.scrollIntoView({ block: 'center', inline: 'center' });"
        " el.click();"
        " return { ok: true, selector };"
        " }"
    )


def js_fill(selector: str, value: str) -> str:
    selector_json = json.dumps(selector)
    value_json = json.dumps(value)
    return (
        "() => {"
        f" const selector = {selector_json};"
        f" const value = {value_json};"
        " const el = document.querySelector(selector);"
        " if (!el) return { ok: false, selector, reason: 'missing' };"
        " el.scrollIntoView({ block: 'center', inline: 'center' });"
        " el.focus();"
        " el.value = value;"
        " el.dispatchEvent(new Event('input', { bubbles: true }));"
        " el.dispatchEvent(new Event('change', { bubbles: true }));"
        " return { ok: true, selector, valueLength: value.length };"
        " }"
    )


FLOW_METRICS_JS = (
    "() => { const button = document.querySelector(\"[data-testid='btn-generate-flow']\"); "
    "const buttonText = button ? String(button.textContent || '') : ''; "
    "const panel = document.querySelector(\"[data-testid='panel-messages']\"); "
    "const panelText = panel ? String(panel.innerText || '') : ''; "
    "return { "
    "nodes: document.querySelectorAll('.react-flow__node').length, "
    "edges: document.querySelectorAll('.react-flow__edge').length, "
    "generating: buttonText.toLowerCase().includes('generating'), "
    "buttonDisabled: !!(button && button.disabled), "
    "buttonText: buttonText.trim(), "
    "panelTail: panelText.slice(-500) "
    "}; }"
)


EXCALIDRAW_METRICS_JS = (
    "() => { const button = document.querySelector(\"[data-testid='btn-generate-flow']\"); "
    "const buttonText = button ? String(button.textContent || '') : ''; "
    "const panel = document.querySelector(\"[data-testid='panel-messages']\"); "
    "const panelText = panel ? String(panel.innerText || '') : ''; "
    "const store = window.__ARCHITECT_STORE__; "
    "const scene = store && store.getState ? store.getState().excalidrawScene : null; "
    "const sceneElements = scene && Array.isArray(scene.elements) ? scene.elements.length : 0; "
    "const sceneStreaming = !!(scene && scene.appState && scene.appState.__streaming); "
    "const streamMatch = panelText.match(/(\\\\d+) elements drawn/i) || panelText.match(/partial_elements=(\\\\d+)/i); "
    "const finalMatch = panelText.match(/Final elements:\\\\s*(\\\\d+)/i); "
    "return { "
    "canvasCount: document.querySelectorAll('canvas').length, "
    "generating: buttonText.toLowerCase().includes('generating'), "
    "buttonText: buttonText.trim(), "
    "streamedElements: streamMatch ? Number(streamMatch[1]) : 0, "
    "finalElements: finalMatch ? Number(finalMatch[1]) : 0, "
    "sceneElements, "
    "sceneStreaming, "
    "hasResult: panelText.includes('[RESULT]') || panelText.includes('Excalidraw generated successfully'), "
    "panelTail: panelText.slice(-500) "
    "}; }"
)


DOM_SCAN_JS = (
    "() => { const viewport = { width: window.innerWidth, height: window.innerHeight }; "
    "const issues = { overflow: [], tinyInteractive: [], nestedScroll: [] }; "
    "const all = Array.from(document.querySelectorAll('body *')); "
    "for (const el of all.slice(0, 4000)) { "
    "const rect = el.getBoundingClientRect(); "
    "if (!Number.isFinite(rect.width) || !Number.isFinite(rect.height)) continue; "
    "const style = window.getComputedStyle(el); "
    "const tag = (el.tagName || '').toLowerCase(); "
    "const className = (el.className || '').toString(); "
    "const isSvg = el.namespaceURI === 'http://www.w3.org/2000/svg'; "
    "const inDiagramCanvas = !!el.closest('.react-flow, .react-flow__renderer, .react-flow__viewport, [data-testid=\"excalidraw-board\"], .excalidraw'); "
    "const isFloating = style.position === 'absolute' || style.position === 'fixed' || style.position === 'sticky'; "
    "const out = !inDiagramCanvas && !isFloating && rect.width > 20 && rect.height > 10 && (rect.right > viewport.width + 2 || rect.left < -2); "
    "if (out && issues.overflow.length < 35) { issues.overflow.push({ tag, className: (el.className || '').toString().slice(0, 80), text: (el.textContent || '').trim().slice(0, 80), left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width) }); } "
    "const interactive = !isSvg && (['button','a','input','textarea','select'].includes(tag) || el.getAttribute('role') === 'button'); "
    "if (interactive && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && (rect.width < 8 || rect.height < 8) && issues.tinyInteractive.length < 35) { issues.tinyInteractive.push({ tag, className: (el.className || '').toString().slice(0, 80), text: (el.textContent || '').trim().slice(0, 80), width: Math.round(rect.width), height: Math.round(rect.height) }); } "
    "const hasScroll = /(auto|scroll)/.test(String(style.overflow) + ' ' + String(style.overflowY) + ' ' + String(style.overflowX)); "
    "if (hasScroll && el.scrollHeight - el.clientHeight > 60 && issues.nestedScroll.length < 50) { issues.nestedScroll.push({ tag, className: (el.className || '').toString().slice(0, 80), clientHeight: el.clientHeight, scrollHeight: el.scrollHeight }); } "
    "} "
    "return { viewport, counts: { overflow: issues.overflow.length, tinyInteractive: issues.tinyInteractive.length, nestedScroll: issues.nestedScroll.length }, issues }; }"
)


def wait_until(fetch_state: Callable[[], Dict[str, Any]], condition: Callable[[Dict[str, Any]], bool], timeout: float, interval: float = 1.0) -> Tuple[Optional[Dict[str, Any]], float]:
    started = time.perf_counter()
    latest: Optional[Dict[str, Any]] = None
    while (time.perf_counter() - started) < timeout:
        latest = fetch_state()
        if condition(latest):
            return latest, time.perf_counter() - started
        time.sleep(interval)
    return latest, time.perf_counter() - started


def image_diff_metrics(current: Path, baseline: Path, diff_output: Path) -> Dict[str, Any]:
    if not baseline.exists():
        baseline.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current, baseline)
        return {
            "baseline_created": True,
            "changed_percent": 0.0,
            "mean_channel_delta": 0.0,
            "diff_image": None,
        }

    img_a = Image.open(baseline).convert("RGB")
    img_b = Image.open(current).convert("RGB")
    if img_a.size != img_b.size:
        img_a = img_a.resize(img_b.size)

    diff = ImageChops.difference(img_a, img_b)
    stat = ImageStat.Stat(diff)
    mean_delta = sum(stat.mean) / max(len(stat.mean), 1)

    gray = diff.convert("L")
    histogram = gray.histogram()
    total_pixels = img_b.size[0] * img_b.size[1]
    unchanged = histogram[0] if histogram else 0
    changed_pixels = max(total_pixels - unchanged, 0)
    changed_percent = (changed_pixels / total_pixels * 100.0) if total_pixels else 0.0

    if changed_pixels > 0:
        diff_output.parent.mkdir(parents=True, exist_ok=True)
        diff.save(diff_output)
        diff_file = str(diff_output.relative_to(ROOT)).replace("\\", "/")
    else:
        diff_file = None

    return {
        "baseline_created": False,
        "changed_percent": round(changed_percent, 4),
        "mean_channel_delta": round(mean_delta, 4),
        "diff_image": diff_file,
    }


def parse_network_log(log_file: Path) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    if not log_file.exists():
        return {"entries": entries, "total": 0, "failures": 0}

    for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
        match = NETWORK_LINE_RE.search(line)
        if not match:
            continue
        status = int(match.group("status"))
        url = match.group("url")
        entries.append(
            {
                "method": match.group("method"),
                "url": url,
                "status": status,
                "reason": match.group("reason").strip(),
                "is_api": "/api/" in url,
                "is_failure": status >= 400,
            }
        )

    failures = sum(1 for item in entries if item["is_failure"])
    api_entries = [item for item in entries if item["is_api"]]
    return {
        "entries": entries,
        "api_entries": api_entries,
        "total": len(entries),
        "api_total": len(api_entries),
        "failures": failures,
        "api_failures": sum(1 for item in api_entries if item["is_failure"]),
    }


def ensure_ok(result: Any, step: str, issues: List[Dict[str, Any]]) -> None:
    if isinstance(result, dict) and result.get("ok"):
        return
    issues.append({"severity": "high", "module": "automation", "step": step, "detail": result})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Playwright CLI full-path UI regression loop")
    parser.add_argument("--base-url", default="http://127.0.0.1:3000", help="Frontend base URL")
    parser.add_argument("--flow-timeout", type=int, default=180, help="Flow generation timeout seconds")
    parser.add_argument("--excalidraw-timeout", type=int, default=220, help="Excalidraw generation timeout seconds")
    parser.add_argument("--session-prefix", default="smartarch-reg", help="Playwright session prefix")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = OUTPUT_ROOT / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    BASELINE_ROOT.mkdir(parents=True, exist_ok=True)

    session_name = f"{args.session_prefix}-{int(time.time())}"
    cli = PlaywrightCliSession(session_name=session_name)

    issues: List[Dict[str, Any]] = []
    screenshots: Dict[str, str] = {}
    visual_diffs: Dict[str, Any] = {}

    report: Dict[str, Any] = {
        "timestamp": timestamp,
        "base_url": args.base_url,
        "session": session_name,
        "flow": {},
        "excalidraw": {},
        "dom_scans": {},
        "network": {},
        "issues": issues,
        "screenshots": screenshots,
        "visual_diffs": visual_diffs,
    }

    def eval_json(func_src: str) -> Dict[str, Any]:
        normalized_src = normalize_eval_source(func_src)
        res = cli.run(["eval", normalized_src], check=True, timeout_seconds=90)
        parsed = parse_eval_result(res.stdout)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}

    def click(selector: str, step: str) -> None:
        state = eval_json(js_click(selector))
        ensure_ok(state, step, issues)

    def fill(selector: str, value: str, step: str) -> None:
        state = eval_json(js_fill(selector, value))
        ensure_ok(state, step, issues)

    def capture_screenshot(name: str) -> Optional[Path]:
        result = cli.run(["screenshot"], check=True, timeout_seconds=90)
        destination = run_dir / f"{name}.png"
        copied = copy_artifact(result.stdout, destination)
        if copied:
            screenshots[name] = str(copied.relative_to(ROOT)).replace("\\", "/")
        return copied

    def capture_dom_scan(name: str) -> Dict[str, Any]:
        data = eval_json(DOM_SCAN_JS)
        report["dom_scans"][name] = data
        return data

    def capture_network(name: str) -> Dict[str, Any]:
        result = cli.run(["network"], check=True, timeout_seconds=40)
        destination = run_dir / f"network-{name}.log"
        copied = copy_artifact(result.stdout, destination)
        if copied:
            parsed = parse_network_log(copied)
            report["network"][name] = parsed
            return parsed
        parsed = {"entries": [], "total": 0, "failures": 0, "api_total": 0, "api_failures": 0}
        report["network"][name] = parsed
        return parsed

    try:
        cli.run(["open", args.base_url], check=True, timeout_seconds=90)
        cli.run(["resize", "1600", "980"], check=True, timeout_seconds=20)

        ready_state, waited = wait_until(
            fetch_state=lambda: eval_json("() => ({ ready: !!document.querySelector('[data-testid=\"ai-control-panel\"]') })"),
            condition=lambda state: bool(state.get("ready")),
            timeout=35,
            interval=1.0,
        )
        report["page_ready_seconds"] = round(waited, 3)
        if not ready_state or not ready_state.get("ready"):
            issues.append({"severity": "high", "module": "ui", "step": "initial-load", "detail": "AI control panel not found"})

        capture_screenshot("home-initial")
        capture_dom_scan("home-initial")

        # Flow module path
        click("[data-testid='mode-reactflow']", "switch-flow-mode")
        click("[data-testid='btn-toggle-quick-prompts']", "toggle-prompts-collapse")
        capture_screenshot("flow-prompts-collapsed")
        click("[data-testid='btn-toggle-quick-prompts']", "toggle-prompts-expand")
        click("[data-testid='btn-filter-architecture']", "select-architecture-filter")
        click("[data-testid='btn-architecture-technical']", "select-architecture-technical")
        click("[data-testid='quick-prompt-flow-frontend-backend']", "pick-architecture-prompt")
        capture_screenshot("flow-before-generate")

        # Ensure API config loaded (button enabled when not generating)
        flow_btn_state, _ = wait_until(
            fetch_state=lambda: eval_json("() => { const btn = document.querySelector('[data-testid=\"btn-generate-flow\"]'); return { exists: !!btn, disabled: !!btn?.disabled, text: (btn?.textContent || '').trim() }; }"),
            condition=lambda state: bool(state.get("exists")) and not bool(state.get("disabled")),
            timeout=30,
            interval=1.0,
        )
        report["flow"]["button_ready"] = flow_btn_state
        if not flow_btn_state or flow_btn_state.get("disabled"):
            issues.append({"severity": "high", "module": "flow", "step": "pre-generate", "detail": "Generate button disabled (API config not ready?)"})

        flow_start = time.perf_counter()
        click("[data-testid='btn-generate-flow']", "trigger-flow-generate")

        first_node_seconds: Optional[float] = None
        flow_final_state: Dict[str, Any] = {}
        first_flow_shot_taken = False

        while True:
            elapsed = time.perf_counter() - flow_start
            flow_state = eval_json(FLOW_METRICS_JS)
            flow_final_state = flow_state

            if first_node_seconds is None and int(flow_state.get("nodes", 0)) > 0:
                first_node_seconds = elapsed
                if not first_flow_shot_taken:
                    capture_screenshot("flow-first-node")
                    first_flow_shot_taken = True

            done = (not flow_state.get("generating", False)) and int(flow_state.get("nodes", 0)) > 0
            if done:
                break
            if elapsed >= args.flow_timeout:
                issues.append({
                    "severity": "high",
                    "module": "flow",
                    "step": "generation-timeout",
                    "detail": f"Flow generation exceeded {args.flow_timeout}s",
                    "state": flow_state,
                })
                break
            time.sleep(1.0)

        flow_total_seconds = time.perf_counter() - flow_start
        report["flow"].update(
            {
                "first_node_seconds": round(first_node_seconds, 3) if first_node_seconds is not None else None,
                "total_seconds": round(flow_total_seconds, 3),
                "final_state": flow_final_state,
            }
        )
        if first_node_seconds is None:
            issues.append({"severity": "high", "module": "flow", "step": "streaming", "detail": "No nodes appeared during generation"})

        capture_screenshot("flow-final")
        capture_dom_scan("flow-final")

        click("[data-testid='btn-filter-flow']", "switch-filter-back-to-flow")
        click("[data-testid='btn-toggle-style-dock']", "open-style-dock")
        auto_layout_available = eval_json("() => ({ has: !!document.querySelector(\"[data-testid='btn-auto-layout']\") })")
        if auto_layout_available.get("has"):
            click("[data-testid='btn-auto-layout']", "auto-layout")
        else:
            issues.append({
                "severity": "medium",
                "module": "automation",
                "step": "auto-layout",
                "detail": "Auto-layout button not available in current diagram mode",
            })
        capture_screenshot("flow-after-autolayout")

        # Scroll messages panel to cover dynamic scroll path
        eval_json("() => { const panel = document.querySelector('[data-testid=\"panel-messages\"]'); if (!panel) return {ok:false}; panel.scrollTop = panel.scrollHeight; return {ok:true, scrollTop: panel.scrollTop}; }")

        flow_network = capture_network("flow")
        if flow_network.get("api_failures", 0) > 0:
            issues.append({
                "severity": "high",
                "module": "flow",
                "step": "api-network",
                "detail": f"Detected {flow_network.get('api_failures', 0)} API failures in flow path",
            })

        # Excalidraw module path
        click("[data-testid='mode-excalidraw']", "switch-excalidraw-mode")
        ready_excalidraw, wait_excalidraw = wait_until(
            fetch_state=lambda: eval_json("() => ({ ready: !!document.querySelector('[data-testid=\"excalidraw-board\"]') })"),
            condition=lambda state: bool(state.get("ready")),
            timeout=40,
            interval=1.0,
        )
        report["excalidraw"]["board_ready_seconds"] = round(wait_excalidraw, 3)
        if not ready_excalidraw or not ready_excalidraw.get("ready"):
            click("[data-testid='mode-excalidraw']", "switch-excalidraw-mode-retry")
            ready_excalidraw, wait_retry = wait_until(
                fetch_state=lambda: eval_json("() => ({ ready: !!document.querySelector('[data-testid=\"excalidraw-board\"]') })"),
                condition=lambda state: bool(state.get("ready")),
                timeout=25,
                interval=1.0,
            )
            report["excalidraw"]["board_retry_seconds"] = round(wait_retry, 3)
            if not ready_excalidraw or not ready_excalidraw.get("ready"):
                issues.append({"severity": "high", "module": "excalidraw", "step": "board-load", "detail": "Excalidraw board not ready"})

        click("[data-testid='btn-open-excalidraw-upload']", "open-excalidraw-uploader")
        capture_screenshot("excalidraw-uploader-open")
        click("[data-testid='btn-back-to-chat']", "back-to-chat")

        # Make sure quick prompts are expanded
        state = eval_json("() => ({ hasPromptButton: !!document.querySelector('[data-testid=\"quick-prompt-excalidraw-flowchart-boxes\"]') })")
        if not state.get("hasPromptButton"):
            click("[data-testid='btn-toggle-quick-prompts']", "expand-excalidraw-prompts")

        click("[data-testid='quick-prompt-excalidraw-flowchart-boxes']", "pick-excalidraw-prompt")
        capture_screenshot("excalidraw-before-generate")

        exc_start = time.perf_counter()
        click("[data-testid='btn-generate-flow']", "trigger-excalidraw-generate")

        first_stream_seconds: Optional[float] = None
        final_elements_seconds: Optional[float] = None
        exc_final_state: Dict[str, Any] = {}
        first_exc_shot_taken = False

        while True:
            elapsed = time.perf_counter() - exc_start
            exc_state = eval_json(EXCALIDRAW_METRICS_JS)
            exc_final_state = exc_state

            streamed_signal = int(exc_state.get("streamedElements", 0))
            scene_elements = int(exc_state.get("sceneElements", 0))
            scene_streaming = bool(exc_state.get("sceneStreaming"))

            if first_stream_seconds is None and (streamed_signal > 0 or (scene_elements > 0 and scene_streaming)):
                first_stream_seconds = elapsed
                if not first_exc_shot_taken:
                    capture_screenshot("excalidraw-first-stream")
                    first_exc_shot_taken = True

            if final_elements_seconds is None and int(exc_state.get("finalElements", 0)) > 0:
                final_elements_seconds = elapsed

            done = bool(exc_state.get("hasResult")) or (
                (not exc_state.get("generating", False))
                and (int(exc_state.get("finalElements", 0)) > 0 or streamed_signal > 0 or scene_elements > 0)
            )
            if done:
                break
            if elapsed >= args.excalidraw_timeout:
                timeout_severity = "medium" if first_stream_seconds is not None else "high"
                issues.append({
                    "severity": timeout_severity,
                    "module": "excalidraw",
                    "step": "generation-timeout",
                    "detail": f"Excalidraw generation exceeded {args.excalidraw_timeout}s",
                    "state": exc_state,
                })
                break
            time.sleep(1.2)

        exc_total_seconds = time.perf_counter() - exc_start
        report["excalidraw"].update(
            {
                "first_stream_seconds": round(first_stream_seconds, 3) if first_stream_seconds is not None else None,
                "final_elements_seconds": round(final_elements_seconds, 3) if final_elements_seconds is not None else None,
                "total_seconds": round(exc_total_seconds, 3),
                "final_state": exc_final_state,
            }
        )

        if first_stream_seconds is None:
            issues.append({"severity": "high", "module": "excalidraw", "step": "streaming", "detail": "No streamed elements detected"})
        if first_stream_seconds is not None and first_stream_seconds > exc_total_seconds * 0.8:
            issues.append({
                "severity": "high",
                "module": "excalidraw",
                "step": "pseudo-streaming",
                "detail": "First streamed element appeared too late relative to total duration",
                "first_stream_seconds": round(first_stream_seconds, 3),
                "total_seconds": round(exc_total_seconds, 3),
            })

        capture_screenshot("excalidraw-final")
        capture_dom_scan("excalidraw-final")

        exc_network = capture_network("excalidraw")
        if exc_network.get("api_failures", 0) > 0:
            issues.append({
                "severity": "high",
                "module": "excalidraw",
                "step": "api-network",
                "detail": f"Detected {exc_network.get('api_failures', 0)} API failures in excalidraw path",
            })

        # Visual regression pass
        for shot_name, rel_path in screenshots.items():
            current = ROOT / rel_path
            baseline = BASELINE_ROOT / f"{shot_name}.png"
            diff = run_dir / "visual-diff" / f"{shot_name}.png"
            visual_diffs[shot_name] = image_diff_metrics(current=current, baseline=baseline, diff_output=diff)

        # Aggregate DOM warnings
        for scan_name, scan_data in report["dom_scans"].items():
            counts = (scan_data or {}).get("counts", {})
            if int(counts.get("overflow", 0)) > 0:
                issues.append({
                    "severity": "medium",
                    "module": "ui",
                    "step": f"dom-scan-{scan_name}",
                    "detail": f"Detected {counts.get('overflow')} overflow candidates",
                })
            if int(counts.get("tinyInteractive", 0)) > 0:
                issues.append({
                    "severity": "medium",
                    "module": "ui",
                    "step": f"dom-scan-{scan_name}",
                    "detail": f"Detected {counts.get('tinyInteractive')} tiny interactive elements",
                })

    except Exception as exc:
        issues.append({"severity": "critical", "module": "automation", "step": "exception", "detail": str(exc)})
    finally:
        cli.close()

    report_json = run_dir / "ui_regression_report.json"
    report_md = run_dir / "ui_regression_report.md"

    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    high_count = sum(1 for item in issues if item.get("severity") in {"critical", "high"})
    medium_count = sum(1 for item in issues if item.get("severity") == "medium")

    md_lines = [
        "# UI Regression Report",
        "",
        f"- Timestamp: `{timestamp}`",
        f"- Base URL: `{report['base_url']}`",
        f"- Session: `{report['session']}`",
        f"- High/Critical issues: `{high_count}`",
        f"- Medium issues: `{medium_count}`",
        "",
        "## Flow",
        f"- First node latency: `{report.get('flow', {}).get('first_node_seconds')}` s",
        f"- Total duration: `{report.get('flow', {}).get('total_seconds')}` s",
        "",
        "## Excalidraw",
        f"- First streamed element latency: `{report.get('excalidraw', {}).get('first_stream_seconds')}` s",
        f"- Final elements latency: `{report.get('excalidraw', {}).get('final_elements_seconds')}` s",
        f"- Total duration: `{report.get('excalidraw', {}).get('total_seconds')}` s",
        "",
        "## API Network",
        f"- Flow API failures: `{report.get('network', {}).get('flow', {}).get('api_failures', 0)}`",
        f"- Excalidraw API failures: `{report.get('network', {}).get('excalidraw', {}).get('api_failures', 0)}`",
        "",
        "## Issues",
    ]

    if not issues:
        md_lines.append("- None")
    else:
        for item in issues:
            md_lines.append(
                f"- [{item.get('severity', 'unknown')}] {item.get('module', 'n/a')}::{item.get('step', 'n/a')} - {item.get('detail')}"
            )

    md_lines.extend(
        [
            "",
            "## Artifacts",
            f"- JSON: `{report_json.relative_to(ROOT).as_posix()}`",
            f"- Screenshots: `{run_dir.relative_to(ROOT).as_posix()}`",
        ]
    )

    report_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[ui-regression] report: {report_json.relative_to(ROOT).as_posix()}")
    print(f"[ui-regression] markdown: {report_md.relative_to(ROOT).as_posix()}")
    print(f"[ui-regression] high_critical={high_count} medium={medium_count}")

    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
