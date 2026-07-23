---
name: download-scholarly-papers
description: Download, verify, rename, deduplicate, organize, and package scholarly paper PDFs from DOI, title, URL, or literature lists using legal open-access sources or a user-authorized institutional library subscription. Use for requests such as 下载论文、批量下载文献、通过学校账号获取全文、按 DOI 获取 PDF、整理已下载论文、校验论文 PDF，especially when publisher access requires institutional Shibboleth/SAML sign-in.
---

# Download Scholarly Papers

## Outcome

Obtain the requested legal full-text PDFs, keep an auditable acquisition manifest, validate every file, and deliver one clean folder plus an optional ZIP archive.

## Credential and Access Guardrails

- Treat usernames, passwords, OTPs, recovery codes, and session data as extremely sensitive.
- Use credentials only when the user explicitly supplies them for the current download task.
- Enter institutional credentials only on a verified official identity-provider domain. State the domain before submitting.
- Never place credentials in scripts, files, manifests, shell commands, command-line arguments, environment variables, URLs, browser password stores, or final responses.
- Never inspect or export browser cookies, profiles, local storage, saved passwords, or session stores.
- Do not bypass paywalls, bot protections, download limits, CAPTCHAs, or publisher security interstitials.
- Ask the user before solving each CAPTCHA. Pause for the user on MFA, OTP, push approval, or other human verification.
- Do not change account settings, save passwords, request papers from authors, or send external messages unless the user separately asks.
- Use only the papers the user placed in scope. Respect institutional and publisher license limits; do not turn an ordinary retrieval task into text-and-data mining.

## Inputs and Defaults

Accept DOI strings, titles, publisher URLs, citation files, spreadsheets, or a numbered literature list. Preserve the user's numbering when present.

If the output location is unspecified, create a descriptive folder in the current workspace, such as `论文下载/已获取文献_YYYY-MM-DD`. Do not place downloaded papers in the skill directory.

Record for each item:

- requested number, title, DOI, year, and publisher;
- acquisition status and source type (`出版社订阅版`, `开放获取版`, `作者公开版`);
- final filename, page count, file size, SHA-256, and failure reason when unavailable.

## Workflow

1. Normalize and deduplicate the requested list by DOI, then exact title.
2. Query an academic metadata connector before using the browser when one is available. Use it for DOI/title resolution, not for restricted full-text retrieval.
3. Read and follow the Browser skill before authenticated browser work. Group papers by publisher to reuse one valid institutional session.
4. Navigate through the DOI or verified publisher article page.
5. Prefer a legal open-access publisher PDF or repository copy when it is the requested/version-equivalent article.
6. For subscription content, choose `Access through your institution`, `Institutional Sign In`, or the publisher's Shibboleth/SAML path.
7. Select the user's institution and verify the redirect hostname before entering credentials. Never enter a university password on a publisher, search engine, proxy, or unrelated domain.
8. After authentication, verify an authoritative access signal such as `Access provided by <institution>` or an enabled full-text PDF link.
9. Trigger the publisher's visible PDF download. If a PDF opens in a native viewer, use the publisher wrapper/link and its unique PDF iframe or media element with `downloadMedia` when available. Do not extract cookies for `curl` or another downloader.
10. Wait for `.crdownload` or equivalent temporary files to disappear. Copy the completed PDF into the workspace immediately and rename it using the preserved number plus stable metadata, for example `05_2023_TPWRS_Wen_Temporally_Coupled_Flexibility.pdf`.
11. Repeat within the authenticated session, keeping user-visible progress updates at least once per minute during long downloads.
12. Run the bundled organizer:

```powershell
python scripts/validate_and_organize.py "<download-dir>" `
  --output-dir "<clean-output-dir>" `
  --zip "<clean-output-dir>.zip" `
  --recursive
```

13. Use the PDF skill to render and visually inspect at least the first page of every newly acquired publisher PDF. Treat parser warnings as non-fatal only when page count, text extraction, and rendering succeed.
14. Deliver the clean folder and ZIP, plus counts for acquired, unavailable, invalid, and duplicate files. Never repeat credentials.

## Publisher Routing

Read [references/publisher-workflows.md](references/publisher-workflows.md) when handling IEEE Xplore, ScienceDirect/Elsevier, or a new publisher with institutional authentication.

## Failure Handling

- If the official IdP rejects the credentials, report the sign-in failure without echoing any credentials.
- If access is not covered by the subscription, try a lawful open-access or author manuscript source and label the version accurately.
- If a security challenge or CAPTDCHA appears, stop and ask the user rather than bypassing it.
- If the browser cannot export a fully loaded PDF, try the publisher's own wrapper/media download surface. Do not use session-cookie extraction as a workaround.
- Keep unavailable items in the manifest with the exact reason. Do not create fake, screenshot-only, or unrelated PDFs.

## Bundled Script

`scripts/validate_and_organize.py` performs deterministic PDF signature checks, pypdf parsing, page-count validation, SHA-256 deduplication, non-destructive copying, CSV manifest generation, and ZIP packaging. It intentionally has no credential input.
