# Task Processor v2.0.0-alpha

This is an ALPHA prerelease of version 2.0.0.

## Overview

This is the newest version numerically, but it's a prerelease!

With default settings (`include_prerelease=False`):
- `version="latest"` returns v1.1.0 (latest STABLE)
- This version (v2.0.0-alpha) is ignored

With `include_prerelease=True`:
- `version="latest"` still returns v1.1.0 (releases > prereleases of higher version)
- Unless only prereleases exist for the highest version

You can always request this version explicitly:
- `version="v2.0.0-alpha"` returns this file


