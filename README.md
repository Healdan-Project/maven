# Healdan's Maven Repository

Copies of the Maven artifacts [Healdan](https://github.com/Healdan-Project/healdan)'s build needs that only
LogicalDOC's Maven repository (`https://logicaldoc.sourceforge.net/maven/`) has. GitHub Pages serves them at
https://maven.healdan.com/, and Healdan's `docker/maven-settings.xml` mirrors LogicalDOC's repository (id
`logicaldoc`) to it, so Healdan's builds never contact LogicalDOC. The design is Healdan's
[`docs/superpowers/specs/2026-10-29-healdan-maven-repository-design.md`](https://github.com/Healdan-Project/healdan/blob/master/docs/superpowers/specs/2026-10-29-healdan-maven-repository-design.md).

Each artifact keeps its own licence, listed below. Of the 15 artifacts, Healdan's image already ships 8 as jars:
Smart GWT, jgravatar, Commons FileUpload, JPF and jpf-boot, and the three Jackrabbit jars. The other 7, the GUI's GWT
libraries (smartgwt-skins, gwt-dnd, gwt-incubator, gwt-links, tagcloud, gwtchismes and gwtexporter), reach it only
as the GWT compile's JavaScript and resources.

## Importing an Artifact

Files only get in through `import-artifact.py` (Python 3, standard library only), so this repository's history says
where each one came from. A hosted version never changes.

First check that the artifact's licence allows hosting it publicly. One that doesn't stays out: Healdan drops it from
its build instead, and it goes in Not Hosted below. Then:

```bash
python3 import-artifact.py <group>:<artifact>:<version>[:<classifier>] --project '<name and link>' --licence <SPDX id>
```

That fetches the jar and POM from LogicalDOC's repository, checks each against the `.sha1` published beside it,
writes them with their `.sha1`s, and adds the artifact's row below. If LogicalDOC's repository refuses or has gone,
import a jar taken from a LogicalDOC CE release bundle instead, with `--file <jar> --source '<where it came from>'`.
It gets a stub POM. A classifier jar for an artifact that's already hosted, such as a `-sources.jar`, keeps the
artifact's POM instead.

The script refuses group `com.logicaldoc`. Those are Healdan's own modules, which Healdan builds: a build that can't
find one has a Healdan module left behind on an old version, which needs bumping to the root POM's version.

Commit on a branch, open a pull request to `main`, and merge it once Check passes. Once
`python3 import-artifact.py --verify https://maven.healdan.com/` passes, Pages has published it.

## Checks

The Check workflow runs on every push to `main` and every pull request. It runs `import-artifact.py`'s tests and
`--verify`, and fails when a push or pull request modifies, deletes or renames a jar, POM or `.sha1` that's already
hosted, or a push rewrites `main`'s history. Each day, and when run by hand, it also runs
`--verify https://maven.healdan.com/`, which fetches every hosted file from Pages. GitHub stops a public
repository's scheduled runs after 60 days without a commit; the Actions tab turns them back on.

A ruleset on `main`, with no bypass, refuses deleting it or force-pushing to it, and takes changes only through a
pull request whose Check has passed.

## Artifacts

<!-- artifacts -->
| Coordinates | Project | Licence | Source |
|---|---|---|---|
| `com.allen_sauer.gwt.dnd:gwt-dnd:3.0.1` | [gwt-dnd](https://github.com/fredsa/gwt-dnd) | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `com.google.gwt:gwt-incubator:2.1.0` | [GWT Incubator](https://code.google.com/archive/p/google-web-toolkit-incubator/) | Apache-2.0, bundling JavaSWF (BSD-3-Clause) and W3C's CSS parser (W3C-19980720) | logicaldoc.sourceforge.net, 2026-10-29 |
| `com.orange.links:gwt-links:1.4.2` | [gwt-links](https://code.google.com/archive/p/gwt-links/) | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `com.smartgwt:smartgwt-skins:14.1p` | [Smart GWT LGPL Edition](https://smartclient.com/product/) | LGPL-3.0-only | logicaldoc.sourceforge.net, 2026-10-29 |
| `com.smartgwt:smartgwt:14.1p` | [Smart GWT LGPL Edition](https://smartclient.com/product/) | LGPL-3.0-only | logicaldoc.sourceforge.net, 2026-10-29 |
| `com.timgroup:jgravatar:1.2.ld` | [jgravatar](https://github.com/tim-group/jgravatar) | BSD-3-Clause OR LGPL-3.0-only, bundling Guava (Apache-2.0) | logicaldoc.sourceforge.net, 2026-10-29 |
| `commons-fileupload:commons-fileupload:1.6.0-jakarta` | [Apache Commons FileUpload](https://commons.apache.org/proper/commons-fileupload/), LogicalDOC's Jakarta build | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `gdurelle.tagcloud:tagcloud:0.4` | [gwt-tagcloud](https://github.com/gdurelle/gwt-tagcloud) | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `gwtchismes:gwtchismes:0.9.8` | [GWTChismes](https://code.google.com/archive/p/gwtchismes/) | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `net.sf.jpf:jpf-boot:1.5.1` | [Java Plug-in Framework](https://jpf.sourceforge.net/) | LGPL-2.1-or-later, bundling SplashWindow (public domain) | logicaldoc.sourceforge.net, 2026-10-29 |
| `net.sf.jpf:jpf-boot:1.5.1:sources` | [Java Plug-in Framework](https://jpf.sourceforge.net/), its source | LGPL-2.1-or-later, bundling SplashWindow (public domain) | `source-boot/` and build files of JPF's `jpf-src-1.5.1.zip` (sourceforge.net/projects/jpf), 2026-10-29 |
| `net.sf.jpf:jpf:1.5.1` | [Java Plug-in Framework](https://jpf.sourceforge.net/) | LGPL-2.1-or-later | logicaldoc.sourceforge.net, 2026-10-29 |
| `net.sf.jpf:jpf:1.5.1:sources` | [Java Plug-in Framework](https://jpf.sourceforge.net/), its source | LGPL-2.1-or-later | `source/` and build files of JPF's `jpf-src-1.5.1.zip` (sourceforge.net/projects/jpf), 2026-10-29 |
| `org.apache.jackrabbit:jackrabbit-jcr-commons:2.22.0-jakarta` | [Apache Jackrabbit](https://jackrabbit.apache.org/), LogicalDOC's Jakarta build | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `org.apache.jackrabbit:jackrabbit-jcr-server:2.22.0-jakarta` | [Apache Jackrabbit](https://jackrabbit.apache.org/), LogicalDOC's Jakarta build | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `org.apache.jackrabbit:jackrabbit-webdav:2.22.0-jakarta` | [Apache Jackrabbit](https://jackrabbit.apache.org/), LogicalDOC's Jakarta build | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
| `org.timepedia.exporter:gwtexporter:2.0.10` | [gwt-exporter](https://github.com/manolo/gwt-exporter) | Apache-2.0 | logicaldoc.sourceforge.net, 2026-10-29 |
<!-- /artifacts -->

## Licences

Each artifact's licence is in the table above. `LICENSES/` holds the texts and notices the jars don't carry
themselves, or carry where they're easy to miss: `Apache-2.0.txt`; `LGPL-2.1.txt`; `LGPL-3.0.txt` with `GPL-3.0.txt`,
which it builds on; jgravatar's `BSD-3-Clause-jgravatar.txt`; JavaSWF's `BSD-3-Clause-JavaSWF.txt`, copied unchanged
from the root of gwt-incubator's jar (`JavaSWF-License.txt`); and the NOTICE files of Apache Commons FileUpload,
Jackrabbit JCR Commons and Jackrabbit JCR Server, the last taken from Apache's `jackrabbit-jcr-server-2.22.0.jar` on
Maven Central, because LogicalDOC's build of it has none.

- `commons-fileupload:commons-fileupload:1.6.0-jakarta` and the three `org.apache.jackrabbit` `2.22.0-jakarta` jars
  are LogicalDOC's modified builds of Apache's, rebuilt for Jakarta Servlet. FileUpload's portlet package is gone.
- JPF's jars contain no source, so each has a `-sources.jar` beside it. JPF's own 1.5.1 release
  ([SourceForge](https://sourceforge.net/projects/jpf/files/jpf-1.5/jpf-1.5.1/)) has the same two jars, byte for
  byte, in `jpf-bin-1.5.1.zip`. Each `-sources.jar` holds the matching tree of its `jpf-src-1.5.1.zip` (SHA-1
  `51112f4233c379daf291a646d8100e751cb8c0d0`), `source/` or `source-boot/`, with the zip's build, readme and licence
  files, every entry unchanged. Every class in each jar was compiled from a `.java` in its tree, and every resource is
  identical. The zip's `lib/` jars (Commons Logging, and JXP for JPF's documentation tool) are left out: JPF's jars
  don't contain them.
- JPF's source files license it under LGPL version 2.1 "or (at your option) any later version". The one exception,
  jpf-boot's `SplashWindow`, is Werner Randelshofer's, and its header puts it in the public domain.
- jgravatar's README offers it under the BSD licence or LGPL version 3, without "or any later version". Its POM names
  MIT and LGPL instead. Healdan relies on the README.
- Smart GWT's Java sources and Isomorphic's
  [licensing FAQ](https://smartclient.com/product/licensingFAQ.jsp) put its LGPL edition under LGPL version 3, without
  "or any later version". Some of its debug and tool JavaScript files carry Isomorphic's proprietary boilerplate.
  Healdan relies on the LGPL statement.

## Not Hosted

| Coordinates | Licence | Why |
|---|---|---|
| `javax.media:jai-core:1.1.3`, `com.sun.media:jai-codec:1.1.3` | Sun Microsystems, Inc. Binary Code License Agreement | Its POM says distribution is `manual`, and Maven Central carries its POM but not its jar. Nothing in Healdan's build references its classes, so Healdan's `logicaldoc-core` drops it. |
| `betelio:betelio:1.0` | None stated | No licence and no confirmed author. Nothing in Healdan's build uses it, so Healdan drops it. |
| `com.google.code.ksoap2-android:ksoap2-android-assembly:3.3.0:jar-with-dependencies` | MIT, with bundled kObjects code that's partly GPLv2 and partly unlicensed | Its only user was LogicalDOC's SOAP client module, `logicaldoc-webserviceclient`, which Healdan leaves out of its build. |
| `com.oracle.jdbc:ojdbc8:12.2.0.1` | Oracle's OTN licence, which doesn't allow free redistribution; the jar states none | Healdan supports only open-source databases, so it drops Oracle's driver. |
