"""Install an official Camoufox browser build without using the GitHub API.

`camoufox fetch` discovers releases through api.github.com, which is limited to
60 unauthenticated requests per hour per IP. When that quota is exhausted the
sync step fails with "403 rate limit exceeded". This script skips discovery
entirely and drives the documented install path with an explicit asset, so it
only ever hits the release CDN.

Usage:
    python install-camoufox-browser.py <tag> <asset-name> <sha256>

Example:
    python install-camoufox-browser.py v152.0.4-beta.30 \
        camoufox-152.0.4-beta.30-win.x86_64.zip \
        ea52a02fb1cfb1813ef6a326bea03fb2b650c9774143d953a94a27bfc8f10072

Find the sha256 for a release with:
    https://api.github.com/repos/daijro/camoufox/releases  (field assets[].digest)
or from the release page itself.
"""

from __future__ import annotations

import re
import sys

from camoufox.pkgman import AvailableVersion, CamoufoxFetcher, Version

REPO = "daijro/camoufox"
TAG_RE = re.compile(r"^v(?P<version>[^-]+)-(?P<build>.+)$")


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2

    tag, asset, sha256 = argv[1], argv[2], argv[3].strip().lower()
    match = TAG_RE.match(tag)
    if not match:
        print(f"error: cannot parse release tag {tag!r}; expected v<version>-<build>")
        return 2
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        print(f"error: sha256 must be 64 hex characters, got {sha256!r}")
        return 2

    url = f"https://github.com/{REPO}/releases/download/{tag}/{asset}"
    version = Version(build=match["build"], version=match["version"])
    print(f"tag     : {tag}")
    print(f"asset   : {asset}")
    print(f"url     : {url}")
    print(f"sha256  : {sha256}")

    selected = AvailableVersion(
        version=version,
        url=url,
        is_prerelease=False,
        sha256=sha256,
    )
    fetcher = CamoufoxFetcher(selected_version=selected)
    fetcher.install()

    print(f"installed: {fetcher.verstr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
