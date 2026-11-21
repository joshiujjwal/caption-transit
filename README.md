# caption-transit

An accessibility infographic for readable **BART and NYC MTA subway announcements**: hearing access, noisy trains, clear language, and greater independence.

Live: [Homepage](https://joshiujjwal.github.io/caption-transit/) · [NYC](https://joshiujjwal.github.io/caption-transit/nyc/) · [SF / BART](https://joshiujjwal.github.io/caption-transit/sf/)

A dependency-free static site: a homepage, `/nyc/`, and `/sf/`, sharing `styles.css`. Each city page has concise sourced context and its own Change.org petition. SF covers BART, not Muni. No backend, JavaScript, analytics, signature collection, or live transit integration. Not affiliated with or endorsed by either operator.

The page fits standard desktop and phone viewports without scrolling. Very short windows or enlarged text can scroll naturally rather than clip content. Technical research and outreach guidance live here, not on the infographic.

## Preview

With Python 3.9 or newer, from the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000`, `/nyc/`, or `/sf/`. Relative navigation and stylesheets also support GitHub Pages project paths. Stop the server with Ctrl+C. No build or package installation is required.

## Validate

```sh
python3 scripts/check_site.py
python3 -m unittest discover -s tests
python3 scripts/check_site.py --external
```

The structural check validates all three pages, local assets, directory-index routes, anchors, basic document structure, operator-specific signing links or official fallback routes, and regional publication states. It requires matching homepage/city petitions, distinct clean Change.org URLs, and consistent footer status. It is not an HTML conformance validator or WCAG certification. External checks contact public linked URLs only: exit 1 means a broken HTTP destination or structural failure; exit 2 means access blocks/network errors require manual review.

Before publishing, also check mobile/desktop layouts, keyboard-only navigation and visible focus, 200% zoom and narrow reflow, no-JavaScript use, print layout, and screen-reader landmarks/headings. Record checks that could not be performed.

Infographic validation: structural checks and 13 regression tests pass. Chromium confirmed all three pages fit without scrolling at 1280x720, 768x1024, 375x667, and 320x568, with correct city petitions, no-JavaScript navigation, project-path hosting, and automated axe WCAG A/AA checks. Earlier homepage checks also covered 1440x900, 1024x768, 390x844, keyboard focus, print rendering, and narrow/zoom-equivalent reflow. Both public petitions were verified in the browser before linking. Short-screen layouts allow overflow instead of hiding content. Browser helpers were installed only in the session workspace, not as project dependencies. The manual publishing workflow's YAML and city-page staging were validated.

Limitations: no manual screen-reader testing, actual browser-menu zoom testing, or cross-browser verification was performed. Initial automated source checks returned HTTP 403 for agency URLs; the agency content was researched separately, with the R211 excerpt-only limitation noted below. The public petitions were readable, but a later JavaScript-enabled automated visit hit Change.org's session API HTTP 403 and displayed a server error. Verify signing in a normal logged-in browser before sharing. Automated accessibility checks are not certification.

## Content and source maintenance

The short infographic copy lives in `index.html`, `nyc/index.html`, and `sf/index.html`. Keep it focused on why readable announcements matter and their intended benefits. City pages cite existing displays without claiming complete live-caption coverage. Translations are a possibility to explore, not an existing feature or a promise. Don't add invented impact figures.

Research reviewed November 21, 2026:

- [BART Fleet of the Future](https://www.bart.gov/about/projects/cars) describes next-stop/customer-service displays and hearing assistance.
- [MTA R211 announcement](https://www.mta.info/press-release/mta-announces-rollout-of-first-r211-train-cars-d-line) describes station-information displays, not every NYC subway fleet. Reviewed through the indexed official excerpt; direct access returned HTTP 403.
- [Luminator rail displays](https://luminator.com/rail/infotainment-displays) and [E Ink technology](https://esg.eink.com/en/focus/article/product) illustrate options, not agency compatibility or installed prices.
- [BART advertising](https://www.bart.gov/about/business/advertising) and [MTA advertising](https://www.mta.info/doing-business-with-us/advertising) do not establish permission for caption sponsorship.

Complete live-announcement coverage, integration, safety approvals, installed costs, and sponsorship remain unconfirmed. Recheck official sources and action links before publishing. Captioning must complement audio and hearing assistance; emergencies come before ads. Don't substitute consumer screen prices for rail-system costs or use unreviewed transcription as emergency guidance.

## Outreach wording

For BART, start with [Customer Services](https://www.bart.gov/contact/comments) or the [Accessibility Task Force](https://www.bart.gov/about/bod/advisory/accessibility). For NYC MTA, use [official feedback routes](https://www.mta.info/contact-us) or [ACTA](https://www.mta.info/accessibility/ACTA).

Suggested draft, to personalize and send yourself:

> Please review whether essential onboard announcements also appear as readable text. Work with disabled riders on a pilot, reusing suitable screens where feasible. Keep audio, consider plain language and translations, prioritize emergency information, and publish results and costs. Please route this request to accessibility, operations, and fleet engineering.

## Regional petitions

Both petitions are public, and the infographic's buttons link to them:

- [BART / SF Bay Area](https://www.change.org/p/make-bart-announcements-readable-not-just-audible)
- [NYC MTA subway](https://www.change.org/p/make-nyc-subway-announcements-readable-not-just-audible)

The owner published these through their own account. Clean URLs omit personal referral and share-tracking parameters. Drafts remain in `petitions/bart.txt` and `petitions/nyc-mta.txt`; they are not included in the Pages deployment. Signing happens on Change.org, not this site.

For future updates:

1. Keep the `bart-petition` and `mta-petition` buttons mapped to the correct regional petition, with `data-operator` unchanged and `data-petition-status="published"`. Update the homepage and matching city page together.
2. To withdraw a signing link, set that button's status to `unpublished`, restore its official feedback URL and “Ask” label, and update footer wording.
3. Set each footer's `data-status` to `published` when all its signing links are published, `unpublished` when none are, or `partial` for a mixed homepage state. A city page has only one petition.
4. Run validation and manually check the title, intended recipients, and signing page. The checker validates state and URL structure, not petition ownership or content.

Owner follow-up: add the responsible BART and MTA/NYC Transit leadership as decision-makers in Change.org. At verification, NYC listed the New York governor; the BART page had no decision-maker section.

Do not add an on-site signature form, tracker, payment collection, or automatic outreach. External services have their own privacy practices.

## Publishing on GitHub Pages

The site is published on GitHub Pages with owner approval. `.github/workflows/pages.yml` only runs through **manual dispatch**, and requires its publication-approval checkbox. It stages only `index.html`, `styles.css`, `nyc/index.html`, and `sf/index.html`, not tests, scripts, or repository documentation.

For future updates:

1. Review campaign identity, claims, all cited sources (including access-blocked pages), outreach drafts, and recipient choices. Resolve validation limitations.
2. Verify both regional signing links and recipient choices.
3. Commit/push the reviewed changes to `main`. Repository **Settings > Pages** already uses **GitHub Actions**.
4. In **Actions**, select **Publish static site (manual)**, choose `main`, check the approval input, and run it. Verify the deployed pages and links at the URL shown by the deploy job.

The public repository uses Actions-based Pages. After deployment, the live homepage, both city routes, and shared stylesheet were verified against the committed files. Local preview does not need GitHub authentication.

No operator has confirmed a pilot and no sponsor has been approached. The owner published the petitions; this assistant has not signed them or sent outreach.
