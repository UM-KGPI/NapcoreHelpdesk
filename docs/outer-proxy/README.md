# Error page on the kgpi.fgpa.um.si proxy

The NAPCORE Helpdesk is served at `https://kgpi.fgpa.um.si/napcore-helpdesk/` through the nginx on
kgpi.fgpa.um.si, which also serves the KGPI website. That nginx runs on the Helpdesk host, but it is
not managed from this repository (see "Installed on 6 November 2026" below).

When the Helpdesk host does not answer (overloaded, rebooting, or Docker restarting), this proxy
returns its default bare `502 Bad Gateway` page. This happened on 6 November 2026, 01:04–01:09 UTC.
The Helpdesk's own maintenance page cannot help in that case: it is served by the Helpdesk itself.
The three files here make the proxy show a short explanatory page instead.

| File | What it is |
|---|---|
| `napcore-helpdesk-errors.conf` | The nginx change: one `error_page` line and one named location |
| `unavailable.html` | Page for browsers; reloads itself every minute |
| `unavailable.json` | Reply to the web app's API calls, so it can show a message instead of failing to parse HTML |

## What it changes, and what it does not

- Only the errors the proxy produces itself are replaced: **502** (it cannot connect to the Helpdesk)
  and **504** (the Helpdesk did not answer in time).
- The status code stays 502/504. Browsers, caches, monitoring and the Helpdesk's own status
  banner still see a failure, not a 200.
- Everything the Helpdesk sends itself passes through unchanged, including its own 503 maintenance
  page during deploys and any 4xx/5xx from the application. `proxy_intercept_errors` stays off.
- Nothing changes for the KGPI website or any other location.

## Installing

On the proxy host, as root:

```bash
mkdir -p /var/www/napcore-helpdesk-errors
cp unavailable.html unavailable.json /var/www/napcore-helpdesk-errors/
chmod 644 /var/www/napcore-helpdesk-errors/*
```

In the `server { }` block for kgpi.fgpa.um.si:

1. In the existing `location /napcore-helpdesk/ { ... }`, add one line:
   `error_page 502 504 @napcore_helpdesk_unavailable;`
2. Add the `location @napcore_helpdesk_unavailable { ... }` block from `napcore-helpdesk-errors.conf`
   next to it.

Then:

```bash
nginx -t && systemctl reload nginx
```

If the Helpdesk is proxied by a location with a different path, put the `error_page` line in that
location, and change `^/napcore-helpdesk/api/` in the named location to match.

## Checking it

While the Helpdesk is up, nothing changes:
`curl -sI https://kgpi.fgpa.um.si/napcore-helpdesk/` still returns 200.

To see the page without stopping the Helpdesk, temporarily point a test location at a closed port.
Alternatively, wait for the next Helpdesk deploy: the restart window is about 30 s, and the
Helpdesk's own maintenance page covers most of it.

## Timeout

The Helpdesk's own nginx and gunicorn allow 120 s. Before 6 November 2026 the proxy had no
`proxy_read_timeout` for this location, so nginx's 60 s default applied. That explains the 504s
at exactly 60 s seen in October: slow answers were cut off at the proxy, although the Helpdesk
would have finished them. The location now sets `proxy_read_timeout 120s;`, which matches.

## Installed on 6 November 2026

- nginx 1.30.6 under systemd, on the Helpdesk host itself. Config file:
  `/etc/nginx/sites-enabled/kgpi.fgpa.um.si.conf`.
- Upstreams: the Helpdesk is at `127.0.0.1:8080` (`location /napcore-helpdesk/`, 443 block), and
  WordPress at `127.0.0.1:8000` (`location /`). The port 80 block only redirects to https.
- Added in the `/napcore-helpdesk/` location: `proxy_read_timeout 120s;` and the `error_page`
  line. The named location was added next to it, verbatim from `napcore-helpdesk-errors.conf`.
- Error files are in `/var/www/napcore-helpdesk-errors/` (755/644). SELinux is permissive.
- Backup of the previous config: `/etc/nginx/kgpi.fgpa.um.si.conf.bak-2026-11-06` (outside
  `sites-enabled`, so nginx does not load it). Rollback: copy it back, `nginx -t`, reload.
- Checked on the server with temporary `__errortest` locations, since removed:
  - `/napcore-helpdesk/__errortest` → 502 text/html, with `Cache-Control: no-store` and `Retry-After: 60`.
  - `/napcore-helpdesk/api/__errortest` → 502, `UPSTREAM_UNAVAILABLE` JSON.
  - The Helpdesk and the KGPI site still return 200.
  - The 504 path was not triggered on the server. It uses the same `error_page` line, and it was
    tested locally (below).

Tested locally with nginx 1.27 against a closed upstream port (502), an upstream read timeout
(504), and an upstream answering 503 itself (passed through unchanged).
