"""Job 5: pull MX records and split domains by mail provider (free public DNS)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gtm.gate import read_csv, require, run_gated
from gtm.cli import parser

def classify_mx(hosts):
    h = " ".join(hosts).lower()
    if not hosts or hosts == ["."]:
        return "no_mail"
    if "google.com" in h or "googlemail.com" in h:
        return "google"
    if "outlook.com" in h or "protection.outlook" in h:
        return "microsoft"
    return "other"

def offline_resolver(domain):
    """Deterministic fixture so tests and demos need no network."""
    n = sum(map(ord, domain)) % 3
    return [["aspmx.l.google.com"], ["example-com.mail.protection.outlook.com"], ["mx1.mailhost.example.net"]][n]

def live_resolver(domain):
    import dns.resolver
    try:
        ans = dns.resolver.resolve(domain, "MX", lifetime=5)
        return [str(r.exchange).rstrip(".") or "." for r in sorted(ans, key=lambda r: r.preference)]
    except Exception:
        return []

def make_process(resolver):
    def process(rows):
        out = []
        for r in rows:
            hosts = resolver(r["domain"])
            out.append({**r, "mx_hosts": "|".join(hosts), "mail_provider": classify_mx(hosts)})
        return out
    return process

if __name__ == "__main__":
    p = parser(__doc__)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--offline", action="store_true", help="use fixture resolver (default)")
    g.add_argument("--live", action="store_true", help="query public DNS")
    a = p.parse_args()
    rows = read_csv(a.input)
    require(rows, ["domain"])
    run_gated("05-mx-provider-split", rows, make_process(live_resolver if a.live else offline_resolver), a.approve, a.out,
              lambda full: {k: sum(r["mail_provider"] == k for r in full) for k in ("google", "microsoft", "other", "no_mail")})
