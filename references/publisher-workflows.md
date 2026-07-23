# Publisher Workflows

## Universal Institutional Login Checks

1. Start from the DOI or publisher article page.
2. Use the publisher's visible institutional-access control.
3. Select the exact institution; do not guess a similarly named organization.
4. Before entering credentials, confirm the hostname belongs to the institution's official identity provider.
5. Reuse the authenticated publisher session for the current scoped list.
6. Never inspect/export cookies or pass credentials to shell tools.

Known safe identity-provider metadata:

- Heidelberg University: institution name `Universität Heidelberg` / `Heidelberg University`; entity ID `https://idp.uni-heidelberg.de`; enter university credentials only on a `uni-heidelberg.de` hostname.

Do not store a user's Uni-ID, email address, password, or OTP in this reference.

## IEEE Xplore

1. Resolve the DOI to `https://ieeexplore.ieee.org/document/<article-number>`.
2. Verify institutional access on the article page.
3. The visible PDF link commonly points to:

   `https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=<article-number>`

4. The wrapper commonly contains one iframe whose `src` is:

   `https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=<article-number>&ref=`

5. After a fresh DOM snapshot, confirm the iframe locator count is exactly one, then use the browser locator's `downloadMedia` operation. This often succeeds when the Chrome PDF viewer toolbar does not emit a normal page download event.
6. Wait for any `.crdownload` file to finish before copying the PDF.
7. Confirm the downloaded first page title and, when present, the institutional license footer.

Do not use guessed article numbers. Resolve them from the DOI or the authoritative IEEE URL.

## ScienceDirect / Elsevier

1. Resolve the DOI to the authoritative `sciencedirect.com/science/article/pii/<PII>` page.
2. Use `Access through your institution` or the institutional sign-in control.
3. Select the institution and verify its official IdP hostname before submitting credentials.
4. After access is granted, use the visible `View PDF` or `Download PDF` control.
5. Prefer the publisher-exposed PDF/media link, often a `pdfft` URL, and use `downloadMedia` on the unique PDF link or media element.
6. If Cloudflare, a CAPTCHA, or a browser safety interstitial appears, do not bypass it. Ask the user to complete/approve the required human verification.

## Other Publishers

- Use the same DOI -> publisher -> institutional sign-in -> official IdP -> visible PDF sequence.
- Inspect a fresh DOM snapshot before constructing locators.
- Prefer stable `href`, `data-*`, role, and accessible-name contracts exposed by the page.
- Confirm a locator resolves uniquely before clicking or downloading.
- If an authentication flow is unclear, consult the institution library's official database entry and the publisher's official access documentation.
