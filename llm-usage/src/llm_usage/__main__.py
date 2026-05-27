"""Module entry point so `python -m llm_usage` and the console script both work."""

from llm_usage.cli import cli


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
