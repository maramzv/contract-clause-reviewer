"""The extractor prompt carries the signed definitions: what counts and what does not, per category."""
from clause_review.categories import CATEGORIES
from clause_review.chunk import Chunk
from clause_review.extract import PROMPT, describe, llm_candidates
from clause_review.providers import Provider


class Spy(Provider):
    name = "spy"

    def __init__(self):
        super().__init__()
        self.prompts = []

    def _complete(self, prompt):
        self.prompts.append(prompt)
        return "[]", 1, 1


def test_every_category_has_counts_and_not_counts_lines():
    for name, c in CATEGORIES.items():
        assert c["counts"].strip() and c["not_counts"].strip(), name
        assert "{" not in c["counts"] + c["not_counts"] + c["description"], f"{name}: braces would break the prompt template"


def test_the_prompt_lists_each_category_with_its_lines_and_the_general_rules():
    spy = Spy()
    list(llm_candidates(Chunk(0, "Some contract text."), list(CATEGORIES), spy))
    prompt = spy.prompts[0]
    for name in CATEGORIES:
        assert describe(name) in prompt
    assert "Some contract text." in prompt and "<<<CONTRACT>>>" in prompt
    assert "Quote EXACTLY" in prompt and "Do not quote a heading" in prompt
    assert '[{"category": "<name>", "quote": "<exact text>"}]' in prompt  # the JSON shape the parser expects


def test_only_the_chosen_categories_appear():
    spy = Spy()
    list(llm_candidates(Chunk(0, "x"), ["Renewal"], spy))
    assert "- Renewal:" in spy.prompts[0] and "- Assignment:" not in spy.prompts[0]


def test_the_signed_exclusions_are_in_the_prompt():
    # Wording agreed in the Clause Definitions document (approved November 5, 2026).
    assert "successors and assigns" in CATEGORIES["Assignment"]["not_counts"]
    assert "without attaching a termination right, consent or notice" in CATEGORIES["Change of Control"]["not_counts"]
    assert "minimum term" in CATEGORIES["Termination for Convenience"]["counts"]
    assert "notice periods for stopping a renewal" in CATEGORIES["Renewal"]["not_counts"]
    assert "venue or forum clause on its own" in CATEGORIES["Governing Law"]["not_counts"]
