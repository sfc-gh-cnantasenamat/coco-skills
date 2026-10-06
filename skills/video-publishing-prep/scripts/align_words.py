"""Force-align a local transcript; keep uncertain or missing timings explicit."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import wave

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["PYANNOTE_METRICS_ENABLED"] = "0"
os.environ["OTEL_SDK_DISABLED"] = "true"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--output", default="word-alignment")
    args = parser.parse_args()
    root = args.directory.resolve()
    output = root / args.output
    output.mkdir(exist_ok=False)
    source = json.loads((args.transcript or root / "transcript.json").read_text())

    import numpy as np
    import torch
    from whisperx.alignment import align, load_align_model

    torch.set_num_threads(4)
    with wave.open(str(root / "audio.wav"), "rb") as audio:
        assert audio.getframerate() == 16000 and audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        pcm = audio.readframes(audio.getnframes())
    waveform = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
    duration = len(waveform) / 16000
    model_name = "WAV2VEC2_ASR_BASE_960H"
    model, metadata = load_align_model("en", "cpu", model_name=model_name)
    words = []
    for segment in source["segments"]:
        # ASR segment boundaries are coarse: provide audio on both sides.
        window = {"start": max(0, segment["start"] - 0.5),
                  "end": min(duration, segment["end"] + 1.5), "text": segment["text"]}
        raw_path = output / f"segment-{segment['id']:03}.json"
        result = align([window], model, metadata, waveform, "cpu",
                       interpolate_method="ignore", return_char_alignments=True)
        raw_path.write_text(json.dumps(result, indent=2, allow_nan=False))
        expected = segment["text"].split()
        aligned = result["word_segments"]
        if [entry["word"] for entry in aligned] != expected:
            raise ValueError(f"Word coverage mismatch in segment {segment['id']}; inspect {raw_path}")
        for entry in aligned:
            start, end, score = entry.get("start"), entry.get("end"), entry.get("score")
            flags = []
            if start is None or end is None or score is None:
                start_ms = end_ms = None
                flags.append("unaligned")
            else:
                if not all(math.isfinite(value) for value in (start, end, score)):
                    raise ValueError("Nonfinite alignment result")
                start_ms, end_ms = round(start * 1000), round(end * 1000)
                if not 0 <= start_ms < end_ms <= round(duration * 1000):
                    flags.append("invalid_interval")
                if score < 0.5:
                    flags.append("low_alignment_score")
                if end_ms - start_ms > 1500:
                    flags.append("long_word_interval")
            words.append({"word_id": len(words), "segment_id": segment["id"],
                          "word": entry["word"], "start_ms": start_ms, "end_ms": end_ms,
                          "start_seconds": None if start_ms is None else start_ms / 1000,
                          "end_seconds": None if end_ms is None else end_ms / 1000,
                          "alignment_score": score, "flags": flags})
        print(f"Aligned segment {segment['id']+1}/{len(source['segments'])}", flush=True)
    for previous, current in zip(words, words[1:]):
        if previous["end_ms"] is not None and current["start_ms"] is not None:
            if current["start_ms"] < previous["end_ms"]:
                current["flags"].append("overlap_previous_word")
                previous["flags"].append("overlap_next_word")
    payload = {
        "source": "whisperx-forced-alignment", "model": model_name, "granularity": "word",
        "whisperx_version": importlib.metadata.version("whisperx"),
        "duration_seconds": duration, "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "timing_units": "integer milliseconds; seconds are exact ms/1000",
        "accuracy_note": "Acoustic alignment estimates, not millisecond-accurate ground truth. Scores are not calibrated accuracy probabilities.",
        "transcript_note": "Aligns every supplied transcript word, including any ASR errors. No missing times are interpolated.",
        "word_count": len(words), "flagged_word_count": sum(bool(word["flags"]) for word in words),
        "words": words,
    }
    (output / "words.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    with (output / "words.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(words[0]))
        writer.writeheader()
        writer.writerows({**word, "flags": ";".join(word["flags"])} for word in words)
    print(f"Saved {len(words)} words; {payload['flagged_word_count']} flagged for review.")


if __name__ == "__main__":
    main()