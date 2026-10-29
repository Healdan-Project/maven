# Healdan's Maven Repository

Copies of the Maven artifacts [Healdan](https://github.com/Healdan-Project/healdan)'s build needs that only
LogicalDOC's Maven repository (`https://logicaldoc.sourceforge.net/maven/`) has. GitHub Pages serves them at
https://maven.healdan.com/, and Healdan's `docker/maven-settings.xml` mirrors LogicalDOC's repository (id
`logicaldoc`) to it, so Healdan's builds never contact LogicalDOC. The design is Healdan's
[`docs/superpowers/specs/2026-10-29-healdan-maven-repository-design.md`](https://github.com/Healdan-Project/healdan/blob/master/docs/superpowers/specs/2026-10-29-healdan-maven-repository-design.md).

Each artifact keeps its own licence, listed below. Healdan's image already ships these jars as part of the program.

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
It gets a stub POM.

Push, and once `python3 import-artifact.py --verify https://maven.healdan.com/` passes, Pages has published it.

## Artifacts

<!-- artifacts -->
| Coordinates | Project | Licence | Source |
|---|---|---|---|
<!-- /artifacts -->

## Licences

Each artifact's licence is in the table above. `LICENSES/` holds the texts and notices the jars themselves lack:
`Apache-2.0.txt`; `LGPL-2.1.txt`; `LGPL-3.0.txt` with `GPL-3.0.txt`, which it builds on; `BSD-3-Clause-jgravatar.txt`;
and the NOTICE files of Apache Commons FileUpload and Apache Jackrabbit.

- `commons-fileupload:commons-fileupload:1.6.0-jakarta` and the three `org.apache.jackrabbit` `2.22.0-jakarta` jars
  are LogicalDOC's modified builds of Apache's, rebuilt for Jakarta Servlet. FileUpload's portlet package is gone.
- JPF's jars contain no source. Its source is at https://jpf.sourceforge.net/.
- Smart GWT's Java sources and Isomorphic's
  [licensing FAQ](https://smartclient.com/product/licensingFAQ.jsp) put its LGPL edition under LGPL-3.0. Some of its
  debug and tool JavaScript files carry Isomorphic's proprietary boilerplate. Healdan relies on the LGPL statement.

## Not Hosted

| Coordinates | Licence | Why |
|---|---|---|
| `javax.media:jai-core:1.1.3`, `com.sun.media:jai-codec:1.1.3` | Sun Microsystems, Inc. Binary Code License Agreement | Its POM says distribution is `manual`, and Maven Central carries its POM but not its jar. Nothing in Healdan's build references its classes, so Healdan's `logicaldoc-core` drops it. |
| `betelio:betelio:1.0` | None stated | No licence and no confirmed author. Nothing in Healdan's build uses it, so Healdan drops it. |
| `com.google.code.ksoap2-android:ksoap2-android-assembly:3.3.0` | MIT, with bundled kObjects code that's partly GPLv2 and partly unlicensed | Its only user was LogicalDOC's SOAP client module, `logicaldoc-webserviceclient`, which Healdan leaves out of its build. |
