import sys
from pathlib import Path

import pkg_resources

REQUIREMENTS_FILES = [
    Path(__file__).parent.parent / "requirements.txt",
    Path(__file__).parent.parent / "src/requirements.txt",
]


def test_requirements():
    missing_requirements = []
    for requirement_file in REQUIREMENTS_FILES:
        requirements = pkg_resources.parse_requirements(
            requirement_file.read_text()
        )
        for requirement in requirements:
            requirement = str(requirement)
            try:
                pkg_resources.require(requirement)
            except pkg_resources.DistributionNotFound:
                missing_requirements.append(requirement)

    if missing_requirements:
        print(f"Missing requirements! {missing_requirements}")
        sys.exit(1)


if __name__ == "__main__":
    test_requirements()
