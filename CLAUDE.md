Do not pass code as string on the command line.  When writing code, append it as a function to claude.py. Include a comment about the purpose of the code.

When writing Python code

  - Always use PEP-8 style.
  - Do not use inline imports.
  - Always run `make lint` after editing code, not black on individual files.
  - Always break string literals that exceed 88 characters using implicit string
    concatenation, since black does not split string literals.

After adding, removing, or restyling a layer (any edit to a `layers/*.py`
file inside a project directory), update that project's `workflow.md` in the
same session. Do not wait for the user to ask.
