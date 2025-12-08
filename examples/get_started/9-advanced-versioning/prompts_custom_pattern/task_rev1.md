# Task Processor Revision 1

This file uses a custom versioning pattern: `_rev1`

## Overview

Custom patterns allow non-standard versioning schemes:
- `_rev1`, `_rev2`, `_rev42`
- `_build123`
- Or any regex with named capture groups

Pattern used: `r"_rev(?P<major>\d+)"`
