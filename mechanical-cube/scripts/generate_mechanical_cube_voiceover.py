"""Generate and mix a timed Mandarin narration for the mechanical CUBE film."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "mechanical_cube_voiceover.json"
TOOLS = ROOT / ".audio-tools"
OUT = ROOT / "output" / "robot-arm" / "cube-ai-control-loop"
PARTS = OUT / "voiceover_parts"
VOICE_TRACK = OUT / "mechanical_cube_voiceover.wav"
SOURCE_VIDEO = OUT / "mechanical_cube_intro_plus_ai_loop_smooth.mp4"
OUTPUT_VIDEO = OUT / "mechanical_cube_intro_plus_ai_loop_smooth_voiced.mp4"
REPORT = OUT / "mechanical_cube_voiceover_report.json"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def atempo(speed: float) -> str:
    factors: list[float] = []
    while speed > 2.0:
        factors.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        factors.append(0.5)
        speed /= 0.5
    factors.append(speed)
    return ",".join(f"atempo={value:.6f}" for value in factors)


def synthesize(text: str, target: Path, config: dict[str, object]) -> None:
    env = os.environ.copy()
    if TOOLS.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(TOOLS) + (os.pathsep + existing if existing else "")
    base = [
        sys.executable, "-m", "edge_tts",
        "--voice", str(config["voice"]),
        "--rate", str(config["rate"]),
        "--volume", str(config["volume"]),
        f"--pitch={config['pitch']}",
        "--text", text,
        "--write-media", str(target),
        "--no-progress",
    ]
    try:
        subprocess.run(base, cwd=ROOT, env=env, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(
            [*base, "--proxy", "http://127.0.0.1:7897"],
            cwd=ROOT,
            env=env,
            check=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--source-video", type=Path, default=SOURCE_VIDEO)
    parser.add_argument("--output-video", type=Path, default=OUTPUT_VIDEO)
    parser.add_argument("--voice-track", type=Path, default=VOICE_TRACK)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--parts", type=Path, default=PARTS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    source_video = args.source_video.resolve()
    output_video = args.output_video.resolve()
    voice_track = args.voice_track.resolve()
    report_path = args.report.resolve()
    parts_path = args.parts.resolve()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    total = float(config["total_duration"])
    parts_path.mkdir(parents=True, exist_ok=True)
    voice_track.parent.mkdir(parents=True, exist_ok=True)
    output_video.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    previous: dict[str, str] = {}
    if report_path.exists():
        try:
            old = json.loads(report_path.read_text(encoding="utf-8"))
            previous = {item["id"]: item["text"] for item in old["segments"]}
        except (json.JSONDecodeError, KeyError, TypeError):
            previous = {}

    rendered: list[dict[str, object]] = []
    for segment in config["segments"]:
        segment_id = segment["id"]
        raw = parts_path / f"{segment_id}_raw.mp3"
        fitted = parts_path / f"{segment_id}.wav"
        if not raw.exists() or previous.get(segment_id) != segment["text"]:
            print(f"Synthesize {segment_id}: {segment['text']}", flush=True)
            synthesize(segment["text"], raw, config)

        raw_duration = duration(raw)
        max_duration = float(segment["max_duration"])
        speed = max(1.0, raw_duration / max_duration)
        final_duration = raw_duration / speed
        fade_start = max(0.0, final_duration - 0.10)
        run([
            "ffmpeg", "-y", "-i", str(raw),
            "-af",
            ",".join([
                atempo(speed),
                "highpass=f=75",
                "lowpass=f=11500",
                "acompressor=threshold=0.16:ratio=2.2:attack=18:release=120:makeup=1.7",
                "afade=t=in:st=0:d=0.035",
                f"afade=t=out:st={fade_start:.3f}:d=0.10",
                "aresample=48000",
            ]),
            "-ac", "1", "-c:a", "pcm_s16le", str(fitted),
        ])
        rendered.append({
            **segment,
            "path": str(fitted),
            "raw_duration": raw_duration,
            "speed": speed,
            "final_duration": duration(fitted),
        })

    inputs: list[str] = []
    filters: list[str] = []
    labels: list[str] = []
    for index, segment in enumerate(rendered):
        inputs.extend(["-i", str(segment["path"])])
        label = f"n{index}"
        delay_ms = round(float(segment["start"]) * 1000)
        filters.append(f"[{index}:a]adelay={delay_ms}:all=1[{label}]")
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
        + "loudnorm=I=-16:LRA=6:TP=-1.5,aresample=48000,"
        + f"apad=whole_dur={total},atrim=end={total},"
        + "aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=stereo[out]"
    )
    run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[out]", "-c:a", "pcm_s16le", str(voice_track),
    ])
    run([
        "ffmpeg", "-y", "-i", str(source_video), "-i", str(voice_track),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-af", f"apad=whole_dur={total},atrim=end={total}",
        "-movflags", "+faststart", "-t", str(total), str(output_video),
    ])

    report = {
        "voice": config["voice"],
        "audio": str(voice_track),
        "video": str(output_video),
        "segments": [
            {
                "id": item["id"],
                "start": item["start"],
                "text": item["text"],
                "raw_duration": round(float(item["raw_duration"]), 3),
                "speed": round(float(item["speed"]), 3),
                "final_duration": round(float(item["final_duration"]), 3),
            }
            for item in rendered
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
