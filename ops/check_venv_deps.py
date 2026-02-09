import sys
from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path

from packaging.requirements import Requirement


REQUIREMENTS_FILES = [
    Path(__file__).parent.parent / "requirements.txt",
    Path(__file__).parent.parent / "src/requirements.txt",
]


def test_requirements() -> None:
    missing_requirements = []
    for requirement_file in REQUIREMENTS_FILES:
        for line in requirement_file.read_text().splitlines():
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            try:
                req = Requirement(line)
                # Check if the distribution is installed
                distribution(req.name)
            except PackageNotFoundError:
                missing_requirements.append(line)

    if missing_requirements:
        print(f"Missing requirements! {missing_requirements}")
        sys.exit(1)


if __name__ == "__main__":
    test_requirements()
