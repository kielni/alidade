Do not pass code as string on the command line — this includes `python -c "..."` and
any shell one-liner that embeds Python.  When writing Python code to explore or test
something, append it as a function to claude.py and run `uv run python claude.py`.
Include a comment about the purpose of the code.

When writing Python code

  - Always use PEP-8 style.
  - Do not use inline imports.
  - Always run `make lint` after editing code, not black on individual files.
  - Always break string literals that exceed 88 characters using implicit string
    concatenation, since black does not split string literals.

Do not add manual `black` or formatting calls to build-related code; run `make lint`.

Example projects in this repo live under `projects/<name>/`. Conventions for
writing any alidade project, including these, are in the shipped project guide:

@alidade/PROJECT_GUIDE.md
