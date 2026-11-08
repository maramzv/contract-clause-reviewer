"""Checklist categories. Names are Maya's labels; `cuad` is the CUAD label, spelled as in CUADv1.json
(checked against the data files on November 4, 2026). Match case-insensitively anyway."""
import re

CATEGORIES = {
    "Assignment": {
        "cuad": "Anti-Assignment",
        "description": "Restrictions on assigning the agreement or requiring consent to assign.",
        "counts": "a sentence that prohibits or restricts assigning the agreement, or requires consent or notice before it is assigned (a restriction on only one party still counts).",
        "not_counts": "a heading; a sentence that only says the agreement binds or benefits successors and assigns; a sentence that only lets a party assign freely, with no consent, notice or condition; a sentence about what happens after a transfer was already approved or refused.",
        "patterns": [r"\bassign(?:ed|ment|s)?\b[^.]{0,200}\bconsent\b", r"\bmay not (?:be )?assign"],
    },
    "Change of Control": {
        "cuad": "Change Of Control",
        "description": "Rights or consent triggered by a merger, acquisition or change in ownership.",
        "counts": "a sentence that gives a party a termination right, or requires consent or notice, when a party undergoes a change of control (merger, stock sale, sale of all or substantially all assets or business, or assignment by operation of law).",
        "not_counts": "a heading; a definition of \"change of control\" on its own; a sentence that mentions a merger, acquisition or ownership change without attaching a termination right, consent or notice to it.",
        "patterns": [r"change (?:of|in) control", r"\bmerger\b|\bacquisition\b"],
    },
    "Termination for Convenience": {
        "cuad": "Termination For Convenience",
        "description": "A party may terminate without cause on notice.",
        "counts": "a sentence that lets a party end the agreement without cause by giving notice, including a right that can be used only after a minimum term or the initial term.",
        "not_counts": "a heading; termination for breach, insolvency or force majeure.",
        "patterns": [r"terminate[^.]{0,120}\bfor convenience\b", r"terminate[^.]{0,120}without cause"],
    },
    "Renewal": {
        "cuad": "Renewal Term",
        "description": "The renewal or extension term after the initial term expires, including automatic extensions.",
        "counts": "a sentence that states the renewal or extension term after the initial term, including automatic extensions and extensions a party can choose by giving notice.",
        "not_counts": "a heading; a definition of \"Term\" that merely names the renewal term; a sentence about prices or other terms that apply during a renewal; a sentence that says the parties may renew only if they later agree in writing; notice periods for stopping a renewal.",
        "patterns": [r"\brenew(?:al|ed|s)?\b", r"successive[^.]{0,60}term"],
    },
    "Governing Law": {
        "cuad": "Governing Law",
        "description": "Which jurisdiction's law governs the agreement.",
        "counts": "the sentence that names the jurisdiction whose law governs the agreement (a sentence that also names the court counts).",
        "not_counts": "a heading; a venue or forum clause on its own.",
        "patterns": [r"governed by[^.]{0,120}laws?", r"governing law"],
    },
}

COMPILED = {k: [re.compile(p, re.I) for p in v["patterns"]] for k, v in CATEGORIES.items()}
