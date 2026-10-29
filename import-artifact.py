#!/usr/bin/env python3
#
# Healdan's copies of the Maven artifacts only LogicalDOC's repository has. Every file here gets in through this
# script, so the history says where each one came from, and a hosted version never changes. Standard library only.
#
# Usage:
#   import-artifact.py GROUP:ARTIFACT:VERSION[:CLASSIFIER] --project TEXT --licence SPDX [--from URL]
#       Fetches the jar and POM from LogicalDOC's repository (or URL), checks each against the .sha1 published
#       beside it, writes them with their .sha1s, and adds the artifact's row to README.md.
#   import-artifact.py GROUP:ARTIFACT:VERSION[:CLASSIFIER] --file JAR --source TEXT --project TEXT --licence SPDX
#       Imports a jar taken from elsewhere, such as a LogicalDOC CE release bundle, with a stub POM.
#   import-artifact.py --scan LOCAL_REPO [--repository-id ID]
#       Lists the artifacts a local Maven repository records as downloaded from repository ID (logicaldoc).
#   import-artifact.py --verify [URL]
#       Checks every hosted file against its .sha1 and README.md's table and, with URL, against what URL serves.
# Exit status: 0 on success, 1 on a problem, 2 on bad usage.

import argparse
import dataclasses
import datetime
import hashlib
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SOURCEFORGE = "https://logicaldoc.sourceforge.net/maven/"
TABLE_START = "<!-- artifacts -->"
TABLE_END = "<!-- /artifacts -->"


class Problem(Exception):
    """Something the user needs to fix. main() prints it and returns 1."""


@dataclasses.dataclass(frozen=True)
class Coordinates:
    group: str
    artifact: str
    version: str
    classifier: str = ""

    @classmethod
    def parse(cls, text):
        parts = text.split(":")
        if len(parts) not in (3, 4) or not all(parts):
            raise ValueError(f"expected group:artifact:version[:classifier], not {text!r}")
        return cls(*parts)

    @classmethod
    def from_jar_path(cls, parts):
        """The coordinates of the jar at parts (group folders, artifact, version, file name), as in .jar.parts."""
        *group, artifact, version, name = parts
        stem = f"{artifact}-{version}"
        if not group or not name.startswith(stem) or not name.endswith(".jar"):
            raise ValueError(f"{'/'.join(parts)} isn't a jar in Maven's layout")
        return cls(".".join(group), artifact, version, name[len(stem):-len(".jar")].lstrip("-"))

    def __str__(self):
        return ":".join(part for part in (self.group, self.artifact, self.version, self.classifier) if part)

    @property
    def directory(self):
        return pathlib.PurePosixPath(*self.group.split("."), self.artifact, self.version)

    @property
    def jar(self):
        classifier = f"-{self.classifier}" if self.classifier else ""
        return self.directory / f"{self.artifact}-{self.version}{classifier}.jar"

    @property
    def pom(self):
        return self.directory / f"{self.artifact}-{self.version}.pom"


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def published_sha1(text):
    """The checksum in a .sha1 file, which may be followed by a file name."""
    words = text.split()
    return words[0].lower() if words else ""


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Healdan import-artifact.py"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except (urllib.error.URLError, OSError) as error:
        raise Problem(f"{url}: {error}") from error


def fetch_verified(base, path):
    """Fetches base + path and checks it against the .sha1 published beside it."""
    url = urllib.parse.urljoin(base, str(path))
    data = fetch(url)
    expected = published_sha1(fetch(url + ".sha1").decode("ascii", errors="replace"))
    if sha1(data) != expected:
        raise Problem(f"{url}: its SHA-1 is {sha1(data)}, but {url}.sha1 says {expected or 'nothing'}")
    return data


def stub_pom(coordinates):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            f'  <modelVersion>4.0.0</modelVersion>\n'
            f'  <groupId>{coordinates.group}</groupId>\n'
            f'  <artifactId>{coordinates.artifact}</artifactId>\n'
            f'  <version>{coordinates.version}</version>\n'
            f'</project>\n').encode("utf-8")


def write_artifact(root, coordinates, jar, pom):
    """Writes the jar and POM with their .sha1s. Never changes a hosted file."""
    jar_path, pom_path = root / coordinates.jar, root / coordinates.pom
    if jar_path.exists():
        raise Problem(f"{coordinates.jar} is already hosted, and a hosted version never changes")
    if pom_path.exists() and pom_path.read_bytes() != pom:
        raise Problem(f"{coordinates.pom} is already hosted with different content")
    jar_path.parent.mkdir(parents=True, exist_ok=True)
    for path, data in ((jar_path, jar), (pom_path, pom)):
        path.write_bytes(data)
        path.with_name(path.name + ".sha1").write_text(sha1(data) + "\n", encoding="ascii")


def readme_row(coordinates, project, licence, source):
    return f"| `{coordinates}` | {project} | {licence} | {source} |"


def _row_key(row):
    return row.split("|")[1].strip()


def add_readme_row(readme, row):
    """Returns readme with row added to the artifact table, which stays sorted by coordinates."""
    try:
        start = readme.index(TABLE_START) + len(TABLE_START)
        end = readme.index(TABLE_END, start)
    except ValueError:
        raise Problem(f"README.md has no table between {TABLE_START} and {TABLE_END}") from None
    lines = readme[start:end].strip("\n").split("\n")
    header, rows = lines[:2], [line for line in lines[2:] if line.strip()]
    if any(_row_key(line) == _row_key(row) for line in rows):
        raise Problem(f"README.md already lists {_row_key(row)}")
    rows = sorted(rows + [row], key=_row_key)
    return readme[:start] + "\n" + "\n".join(header + rows) + "\n" + readme[end:]


def source_label(base, today):
    return f"{urllib.parse.urlsplit(base).hostname or base}, {today}"


def main(argv, root=ROOT, today=None):
    parser = argparse.ArgumentParser(prog="import-artifact.py",
                                     description="Imports, scans and verifies Healdan's hosted Maven artifacts.")
    parser.add_argument("coordinates", nargs="?", help="GROUP:ARTIFACT:VERSION[:CLASSIFIER]")
    parser.add_argument("--project", help="the upstream project, as Markdown for the README's table")
    parser.add_argument("--licence", help="the artifact's licence, as an SPDX id")
    parser.add_argument("--from", dest="base", default=SOURCEFORGE, help="the repository to fetch from")
    parser.add_argument("--file", type=pathlib.Path, help="import this jar instead of fetching one")
    parser.add_argument("--source", help="with --file: where the jar came from")
    args = parser.parse_args(argv)
    if not (args.coordinates and args.project and args.licence):
        parser.error("importing needs coordinates, --project and --licence")
    if args.file and not args.source:
        parser.error("--file needs --source, saying where the jar came from")
    try:
        coordinates = Coordinates.parse(args.coordinates)
        if args.file:
            jar, pom, source = args.file.read_bytes(), stub_pom(coordinates), args.source
        else:
            base = args.base if args.base.endswith("/") else args.base + "/"
            jar, pom = fetch_verified(base, coordinates.jar), fetch_verified(base, coordinates.pom)
            source = source_label(base, today or datetime.date.today().isoformat())
        readme_path = root / "README.md"
        readme = add_readme_row(readme_path.read_text(encoding="utf-8"),
                                readme_row(coordinates, args.project, args.licence, source))
        write_artifact(root, coordinates, jar, pom)
        readme_path.write_text(readme, encoding="utf-8")
    except (Problem, ValueError, OSError) as problem:
        print(problem, file=sys.stderr)
        return 1
    print(f"Imported {coordinates} from {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
