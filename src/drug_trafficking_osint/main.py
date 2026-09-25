"""Command-line entry point for validating the deployable foundation."""

from drug_trafficking_osint.core.container import build_container


def main() -> int:
    """Compose, start, and gracefully stop the foundation process."""
    container = build_container()
    container.runtime.start()
    container.runtime.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
