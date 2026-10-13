# ai-serving-cost

A one-file terminal calculator for what an AI API request costs: input
tokens at a per-million rate with the cache discount applied, output
tokens at theirs, a per-request fee on top, then the whole thing
multiplied out to a monthly number at your request volume. It also
prints what the cached share of input traffic is worth in dollars, and
it prices two cache shares against each other.

ai-serving-cost is built and maintained by [Pastagi](https://pastagi.com),
a site that prices AI serving the same way, from per-token math and
real bill audits.

## Install

Python 3.8+, standard library only. No install step, no network,
nothing leaves your machine:

    curl -O https://raw.githubusercontent.com/scrapertweeter3-prog/ai-serving-cost/main/aiservingcost.py

## Usage

    $ python3 aiservingcost.py --in-tokens 32000 --out-tokens 1200 \
        --in-rate 2.5 --out-rate 10 --cache-share 0.55 --per-request 0 \
        --req-day 6000
Input tokens/request         32,000
Output tokens/request        1,200
Cached share                 55%
Cost/request                 $0.048000
Requests/day                 6,000
Monthly bill                 $8,640.00
Monthly input-cache savings  $7,920.00

The printout answers the question in order: what one request bills at
your rates, what that turns into over a month of traffic, and how much
the cache is giving back at the current hit share.

## Comparing cache shares

Pass two shares and the tool prices both from the same traffic mix:

    $ python3 aiservingcost.py --compare 0.3 0.6 --in-rate 3 --out-rate 15
cache share 30% -> $0.029000/request
cache share 60% -> $0.020000/request
60% wins, saves $0.009000/request

## Options

    --in-tokens TOKENS   input tokens per request (default 10000)
    --out-tokens TOKENS  output tokens per request (default 500)
    --in-rate RATE       input dollars per million tokens (default 3)
    --out-rate RATE      output dollars per million tokens (default 15)
    --cache-share SHARE  cached fraction of input traffic, 0.3 = 30%
    --per-request FEE    fixed dollars per request (default 0.0005)
    --req-day N          requests per day (default 20000)
    --compare A B        price two cache shares against each other
    --json               machine-readable output

## Honest limits

The tool treats rates as flat inputs and does not model tiered pricing,
batch windows, or the penalty a context re-send pays when the prompt
cache misses. The README links a real bill audit for the full teardown
method behind these numbers.

## License

MIT
