# Contributing

This project follows the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

All commits must be signed off with:

```
git commit -s -m "your message"
```

This adds a `Signed-off-by` trailer confirming your contributions comply
with the Apache License 2.0 and DCO terms.

## Code Style

- Use descriptive variable and function names (no `temp1`, `x2`, etc.)
- Add docstrings to all public functions and classes
- Keep functions focused and under ~60 lines
- No hardcoded secrets — use environment variables

## Running Tests

```bash
pytest tests/ -v
```
