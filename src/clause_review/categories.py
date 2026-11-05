"""Checklist categories. Names are Maya's labels; `cuad` is the CUAD label, spelled as in CUADv1.json
(checked against the data files on November 4, 2026). Match case-insensitively anyway."""
import re

CATEGORIES = {
    "Assignment": {
        "cuad": "Anti-Assignment",
        "description": "Restrictions on assigning the agreement or requiring consent to assign.",
        "patterns": [r"\bassign(?:ed|ment|s)?\b[^.]{0,200}\bconsent\b", r"\bmay not (?:be )?assign"],
    },
    "Change of Control": {
        "cuad": "Change Of Control",
        "description": "Rights or consent triggered by a merger, acquisition or change in ownership.",
        "patterns": [r"change (?:of|in) control", r"\bmerger\b|\bacquisition\b"],
    },
    "Termination for Convenience": {
        "cuad": "Termination For Convenience",
        "description": "A party may terminate without cause on notice.",
        "patterns": [r"terminate[^.]{0,120}\bfor convenience\b", r"terminate[^.]{0,120}without cause"],
    },
    "Renewal": {
        "cuad": "Renewal Term",
        "description": "The renewal or extension term after the initial term expires, including automatic extensions.",
        "patterns": [r"\brenew(?:al|ed|s)?\b", r"successive[^.]{0,60}term"],
    },
    "Governing Law": {
        "cuad": "Governing Law",
        "description": "Which jurisdiction's law governs the agreement.",
        "patterns": [r"governed by[^.]{0,120}laws?", r"governing law"],
    },
}

COMPILED = {k: [re.compile(p, re.I) for p in v["patterns"]] for k, v in CATEGORIES.items()}
