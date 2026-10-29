import contextlib
import hashlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("import_artifact", HERE.parent / "import-artifact.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

README = ("# Healdan's Maven Repository\n\n<!-- artifacts -->\n| Coordinates | Project | Licence | Source |\n"
          "|---|---|---|---|\n<!-- /artifacts -->\n\n## Not Hosted\n")
JPF = "net.sf.jpf:jpf:1.5.1"
KSOAP = "com.google.code.ksoap2-android:ksoap2-android-assembly:3.3.0:jar-with-dependencies"


class CoordinatesTest(unittest.TestCase):

    def test_paths(self):
        jpf = tool.Coordinates.parse(JPF)
        self.assertEqual("net/sf/jpf/jpf/1.5.1/jpf-1.5.1.jar", jpf.jar.as_posix())
        self.assertEqual("net/sf/jpf/jpf/1.5.1/jpf-1.5.1.pom", jpf.pom.as_posix())
        self.assertEqual(JPF, str(jpf))

    def test_classifier_names_the_jar_not_the_pom(self):
        ksoap = tool.Coordinates.parse(KSOAP)
        folder = "com/google/code/ksoap2-android/ksoap2-android-assembly/3.3.0/"
        self.assertEqual(folder + "ksoap2-android-assembly-3.3.0-jar-with-dependencies.jar", ksoap.jar.as_posix())
        self.assertEqual(folder + "ksoap2-android-assembly-3.3.0.pom", ksoap.pom.as_posix())
        self.assertEqual(KSOAP, str(ksoap))

    def test_bad_coordinates_refused(self):
        for text in ("a:b", "a::c", "a:b:c:d:e", ""):
            with self.subTest(text), self.assertRaises(ValueError):
                tool.Coordinates.parse(text)

    def test_from_jar_path_reverses_jar(self):
        for text in (JPF, KSOAP):
            with self.subTest(text):
                coordinates = tool.Coordinates.parse(text)
                self.assertEqual(coordinates, tool.Coordinates.from_jar_path(coordinates.jar.parts))


class ReadmeTest(unittest.TestCase):

    def test_rows_stay_sorted(self):
        readme = README
        for text in (JPF, "betelio:betelio:1.0"):
            readme = tool.add_readme_row(readme, tool.readme_row(tool.Coordinates.parse(text), "P", "L", "S"))
        self.assertIn("|---|---|---|---|\n| `betelio:betelio:1.0` | P | L | S |\n| `net.sf.jpf:jpf:1.5.1` | P | L | S |\n"
                      "<!-- /artifacts -->\n\n## Not Hosted\n", readme)

    def test_duplicate_row_refused(self):
        row = tool.readme_row(tool.Coordinates.parse(JPF), "P", "L", "S")
        with self.assertRaises(tool.Problem):
            tool.add_readme_row(tool.add_readme_row(README, row), row)

    def test_missing_table_refused(self):
        with self.assertRaises(tool.Problem):
            tool.add_readme_row("# No table\n", "| `a:b:c` | P | L | S |")

    def test_source_label(self):
        self.assertEqual("logicaldoc.sourceforge.net, 2026-10-29",
                         tool.source_label("https://logicaldoc.sourceforge.net/maven/", "2026-10-29"))


class ImportTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = pathlib.Path(tmp.name)
        self.root = self.base / "hosted"
        self.root.mkdir()
        (self.root / "README.md").write_text(README, encoding="utf-8")
        self.remote = self.base / "remote"
        self.remote_url = self.remote.as_uri() + "/"

    def publish(self, path, data, checksum=None):
        """Puts a file in the fake remote repository, with a .sha1 beside it as SourceForge writes one."""
        target = self.remote / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        checksum = checksum or hashlib.sha1(data).hexdigest()
        (target.parent / (target.name + ".sha1")).write_text(f"{checksum}  {target.name}\n", encoding="ascii")

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = tool.main(list(argv), root=self.root, today="2026-10-29")
        return status, out.getvalue(), err.getvalue()

    def import_jpf(self):
        return self.run_tool(JPF, "--from", self.remote_url, "--project", "[JPF](https://jpf.sourceforge.net/)",
                             "--licence", "LGPL-2.1-only")

    def test_imports_jar_pom_checksums_and_row(self):
        jpf = tool.Coordinates.parse(JPF)
        self.publish(jpf.jar, b"jar bytes")
        self.publish(jpf.pom, b"<project/>")
        status, out, err = self.import_jpf()
        self.assertEqual((0, ""), (status, err))
        self.assertIn(f"Imported {JPF}", out)
        self.assertEqual(b"jar bytes", (self.root / jpf.jar).read_bytes())
        self.assertEqual(b"<project/>", (self.root / jpf.pom).read_bytes())
        self.assertEqual(hashlib.sha1(b"jar bytes").hexdigest() + "\n",
                         (self.root / jpf.directory / "jpf-1.5.1.jar.sha1").read_text(encoding="ascii"))
        self.assertEqual(hashlib.sha1(b"<project/>").hexdigest() + "\n",
                         (self.root / jpf.directory / "jpf-1.5.1.pom.sha1").read_text(encoding="ascii"))
        self.assertIn(f"| `{JPF}` | [JPF](https://jpf.sourceforge.net/) | LGPL-2.1-only | {self.remote_url}, 2026-10-29 |",
                      (self.root / "README.md").read_text(encoding="utf-8"))

    def test_checksum_mismatch_refused_and_nothing_written(self):
        jpf = tool.Coordinates.parse(JPF)
        self.publish(jpf.jar, b"jar bytes", checksum="0" * 40)
        self.publish(jpf.pom, b"<project/>")
        status, _, err = self.import_jpf()
        self.assertEqual(1, status)
        self.assertIn("SHA-1", err)
        self.assertFalse((self.root / jpf.directory).exists())
        self.assertEqual(README, (self.root / "README.md").read_text(encoding="utf-8"))

    def test_missing_remote_file_refused(self):
        status, _, err = self.import_jpf()
        self.assertEqual(1, status)
        self.assertIn("jpf-1.5.1.jar", err)
        self.assertEqual(README, (self.root / "README.md").read_text(encoding="utf-8"))

    def test_hosted_version_never_changes(self):
        jpf = tool.Coordinates.parse(JPF)
        self.publish(jpf.jar, b"jar bytes")
        self.publish(jpf.pom, b"<project/>")
        self.assertEqual(0, self.import_jpf()[0])
        self.publish(jpf.jar, b"other bytes")
        status, _, err = self.import_jpf()
        self.assertEqual(1, status)
        self.assertIn("already", err)
        self.assertEqual(b"jar bytes", (self.root / jpf.jar).read_bytes())

    def test_file_import_writes_stub_pom_and_source(self):
        jar = self.base / "jpf.jar"
        jar.write_bytes(b"jar from a bundle")
        status, _, err = self.run_tool(JPF, "--file", str(jar), "--source", "LogicalDOC CE 9.3.2 release bundle",
                                       "--project", "JPF", "--licence", "LGPL-2.1-only")
        self.assertEqual((0, ""), (status, err))
        jpf = tool.Coordinates.parse(JPF)
        self.assertEqual(b"jar from a bundle", (self.root / jpf.jar).read_bytes())
        pom = (self.root / jpf.pom).read_text(encoding="utf-8")
        for element in ("<groupId>net.sf.jpf</groupId>", "<artifactId>jpf</artifactId>", "<version>1.5.1</version>"):
            self.assertIn(element, pom)
        self.assertIn("| LogicalDOC CE 9.3.2 release bundle |", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_classifier_import(self):
        ksoap = tool.Coordinates.parse(KSOAP)
        self.publish(ksoap.jar, b"assembly")
        self.publish(ksoap.pom, b"<project/>")
        status, _, err = self.run_tool(KSOAP, "--from", self.remote_url, "--project", "ksoap2-android",
                                       "--licence", "MIT")
        self.assertEqual((0, ""), (status, err))
        self.assertEqual(b"assembly", (self.root / ksoap.jar).read_bytes())
        self.assertTrue((self.root / ksoap.pom).is_file())

    def test_usage_errors(self):
        jar = self.base / "x.jar"
        jar.write_bytes(b"x")
        for argv in ((JPF, "--project", "P"),
                     (JPF, "--file", str(jar), "--project", "P", "--licence", "L")):
            with self.subTest(argv), self.assertRaises(SystemExit), \
                    contextlib.redirect_stderr(io.StringIO()):
                tool.main(list(argv), root=self.root, today="2026-10-29")


class WriteArtifactTest(unittest.TestCase):
    """write_artifact's guards, tested directly: a hosted file is never replaced, even when README.md has no row for it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.jpf = tool.Coordinates.parse(JPF)

    def test_existing_jar_refused_and_left_alone(self):
        jar = self.root / self.jpf.jar
        jar.parent.mkdir(parents=True)
        jar.write_bytes(b"hosted bytes")
        with self.assertRaises(tool.Problem) as caught:
            tool.write_artifact(self.root, self.jpf, b"new bytes", b"<project/>")
        self.assertIn("already hosted", str(caught.exception))
        self.assertEqual(b"hosted bytes", jar.read_bytes())
        self.assertFalse((self.root / self.jpf.pom).exists())

    def test_existing_pom_with_different_content_refused_and_left_alone(self):
        pom = self.root / self.jpf.pom
        pom.parent.mkdir(parents=True)
        pom.write_bytes(b"<hosted/>")
        with self.assertRaises(tool.Problem) as caught:
            tool.write_artifact(self.root, self.jpf, b"jar bytes", b"<new/>")
        self.assertIn("different content", str(caught.exception))
        self.assertEqual(b"<hosted/>", pom.read_bytes())
        self.assertFalse((self.root / self.jpf.jar).exists())

    def test_existing_pom_with_same_content_completes_the_import(self):
        pom = self.root / self.jpf.pom
        pom.parent.mkdir(parents=True)
        pom.write_bytes(b"<project/>")
        tool.write_artifact(self.root, self.jpf, b"jar bytes", b"<project/>")
        self.assertEqual(b"jar bytes", (self.root / self.jpf.jar).read_bytes())
        self.assertEqual(b"<project/>", pom.read_bytes())
        self.assertEqual(hashlib.sha1(b"jar bytes").hexdigest() + "\n",
                         (self.root / self.jpf.directory / "jpf-1.5.1.jar.sha1").read_text(encoding="ascii"))
        self.assertEqual(hashlib.sha1(b"<project/>").hexdigest() + "\n",
                         (self.root / self.jpf.directory / "jpf-1.5.1.pom.sha1").read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
