from flauschi_pipeline.utils import slugify


def test_umlauts_lower_case() -> None:
    assert slugify("Fußball, schöne Grüße!") == "fussball-schoene-gruesse"


def test_umlauts_upper_case() -> None:
    assert (
        slugify("Übung für Ärzte in Ölzwiebeln") == "uebung-fuer-aerzte-in-oelzwiebeln"
    )


def test_umlauts_keep_case() -> None:
    assert slugify("Übungs-Ärzte Ö.K.", lower=False) == "Uebungs-Aerzte-Oe-K"


def test_capital_sharp_s() -> None:
    assert slugify("STRAẞE", lower=False) == "STRASSE"


def test_accents_are_stripped() -> None:
    assert slugify("Café René") == "cafe-rene"


def test_non_ascii_digits_are_replaced() -> None:
    assert slugify("Folge ٣ für alle") == "folge-fuer-alle"


def test_no_leading_or_trailing_underscores() -> None:
    assert slugify("!Fußball!") == "fussball"


def test_degenerate_input() -> None:
    assert slugify("!!!") == ""
    assert slugify("") == ""


def test_lower_false_keeps_upper_case() -> None:
    assert slugify("Hallo Welt", lower=False) == "Hallo-Welt"


def test_max_length_truncates() -> None:
    assert slugify("Änderungsantrag", max_length=8) == "aenderun"


def test_max_length_strips_trailing_underscore() -> None:
    assert slugify("Änd-rung", max_length=5) == "aend"


def test_max_length_none_keeps_full_text() -> None:
    long_title = "abcd" * 100
    assert len(slugify(long_title)) == 400
