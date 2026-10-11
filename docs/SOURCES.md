# Sources and assumptions

## Downtime cost: $38,000 per minute
- Siemens, *The True Cost of Downtime 2024* (Siemens, June 2024): "An hour's downtime in a large Automotive plant now costs $2.3 million an hour, or more than $600 a second." Report: https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf (checked in the PDF, p. 2-5)
- $2.3M / 60 = about $38,300 per minute. The report gives hourly and per-second figures, so the per-minute number is our division. We use $38,000.
- Applies to a **large** plant. A single line is smaller; call it "industry figure for a large automotive plant" on the slide.
- Older figure in the original brief, about $22,000 per minute: a 2006 survey of 101 automotive executives by Advanced Technology Services / Nielsen. Outdated, so we do not use it. Siemens also says an automotive hour of downtime cost more than $1.3M in 2019 to 2020, which is the same era.
- Configurable in `data/plantdata/outputs.py` (`DOWNTIME_COST_PER_MIN_USD`).

## Estimated, not measured
Everything in `data/out/history/maintenance_*.csv`, `downtime_events.csv` and `failure_modes.csv` is an estimate built from typical industrial ranges (MTBF, repair times, part prices, $65/h labour). Fine for a fictional plant, but never present it as real plant data.
