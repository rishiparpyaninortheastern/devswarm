import argparse
import logging
import time

from devswarm.shared.llm import LocalDraftProvider
from devswarm.shared.runtime import store


def tick() -> bool:
    return store().process_next(LocalDraftProvider())


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if args.once:
        tick()
        return
    while True:
        try:
            tick()
        except Exception:  # noqa: BLE001 - worker boundary must retry without leaking telemetry
            # Never log payloads or provider exceptions containing telemetry.
            logging.getLogger(__name__).error("Draft processing failed; pending work will retry")
        time.sleep(1)


if __name__ == "__main__":
    main()
