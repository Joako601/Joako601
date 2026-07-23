name: Update Collaborators

on:
  schedule:
    - cron: "0 6 * * 1"   # todos los lunes 6am UTC
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  update-collaborators:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run collaborators script
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_USERNAME: Joako601
        run: python .github/scripts/gen_collaborators.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md assets/avatar-*.svg
          git diff --cached --quiet || git commit -m "chore: actualizar colaboradores automáticamente"
          git push
