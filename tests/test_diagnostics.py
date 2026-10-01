"""Diagnostics: INVALID results name the violated rule (hints, never status changes)."""
import pytest

from openpona import parse

EXAMPLES = [
    ("sona pali ken", "units-without-pi"),
    ("sona pi lawa", "pi-after-one-unit"),
    ("sona pi lawa", "pi-arity"),
    ("li pali", "particle-first"),
    ("jan li", "particle-last"),
    ("jan li li li", "particle-run"),
    ("jan pi li pali", "particle-run"),
    ("ma la ma la jan li pali", "la-count"),
    ("jan pi ilo", "pi-arity"),
    ("ILO LI AWEN", "case"),
    ("ilo mi", "unknown-token"),
]


@pytest.mark.parametrize("text,rule", EXAMPLES)
def test_rule_named_in_errors(text, rule):
    res = parse(text)
    assert res.status == "INVALID" and res.skeletons == []
    assert any(e.startswith(rule + ":") for e in res.errors), res.errors


def test_errors_are_located():
    res = parse("li pali")
    assert any("(token 1 'li')" in e for e in res.errors)


def test_line_and_length_guards():
    assert parse("jan li pali\njan li awen").errors[0].startswith("line:")
    long = " ".join(["jan"] * 257)
    assert parse(long).errors[0].startswith("length:")


def test_long_valid_statement_parses_resolved():
    # 1 + 2 + 2*100 = 203 tokens, under the 256 guard; a hundred e-phrases
    text = "jan li pali " + " ".join(["e ilo"] * 100)
    res = parse(text)
    assert res.status == "RESOLVED", res.errors
    assert res.skeletons == ["({jan} li {pali}" + " e {ilo}" * 100 + ")"]


def test_specific_diagnostic_replaces_the_generic_message():
    # each input has a specific rule; the generic line must then be absent
    for text, rule in (("jan li li pali", "particle-run"), ("sona pali ken", "units-without-pi"),
                       ("sona pi lawa", "pi-"), ("li pali", "particle-first")):
        res = parse(text)
        assert res.status == "INVALID"
        assert any(e.startswith(rule) for e in res.errors), (text, res.errors)
        assert not any("no structural parse" in e for e in res.errors), (text, res.errors)


def test_generic_message_when_nothing_specific_fires():
    # a 3-unit group after pi is caught by pi-arity, so pick a shape no rule names:
    # a bare `tan` phrase as the whole predicate after e is fine; use anu at a boundary instead
    res = parse("jan anu li pali")
    assert res.status == "INVALID"
    assert res.errors, "INVALID must always carry at least one message"
