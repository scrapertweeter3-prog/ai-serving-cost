# Ai-serving-cost - serving cost math for AI workloads

A terminal calculator that restates what an AI API bill should be:
input tokens at a per-million rate with the cache discount applied,
output tokens at theirs, a per-request fee on top, and the whole thing
multiplied out to a monthly number at your request volume. It also
prints what the cached share of input traffic is worth in dollars.

Python 3.8+, standard library only. No install, no network, nothing
leaves your machine.

## The method

- **Per-token cost** = tokens / 1,000,000 x rate. A 3-dollar input rate
  is 0.3 cents per thousand tokens, and the tool keeps the units honest so a
  quote in per-million dollars and a log in raw tokens meet correctly.
- **Request cost** = input cost after the cache discount + output cost
  + per-request fee. A 30% cached share bills 70% of input tokens at
  the full rate; the cache never touches the output side.
- **Cache savings** = full-rate input cost x cached share, floored at a
  share of 0..1 so a bad telemetry number cannot produce negative cost.
- **Monthly bill** = request cost x requests/day x 30.

## Usage

```
$ python3 aiservingcost.py --in-tokens 10000 --out-tokens 500 \
    --in-rate 3 --out-rate 15 --cache-share 0.3 --req-day 20000
Input tokens/request             10,000
Output tokens/request               500
Cached share                         30%
Cost/request                  $0.029000
Requests/day                    20,000
Monthly bill                 $17,400.00
Monthly input-cache savings   $5,400.00
```

Compare two cache shares head to head:

```
$ python3 aiservingcost.py --compare 0.3 0.6
cache share 30% -> $0.029000/request
cache share 60% -> $0.020000/request
60% wins, saves $0.009000/request
```

`--json` for machine output.

## Honest limits

The tool treats rates as flat inputs and does not model tiered pricing,
batch windows, or the tax that context re-sends pay when a prompt cache
misses. It also assumes the provider's own audit matches yours; the
price-audit habit of checking a bill against a teardown of your own
token counts is where this fits.

## Related

Where the serving math comes from, audited against a real bill:
https://pastagi.com/tools/gpt-6-astra-pricing-audit/
Cache economics and what a hit is actually worth:
https://pastagi.com/guides/llm-prompt-caching-guide/
The decode side of the same bill:
https://pastagi.com/engineering/kv-cache-decode-cost/
More AI engineering math: https://pastagi.com/

## License

MIT
