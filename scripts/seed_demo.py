from __future__ import annotations

import json

from app.demo.seed import seed_demo_dataset


def main() -> None:
    print(json.dumps(seed_demo_dataset(), indent=2))


if __name__ == "__main__":
    main()
