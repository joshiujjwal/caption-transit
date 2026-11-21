import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BART_URL = "https://www.change.org/p/make-bart-announcements-readable-not-just-audible"
MTA_URL = "https://www.change.org/p/make-nyc-subway-announcements-readable-not-just-audible"
SPEC = importlib.util.spec_from_file_location("check_site", ROOT / "scripts/check_site.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class SiteChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        (self.root / "styles.css").write_text((ROOT / "styles.css").read_text(encoding="utf-8"), encoding="utf-8")
        for city in ("nyc", "sf"):
            (self.root / city).mkdir()
            (self.root / city / "index.html").write_text(
                (ROOT / city / "index.html").read_text(encoding="utf-8"), encoding="utf-8",
            )

    def check(self, html):
        (self.root / "index.html").write_text(html, encoding="utf-8")
        return CHECK.check_site(self.root)[0]

    def unpublished_site(self):
        return (self.html
                .replace('data-petition-status="published"', 'data-petition-status="unpublished"')
                .replace('data-status="published"', 'data-status="unpublished"')
                .replace(BART_URL, "https://www.bart.gov/contact/comments")
                .replace(MTA_URL, "https://www.mta.info/contact-us"))

    def test_current_site_has_no_structural_errors(self):
        self.assertEqual(self.check(self.html), [])

    def test_missing_anchor_and_asset_are_reported(self):
        html = self.html.replace('href="#main"', 'href="#missing"')
        html = html.replace('href="styles.css"', 'href="missing.css"')
        errors = self.check(html)
        self.assertTrue(any("Missing anchor target" in error for error in errors))
        self.assertTrue(any("Missing or out-of-site asset" in error for error in errors))

    def test_operator_action_cannot_point_to_other_operator(self):
        html = self.unpublished_site().replace(
            "https://www.bart.gov/contact/comments", "https://www.mta.info/contact-us",
        )
        self.assertTrue(any("Wrong official action route" in error for error in self.check(html)))

    def test_unpublished_petition_cannot_offer_signing(self):
        html = self.unpublished_site().replace("https://www.bart.gov/contact/comments", BART_URL)
        self.assertTrue(any("Unpublished petition" in error for error in self.check(html)))

    def test_published_petition_requires_specific_approved_link(self):
        html = re.sub(r'<a id="bart-petition".*?</a>', "", self.html)
        self.assertTrue(any("exactly one" in error for error in self.check(html)))
        for url in ("https://www.change.org/", "https://www.change.org/p/",
                    "https://fakechange.org/p/example", BART_URL + "?recruiter=example"):
            with self.subTest(url=url):
                candidate = self.html.replace(BART_URL, url)
                self.assertTrue(any("explicit Change.org" in error for error in self.check(candidate)))

    def test_regional_petitions_cannot_share_one_url(self):
        errors = self.check(self.html.replace(MTA_URL, BART_URL))
        self.assertTrue(any("separate petition URLs" in error for error in errors))

    def test_unpublished_and_partial_states_can_use_official_fallbacks(self):
        unpublished = self.unpublished_site()
        self.assertEqual(self.check(unpublished), [])
        partial = (unpublished
                   .replace('data-operator="bart" data-petition-status="unpublished"',
                            'data-operator="bart" data-petition-status="published"')
                   .replace("https://www.bart.gov/contact/comments", BART_URL)
                   .replace('data-status="unpublished"', 'data-status="partial"'))
        self.assertEqual(self.check(partial), [])

    def test_footer_cannot_claim_wrong_publication_status(self):
        errors = self.check(self.html.replace('data-status="published"', 'data-status="unpublished"'))
        self.assertTrue(any("Footer petition state" in error for error in errors))

    def test_external_runtime_asset_is_rejected(self):
        html = self.html.replace('href="styles.css"', 'href="https://example.com/style.css"')
        self.assertTrue(any("External runtime asset" in error for error in self.check(html)))

    def test_city_routes_share_assets_and_have_matching_petitions(self):
        self.assertEqual(self.check(self.html), [])
        for city in ("nyc", "sf"):
            with self.subTest(city=city):
                self.assertEqual(CHECK.check_site(self.root, Path(city) / "index.html")[0], [])

    def test_city_cannot_link_the_other_petition(self):
        self.check(self.html)
        index = self.root / "sf/index.html"
        index.write_text(index.read_text(encoding="utf-8").replace(BART_URL, MTA_URL), encoding="utf-8")
        errors = CHECK.check_site(self.root, Path("sf/index.html"))[0]
        self.assertTrue(any("Regional petition must match" in error for error in errors))

    def test_missing_city_directory_index_is_reported(self):
        (self.root / "nyc/index.html").unlink()
        errors = self.check(self.html)
        self.assertTrue(any("Missing or out-of-site asset: nyc/" in error for error in errors))

    def test_shared_asset_must_stay_inside_site_root(self):
        self.check(self.html)
        index = self.root / "nyc/index.html"
        index.write_text(index.read_text(encoding="utf-8").replace("../styles.css", "../../styles.css"), encoding="utf-8")
        errors = CHECK.check_site(self.root, Path("nyc/index.html"))[0]
        self.assertTrue(any("Missing or out-of-site asset" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
