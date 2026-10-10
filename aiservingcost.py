#!/usr/bin/env python3
"""aiservingcost.py - serving cost math for AI workloads: per-token cost
with cache discounts, request cost from token counts, and the cache
savings at a given volume. Python mirror of the Rust crate, stdlib only.

Exit code 1 when the compared request costs tie (comparison needs a gap);
exit 0 always otherwise (informational tool).
"""

import argparse
import json
import sys


def token_cost(tokens, rate_per_million):
    return tokens / 1_000_000.0 * rate_per_million


def request_cost(input_tokens, output_tokens, input_rate, output_rate,
                 cache_share, per_request):
    share = max(0.0, min(1.0, cache_share))
    return (token_cost(input_tokens, input_rate) * (1.0 - share)
            + token_cost(output_tokens, output_rate) + per_request)


def cache_savings(tokens, input_rate, cache_share):
    share = max(0.0, min(1.0, cache_share))
    return token_cost(tokens, input_rate) * share


def monthly_bill(cost_per_request, requests_per_day):
    return cost_per_request * requests_per_day * 30.0


def _nonneg(text):
    try:
        val = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}")
    if val < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {val}")
    return val


def main():
    p = argparse.ArgumentParser(
        description="Serving cost math for AI workloads.")
    p.add_argument("--in-tokens", type=_nonneg, default=10_000.0,
                   help="input tokens per request")
    p.add_argument("--out-tokens", type=_nonneg, default=500.0,
                   help="output tokens per request")
    p.add_argument("--in-rate", type=_nonneg, default=3.0,
                   help="input dollars per million tokens")
    p.add_argument("--out-rate", type=_nonneg, default=15.0,
                   help="output dollars per million tokens")
    p.add_argument("--cache-share", type=_nonneg, default=0.3,
                   help="cached share of input traffic, 0..1")
    p.add_argument("--per-request", type=_nonneg, default=0.0005,
                   help="per-request fee in dollars")
    p.add_argument("--req-day", type=_nonneg, default=20_000.0,
                   help="requests per day")
    p.add_argument("--compare", nargs=2, type=_nonneg,
                   metavar=("SHARE_A", "SHARE_B"),
                   help="request cost at two cache shares")
    p.add_argument("--json", action="store_true", help="machine output")
    a = p.parse_args()

    if a.compare:
        share_a, share_b = a.compare
        ca = request_cost(a.in_tokens, a.out_tokens, a.in_rate, a.out_rate,
                          share_a, a.per_request)
        cb = request_cost(a.in_tokens, a.out_tokens, a.in_rate, a.out_rate,
                          share_b, a.per_request)
        if abs(ca - cb) < 1e-12:
            print("tie: the two cache shares cost the same")
            return 1
        winner = share_a if ca < cb else share_b
        print(f"cache share {share_a:.0%} -> ${ca:.6f}/request")
        print(f"cache share {share_b:.0%} -> ${cb:.6f}/request")
        print(f"{winner:.0%} wins, saves ${abs(ca - cb):.6f}/request")
        return 0

    req = request_cost(a.in_tokens, a.out_tokens, a.in_rate, a.out_rate,
                       a.cache_share, a.per_request)
    mo = monthly_bill(req, a.req_day)
    sv = cache_savings(a.in_tokens * a.req_day * 30.0, a.in_rate,
                       a.cache_share)
    lines = [
        ("Input tokens/request", f"{a.in_tokens:,.0f}"),
        ("Output tokens/request", f"{a.out_tokens:,.0f}"),
        ("Cached share", f"{a.cache_share:.0%}"),
        ("Cost/request", f"${req:.6f}"),
        ("Requests/day", f"{a.req_day:,.0f}"),
        ("Monthly bill", f"${mo:,.2f}"),
        ("Monthly input-cache savings", f"${sv:,.2f}"),
    ]
    if a.json:
        print(json.dumps(dict(lines)))
    else:
        width = max(len(k) for k, _ in lines)
        for k, v in lines:
            print(f"{k:<{width}}  {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
