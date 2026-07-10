# Third-Party Notices

This repository is MIT-licensed for its original code and documentation. That
license does **not** relicense third-party issue text, upstream source code, or
other material linked from the evaluation fixtures.

## Public GitHub issue material

`evals/tasks/*.json`, `evals/candidates.json`, and a few historical experiment
packets contain titles, excerpts, reproduction details, and URLs from public
GitHub issues. Exact issue text is retained only where it formed the prompt input
for a historical evaluation; public narrative documents otherwise paraphrase it.
Copyright and attribution for that text remain with the original authors. The
canonical issue pages are:

- `kellyjonbrazil/jc`: [#685](https://github.com/kellyjonbrazil/jc/issues/685),
  [#687](https://github.com/kellyjonbrazil/jc/issues/687), and
  [#694](https://github.com/kellyjonbrazil/jc/issues/694)
- `pallets/click`: [#2994](https://github.com/pallets/click/issues/2994)
- `tqdm/tqdm`: [#1701](https://github.com/tqdm/tqdm/issues/1701)
- `jd/tenacity`: [#420](https://github.com/jd/tenacity/issues/420),
  [#544](https://github.com/jd/tenacity/issues/544),
  [#554](https://github.com/jd/tenacity/issues/554), and
  [#613](https://github.com/jd/tenacity/issues/613)
- `date-fns/date-fns`: [#4129](https://github.com/date-fns/date-fns/issues/4129)
  and [#4148](https://github.com/date-fns/date-fns/issues/4148)
- `colinhacks/zod`: [#5273](https://github.com/colinhacks/zod/issues/5273),
  [#5296](https://github.com/colinhacks/zod/issues/5296),
  [#5824](https://github.com/colinhacks/zod/issues/5824),
  [#5937](https://github.com/colinhacks/zod/issues/5937), and
  [#5944](https://github.com/colinhacks/zod/issues/5944)
- `yargs/yargs`: [#2497](https://github.com/yargs/yargs/issues/2497)
- `sindresorhus/execa`: [#1193](https://github.com/sindresorhus/execa/issues/1193)

Some issue bodies link to additional public discussions, source lines, or pull
requests. Those links remain attribution pointers to the original pages; their
contents are not covered by this repository's MIT license.

## Upstream repositories

The evaluation runner can clone upstream repositories at recorded revisions. Their
source code is not vendored into this repository and remains governed by each
upstream project's license. Task records point to an issue and a later fix only as
ground-truth metadata; inclusion does not imply endorsement by the issue author or
upstream maintainer.

## Privacy boundary

Public fixtures use public issue material and generic work-directory placeholders.
Private application names, service/account details, screenshots, credentials,
tokens, cookies, raw private records, and machine-specific personal paths are not
part of the intended public package. Historical notes have been paraphrased where
those details were unnecessary to understand the mechanism.
