"""The theme: its CSS must format without error (a stray % once crashed the whole page), and the header/KPI pieces escape text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # theme.py sits next to app.py

import theme


class FakeSt:
    def __init__(self):
        self.out = []

    def markdown(self, text, **kw):
        self.out.append(text)

    def html(self, text, **kw):
        self.out.append(text)


def test_the_css_formats_and_keeps_its_percentages():
    st = FakeSt()
    theme.apply_theme(st)
    css = st.out[0]
    assert "<style>" in css and "max-width:100%;" in css and "%(" not in css
    assert "--ink:#142737" in css and "clautra-slide" in css


def test_kpi_tile_is_highlighted_only_when_there_is_something_to_check():
    st = FakeSt()
    theme.kpi_row(st, [(3, "Contracts", None, False), (5, "To check", "for you", True)])
    html = st.out[0]
    assert html.count('class="kpi"') == 1 and html.count('class="kpi flag"') == 1 and ">5<" in html


def test_text_in_headings_and_chips_is_escaped():
    assert "&lt;b&gt;" in theme.category_heading("<b>x</b>", "Found")
    st = FakeSt()
    theme.kpi_row(st, [(1, "<script>", "<i>", False)])
    assert "<script>" not in st.out[0] and "&lt;script&gt;" in st.out[0]


def test_offline_tag_appears_in_the_header_only_when_asked():
    on, off = FakeSt(), FakeSt()
    theme.hero(on, offline=True)
    theme.hero(off)
    assert "Offline mode" in on.out[0] and "Offline mode" not in off.out[0]


def test_marquee_is_switched_off_so_no_script_is_sent():
    calls = []

    class St:
        def html(self, text, **kw):
            calls.append((text, kw))
    theme.marquee(St())
    assert calls == []  # long names no longer slide on hover
