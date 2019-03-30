# Repology link checker

[![Build Status](https://travis-ci.org/repology/repology-linkchecker.svg?branch=master)](https://travis-ci.org/repology/repology-linkchecker)

This is a standalone link validity checker daemon for Repology project.

It operates on `links` table in Repology PostgreSQL database, which
contains homepage and download URLs of F/OSS projects extracted from
packages by Repology, taking URLs from there, checking their validity
and accessibility via both IPv4 and IPv6 and writes the status back.

## Features

- `asyncio` based, which means it doesn't require a lot of resources,
  but still can process a lot of links in parallel
- it takes most care to not generate excess load on servers by maintaining
  per-host queues and adding delays between consequential requests to
  a single host
- (TODO) checks link availability via both IPv4 and IPv6
- (TODO) capable of FTP link checking

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
