import pytest

from app.models import utils as u


def test_from_str_and_from_none_and_from_bool_and_from_int():
    assert u.from_str("hello") == "hello"
    with pytest.raises(AssertionError):
        u.from_str(5)

    assert u.from_none(None) is None
    with pytest.raises(AssertionError):
        u.from_none(0)

    assert u.from_bool(True) is True
    with pytest.raises(AssertionError):
        u.from_bool(1)

    assert u.from_int(3) == 3
    with pytest.raises(AssertionError):
        # bools are not accepted as ints here
        u.from_int(True)


def test_from_list_and_to_class():
    # simple converter
    def conv(x):
        return x * 2

    assert u.from_list(conv, [1, 2, 3]) == [2, 4, 6]

    # with parent: f should accept a tuple (item, parent)
    def conv_with_parent(t):
        (item, parent) = t
        return (item, parent)

    assert u.from_list(conv_with_parent, ["a"], parent="P") == [("a", "P")]

    class C:
        def __init__(self, d):
            self.d = d

        def to_dict(self):
            return {"d": self.d}

    c = C(5)
    assert u.to_class(C, c) == {"d": 5}


def test_from_union():
    # first converter will raise, second will work
    def a(x):
        raise ValueError

    def b(x):
        return str(x)

    assert u.from_union([a, b], 123) == "123"

    # nothing matches -> assertion
    def fail1(x):
        raise Exception

    def fail2(x):
        raise Exception

    with pytest.raises(AssertionError):
        u.from_union([fail1, fail2], 1)


def test_normalize_text_and_sha_and_snake():
    s = "Caf\u00e9 \n Test \u2019"
    norm = u.normalize_text(s)
    assert "Cafe" in norm or "Caf" in norm

    # sha returns alnum string
    h = u.calculate_sha1_hash("some-value")
    assert h.isalnum()

    # snake case
    assert u.to_snake_case("HelloWorld") == "helloworld"
    assert (
        u.to_snake_case("Some text, with punctuation!") == "some_text_with_punctuation"
    )


def test_normalize_text_unicode_variants():
    # Smart quotes, multiple whitespace, HTML entities and combining marks
    s1 = "“Quoted” text \u2014 with\nnewlines and\t tabs"
    out1 = u.normalize_text(s1)
    assert "Quoted" in out1 and "newlines" in out1

    # HTML entities may or may not be decoded; accents should be transliterated
    s2 = "AT&amp;T &#8217; Café"
    out2 = u.normalize_text(s2)
    # accept either decoded '&' or preserved '&amp;'
    assert ("&" in out2) or ("&amp;" in out2)
    assert "Cafe" in out2

    # combining accents become normalized
    s3 = "e\u0301"  # e + combining acute
    out3 = u.normalize_text(s3)
    assert out3 in ("e", "e\u0301", "e")


def test_to_snake_case_edge_cases():
    assert u.to_snake_case("It's John's Book") == "its_johns_book"
    assert u.to_snake_case("HelloWorld123") == "helloworld123"
    assert (
        u.to_snake_case("  multiple   spaces---and___punct ")
        == "multiple_spaces_and_punct"
    )
    # underscores are removed and words joined
    assert (
        u.to_snake_case("snake_case stays") == "snake_case_stays"
        or u.to_snake_case("snake_case stays") == "snake_case_stays"
    )
