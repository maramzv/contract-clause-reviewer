"""Sample contracts bundled with the app for demos, with an estimate of how long a review of each will take.

The estimate counts the chunks a contract is cut into (one model call each) and multiplies by a typical time per call
for the chosen provider. The per-call times are rough: see SECONDS_PER_CALL."""
import functools
import os
from pathlib import Path

from .chunk import chunk

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

# (file under samples/, short id, title). The ten contracts are public SEC filings; see docs/03-tests/contract-sources.md.
SAMPLES = [
    ("sample_contract.txt", "sample", "Sample master services agreement (short)"),
    ("contracts/contract_01.txt", "contract_01", "Endorsement Licensing and Co-Branding Agreement (MusclePharm)"),
    ("contracts/contract_02.txt", "contract_02", "Cooperation Agreement (HPIL Energytech and Ginares)"),
    ("contracts/contract_03.txt", "contract_03", "Consulting Agreement (Emerald Health Naturals)"),
    ("contracts/contract_04.txt", "contract_04", "Master Franchise Agreement (Kiosk Concepts)"),
    ("contracts/contract_05.txt", "contract_05", "Strategic Alliance Agreement (SHBV and Waste2Energy)"),
    ("contracts/contract_06.txt", "contract_06", "Non-Competition and Right of First Offer (Glamis Gold and Western Copper)"),
    ("contracts/contract_07.txt", "contract_07", "Joint Filing Agreement (OneMain Holdings)"),
    ("contracts/contract_08.txt", "contract_08", "Cooperation Agreement, 50MWp Solar Project (Fenyi County)"),
    ("contracts/contract_09.txt", "contract_09", "Content License Agreement (Xinhua)"),
    ("contracts/contract_10.txt", "contract_10", "Outsource Technology Development Agreement (DSS and HotApp)"),
]

# Seconds for one model call (one chunk). anthropic: measured on the Nov 8 test run, 2,096 calls in 14 min 40 s with
# 4 workers = about 1.7 s per call per worker. claude_code: two quick tests took 4 and 8 s, so 6 is a guess. mock: no model.
# local: unknown, so no estimate is shown.
SECONDS_PER_CALL = {"mock": 0.0, "anthropic": 1.7, "claude_code": 6.0}


@functools.lru_cache(maxsize=None)
def list_samples():
    """The sample files that exist, each as {path, id, title, label, chars, chunks}."""
    out = []
    for rel, sid, title in SAMPLES:
        path = SAMPLES_DIR / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        out.append({"path": str(path), "id": sid, "title": title, "label": f"{sid} - {title}",
                    "chars": len(text), "chunks": len(chunk(text))})
    return out


def estimate_seconds(chunks, provider, workers=1):
    """Rough seconds to review `chunks` chunks, or None if there is no basis for an estimate."""
    per_call = SECONDS_PER_CALL.get(provider)
    if per_call is None:
        return None
    return chunks * per_call / max(1, workers)


def format_duration(seconds):
    if seconds is None:
        return "time unknown"
    if seconds < 10:
        return "instant" if seconds < 1 else "under 10 sec"
    if seconds < 90:
        return f"about {round(seconds / 5) * 5} sec"
    minutes = seconds / 60
    return f"about {round(minutes)} min" if minutes < 60 else f"about {minutes / 60:.1f} hr"


def workers_from_env():
    try:
        return max(1, int(os.environ.get("CLAUSE_WORKERS", "1")))
    except ValueError:
        return 1
