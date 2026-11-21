#!/usr/bin/env python3
"""Check static-site structure and actions; optionally check external links."""

import argparse
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.stack = []
        self.errors = []
        self.anchors = []
        self.current_anchor = None

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.elements.append((tag, attrs))
        if tag not in VOID_TAGS:
            self.stack.append(tag)
        if tag == "a":
            if self.current_anchor is not None:
                self.errors.append("Nested links are not valid.")
            self.current_anchor = [attrs, ""]

    def handle_startendtag(self, tag, attributes):
        self.handle_starttag(tag, attributes)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("Unexpected closing tag: </{}>.".format(tag))
        else:
            self.stack.pop()
        if tag == "a" and self.current_anchor is not None:
            self.anchors.append(self.current_anchor)
            self.current_anchor = None

    def handle_data(self, data):
        if self.current_anchor is not None:
            self.current_anchor[1] += data


def is_petition_url(value):
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"change.org", "www.change.org"}
        and parsed.path.startswith("/p/")
        and bool(parsed.path[3:].strip("/"))
        and not parsed.username
        and not parsed.query
        and not parsed.fragment
    )


def check_site(root, page=Path("index.html")):
    errors = []
    document = Document()
    index = root / page
    if not index.is_file():
        return ["Missing {}.".format(page)], []
    html = index.read_text(encoding="utf-8")
    document.feed(html)
    document.close()
    errors.extend(document.errors)
    if document.stack:
        errors.append("Unclosed tags: {}.".format(", ".join(document.stack)))
    if not re.match(r"\s*<!doctype html>", html, re.IGNORECASE):
        errors.append("Missing HTML doctype.")
    tags = Counter(tag for tag, _ in document.elements)
    ids = Counter(attrs["id"] for _, attrs in document.elements if "id" in attrs)
    errors.extend("Duplicate id: {}.".format(key) for key, count in ids.items() if count > 1)
    for tag in ("html", "head", "body", "main", "h1", "title"):
        if tags[tag] != 1:
            errors.append("Expected exactly one <{}>.".format(tag))
    if not any(tag == "html" and attrs.get("lang") == "en" for tag, attrs in document.elements):
        errors.append("Set the document language to English.")
    if not any(tag == "meta" and attrs.get("name") == "viewport" for tag, attrs in document.elements):
        errors.append("Missing responsive viewport metadata.")
    if not any("skip-link" in attrs.get("class", "").split() and attrs.get("href") == "#main"
               for attrs, _ in document.anchors):
        errors.append("Missing skip link to #main.")

    external = set()
    for tag, attrs in document.elements:
        if tag in {"script", "form", "input", "iframe", "base", "object", "embed"}:
            errors.append("Unexpected active or data-collection element: <{}>.".format(tag))
        if tag == "img" and "alt" not in attrs:
            errors.append("Image missing alternative text.")
        if tag == "link" and attrs.get("rel") != "stylesheet":
            errors.append("Only local stylesheet links are expected.")
        for attribute in ("href", "src"):
            value = attrs.get(attribute)
            if value is None:
                continue
            parsed = urlsplit(value)
            if not value.strip():
                errors.append("Empty {} on <{}>.".format(attribute, tag))
            elif parsed.scheme or parsed.netloc:
                if parsed.scheme != "https" or not parsed.netloc or parsed.username:
                    errors.append("Unsupported URL: {}.".format(value))
                elif tag != "a":
                    errors.append("External runtime asset is not allowed: {}.".format(value))
                else:
                    external.add(value)
            else:
                if parsed.path:
                    asset = (index.parent / unquote(parsed.path)).resolve()
                    if asset.is_dir():
                        asset = asset / "index.html"
                    if root.resolve() not in asset.parents or not asset.is_file():
                        errors.append("Missing or out-of-site asset: {}.".format(value))
                    elif parsed.fragment:
                        errors.append("Cross-file fragments need manual review: {}.".format(value))
                elif not parsed.fragment or unquote(parsed.fragment) not in ids:
                    errors.append("Missing anchor target: {}.".format(value))

    operator_hosts = {"bart": "www.bart.gov", "mta": "www.mta.info"}
    region_operators = {"nyc": "mta", "sf": "bart"}
    expected_operators = (
        {region_operators[page.parts[0]]}
        if page.parts[0] in region_operators
        else set(operator_hosts)
    )
    found_operators = set()
    petition_states = {}
    published_urls = []
    for attrs, text in document.anchors:
        if not (attrs.get("aria-label") or text).strip():
            errors.append("Link has no accessible name: {}.".format(attrs.get("href", "")))
        operator = attrs.get("data-operator")
        status = attrs.get("data-petition-status")
        value = attrs.get("href", "")
        parsed = urlsplit(value)
        if status is not None:
            if operator not in operator_hosts or operator in petition_states:
                errors.append("Each operator needs exactly one petition-status route.")
            else:
                petition_states[operator] = status
            if status not in {"published", "unpublished"}:
                errors.append("Invalid operator petition status: {}.".format(status))
        if operator:
            found_operators.add(operator)
            if status == "published":
                if not is_petition_url(value):
                    errors.append("Signing link must be an explicit Change.org petition URL.")
                else:
                    published_urls.append(value)
            elif (operator not in operator_hosts or parsed.scheme != "https"
                    or parsed.hostname != operator_hosts[operator] or parsed.path in {"", "/"}):
                errors.append("Wrong official action route for {}: {}.".format(operator, value))
                if status == "unpublished":
                    errors.append("Unpublished petition must not expose a signing link.")
        if ((parsed.hostname or "").endswith("change.org") or attrs.get("id") == "petition-link"):
            if operator not in operator_hosts or status != "published":
                errors.append("Signing links require a published operator petition status.")
    if found_operators != expected_operators:
        errors.append("Provide matching operator actions for {}.".format(page))
    if set(petition_states) != expected_operators:
        errors.append("Each operator needs exactly one petition-status route.")
    if len(published_urls) != len(set(published_urls)):
        errors.append("BART and NYC MTA must use separate petition URLs.")

    petitions = [attrs for _, attrs in document.elements if attrs.get("id") == "petition"]
    published_count = sum(state == "published" for state in petition_states.values())
    expected_status = (
        "published" if published_count == len(expected_operators)
        else "partial" if published_count else "unpublished"
    )
    if len(petitions) != 1 or petitions[0].get("data-status") != expected_status:
        errors.append("Footer petition state does not match operator links.")

    if page != Path("index.html") and (root / "index.html").is_file():
        homepage = Document()
        homepage.feed((root / "index.html").read_text(encoding="utf-8"))
        homepage_links = {
            attrs["data-operator"]: attrs.get("href")
            for attrs, _ in homepage.anchors if "data-petition-status" in attrs
        }
        for attrs, _ in document.anchors:
            if "data-petition-status" in attrs and attrs.get("href") != homepage_links.get(attrs.get("data-operator")):
                errors.append("Regional petition must match the homepage's operator link.")

    stylesheet = root / "styles.css"
    if stylesheet.is_file():
        css = stylesheet.read_text(encoding="utf-8")
        if re.search(r"@import\b|url\s*\(", css, re.IGNORECASE):
            errors.append("Stylesheet unexpectedly loads additional assets; review them explicitly.")
    else:
        errors.append("Missing styles.css.")
    return errors, sorted(external)


def check_external(url):
    try:
        request = Request(url, headers={"User-Agent": "CaptionTransit-LinkCheck/1.0"})
        with urlopen(request, timeout=20) as response:
            # Read a bounded sample to detect access challenges, not scrape pages.
            sample = response.read(8192).decode("utf-8", errors="replace").lower()
            if any(marker in sample for marker in ("<title>request access", "verify you are human", "captcha")):
                return "REVIEW access challenge: {}".format(url)
            return "OK {}: {}".format(response.status, url)
    except HTTPError as error:
        label = "REVIEW access/rate limit" if error.code in {401, 403, 429} else "FAIL"
        return "{} HTTP {}: {}".format(label, error.code, url)
    except (URLError, TimeoutError, OSError) as error:
        return "REVIEW network error: {} ({})".format(url, error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--external", action="store_true", help="Check public URLs; access blocks need manual review.")
    args = parser.parse_args()
    errors = []
    links = set()
    for page in (Path("index.html"), Path("nyc/index.html"), Path("sf/index.html")):
        page_errors, page_links = check_site(args.root, page)
        errors.extend("{}: {}".format(page, error) for error in page_errors)
        links.update(page_links)
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print("PASS: homepage and city routes, assets, anchors, operator actions, and regional petition states.")
    if args.external:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(check_external, sorted(links)))
        for result in results:
            print(result)
        if any(result.startswith("FAIL") for result in results):
            return 1
        if any(result.startswith("REVIEW") for result in results):
            print("External-link review is incomplete; resolve flagged URLs before public launch.")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
