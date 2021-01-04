# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
from io import StringIO
import os
import pytest
from urllib.parse import urlencode
from urllib.request import urlopen

import mwparserfromhell

class TestDocs:
    """Integration test cases for mwparserfromhell's documentation."""

    def assertPrint(self, value, output):
        """Assertion check that *value*, when printed, produces *output*."""
        buff = StringIO()
        print(value, end="", file=buff)
        buff.seek(0)
        assert output == buff.read()

    def test_readme_1(self):
        """test a block of example code in the README"""
        text = "I has a template! {{foo|bar|baz|eggs=spam}} See it?"
        wikicode = mwparserfromhell.parse(text)
        self.assertPrint(wikicode,
                         "I has a template! {{foo|bar|baz|eggs=spam}} See it?")
        templates = wikicode.filter_templates()
        self.assertPrint(templates, "['{{foo|bar|baz|eggs=spam}}']")
        template = templates[0]
        self.assertPrint(template.name, "foo")
        self.assertPrint(template.params, "['bar', 'baz', 'eggs=spam']")
        self.assertPrint(template.get(1).value, "bar")
        self.assertPrint(template.get("eggs").value, "spam")

    def test_readme_2(self):
        """test a block of example code in the README"""
        text = "{{foo|{{bar}}={{baz|{{spam}}}}}}"
        temps = mwparserfromhell.parse(text).filter_templates()
        res = "['{{foo|{{bar}}={{baz|{{spam}}}}}}', '{{bar}}', '{{baz|{{spam}}}}', '{{spam}}']"
        self.assertPrint(temps, res)

    def test_readme_3(self):
        """test a block of example code in the README"""
        code = mwparserfromhell.parse("{{foo|this {{includes a|template}}}}")
        self.assertPrint(code.filter_templates(recursive=False),
                         "['{{foo|this {{includes a|template}}}}']")
        foo = code.filter_templates(recursive=False)[0]
        self.assertPrint(foo.get(1).value, "this {{includes a|template}}")
        self.assertPrint(foo.get(1).value.filter_templates()[0],
                         "{{includes a|template}}")
        self.assertPrint(foo.get(1).value.filter_templates()[0].get(1).value,
                         "template")

    def test_readme_4(self):
        """test a block of example code in the README"""
        text = "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}"
        code = mwparserfromhell.parse(text)
        for template in code.filter_templates():
            if template.name.matches("Cleanup") and not template.has("date"):
                template.add("date", "July 2012")
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{uncategorized}}"
        self.assertPrint(code, res)
        code.replace("{{uncategorized}}", "{{bar-stub}}")
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}"
        self.assertPrint(code, res)
        res = "['{{cleanup|date=July 2012}}', '{{bar-stub}}']"
        self.assertPrint(code.filter_templates(), res)
        text = str(code)
        res = "{{cleanup|date=July 2012}} '''Foo''' is a [[bar]]. {{bar-stub}}"
        self.assertPrint(text, res)
        assert text == code

    @pytest.mark.skipif("NOWEB" in os.environ, reason="web test disabled by environ var")
    def test_readme_5(self):
        """test a block of example code in the README; includes a web call"""
        url1 = "https://en.wikipedia.org/w/api.php"
        url2 = "https://en.wikipedia.org/w/index.php?title={0}&action=raw"
        title = "Test"
        data = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "rvlimit": 1,
            "titles": title,
            "format": "json",
            "formatversion": "2",
        }
        try:
            raw = urlopen(url1, urlencode(data).encode("utf8")).read()
        except OSError:
            pytest.skip("cannot continue because of unsuccessful web call")
        res = json.loads(raw.decode("utf8"))
        revision = res["query"]["pages"][0]["revisions"][0]
        text = revision["slots"]["main"]["content"]
        try:
            expected = urlopen(url2.format(title)).read().decode("utf8")
        except OSError:
            pytest.skip("cannot continue because of unsuccessful web call")
        actual = mwparserfromhell.parse(text)
        assert expected == actual
