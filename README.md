# config-diff

**What changed between the run that worked and the one that didn't? Compare experiment
configuration files (JSON, TOML, INI) by meaning, not by text, with dotted parameter paths.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Simulations and ML experiments are driven by configuration files. A plain `diff` is confused by
reordered keys, formatting and number representations (`1e-3` vs `0.001`), and cannot compare an INI
file with a JSON file. When results change, you need the list of *parameters* that changed, ideally
as a table for the lab notebook or the paper's supplementary material.

## Features

- Formats: JSON, TOML (Python 3.11+), INI/CFG (values coerced to numbers/booleans/null)
- Nested structures flattened to paths like `model.layers[2]` and `optimizer.lr`
- Change kinds: added, removed, changed, type changed (e.g. `"1"` vs `1`)
- Numeric tolerance (`--rel-tol 1e-9`) and ignore globs (`-i "paths.*"`)
- Text, Markdown table or JSON output; exit code 1 if configs differ

## Usage

```bash
pip install .
config-diff runs/42/config.json runs/57/config.json
config-diff baseline.toml new.ini -i "logging.*" --rel-tol 1e-9 -f markdown
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
