[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/romdhoncom/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/romdhoncom/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

# The Passport Page of a Country That Isn't There

`main.py` (Python 3.13, pure standard library + PIL) draws one invented
passport spread and writes it to `/output/entry.png` (1024×724 PNG,
about 160 KB). It uses no network, no clock and no randomness: two runs
produce byte-identical output.

## The country

The **Republic of Kavora** is a small South Atlantic island nation —
fishing, salt, one ferry port, and **no airport**: every arrival and
departure is by sea. Its capital is Port Anselm. The passport is
bilingual, English and Portuguese, as a South Atlantic island's would be.

## The holder

**Elias Varela**, fisherman of the Kavora fishing fleet, born 17 September
1981 in Port Anselm. Passport KV 847 291, issued 14 March 2023 in Port
Anselm, valid until 13 March 2033. His portrait is drawn in code: a
weathered fisherman in a knitted cap, grey-streaked beard, navy sweater.

## The travel history

One trip, told by the stamps on the facing page — every date after the
passport's issue date:

- 28 May 2023 — visitor visa for South Africa issued in Cape Town
  (single entry, 90 days, fishing industry conference)
- 02 Jun 2023 — departed Port Anselm, Kavora
- 05 Jun 2023 — arrived Cape Town, South Africa
- 19 Jun 2023 — departed Cape Town
- 22 Jun 2023 — arrived Port Anselm, **by ferry MV Sea Star**;
  harbour fee of 40 kavori paid the same day

The telling detail is the red notice on the visa page: *Kavora has no
airport. All arrivals and departures by sea — ferry terminal, Port
Anselm.*

The machine-readable zone at the foot of the data page carries correct
MRZ check digits (document number, birth date, expiry date, personal
number and the composite check).

## Run it

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py
```
