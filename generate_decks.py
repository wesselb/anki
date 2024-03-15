import datetime
import hashlib
import logging
import sys
from pathlib import Path
from typing import Literal, Optional

import click
import genanki


def str_hash(x: str) -> int:
    """Generate a hash for a string."""
    return int(hashlib.md5(x.encode()).hexdigest(), 16) % (1 << 32)


def generate_deck_id(lesson_num: str, section_num: str) -> int:
    """Generate a deck ID."""
    return str_hash(f"{lesson_num}::{section_num}")


def generate_note_id(lesson_num: str, section_num: str, note_num: str) -> str:
    """Generate a note ID."""
    return genanki.guid_for(lesson_num, section_num, note_num)


def load_path(
    path: Path,
) -> tuple[tuple[str, str], dict[tuple[str, str], list[tuple[str, str, str]]]]:
    """Load all files in a folder."""

    sections: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    section_name = None

    lesson_name = None
    lesson_num = None

    with open(path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Ignore empty lines. An empty line also ends any section.
        if not line:
            section_name = None
            continue

        # The first non-empty line is the lesson name.
        if lesson_num is None:
            lesson_num, lesson_name = line.split("|")
            lesson_num = lesson_num.strip().lower()
            lesson_name = lesson_name.strip()
            continue

        # Afterwards, every consecutive block of non-empty lines is a section.
        num_bars = sum(x == "|" for x in line)

        # One bar specifies a section name.
        if num_bars == 1:
            if section_name is not None:
                raise RuntimeError("Encountered double section name.")

            num, name = line.split("|")
            num = num.strip().lower()
            name = name.strip()

            section_name = (num, name)
            sections[section_name] = []

        # Two bars specify a note.
        elif num_bars == 2:
            if section_name is None:
                raise RuntimeError("Encountered section without name.")

            num, left, right = line.split("|")
            num = num.strip().lower()
            left = left.strip()
            right = right.strip()

            sections[section_name].append((num, left, right))

        # Anything else is not valid.
        else:
            raise RuntimeError(f"Line `{line}` contains {num_bars} bar(s).")

    if lesson_num is None or lesson_name is None:
        raise RuntimeError("Did not specify a lesson name.")

    return (lesson_num, lesson_name), sections


Way = Literal["both-ways", "left-to-right", "right-to-left"]
models: dict[Way, genanki.Model] = {
    "both-ways": genanki.Model(
        1760709464,
        "Question and Answer",
        fields=[
            {"name": "left"},
            {"name": "right"},
        ],
        templates=[
            {
                "name": "Left to Right",
                "qfmt": "{{left}}",
                "afmt": '{{left}}<hr id="answer">{{right}}',
            },
            {
                "name": "Right to Left",
                "qfmt": "{{right}}",
                "afmt": '{{right}}<hr id="answer">{{left}}',
            },
        ],
    ),
    "left-to-right": genanki.Model(
        1760709464 + 1,
        "Question and Answer",
        fields=[
            {"name": "left"},
            {"name": "right"},
        ],
        templates=[
            {
                "name": "Left to Right",
                "qfmt": "{{left}}",
                "afmt": '{{left}}<hr id="answer">{{right}}',
            },
        ],
    ),
    "right-to-left": genanki.Model(
        1760709464 + 2,
        "Question and Answer",
        fields=[
            {"name": "left"},
            {"name": "right"},
        ],
        templates=[
            {
                "name": "Right to Left",
                "qfmt": "{{right}}",
                "afmt": '{{right}}<hr id="answer">{{left}}',
            },
        ],
    ),
}


@click.command(help="Generate Anki decks.")
@click.option(
    "--path",
    "path_in",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    required=True,
    help="Path to directory with lesson files.",
)
@click.option(
    "--name",
    "header",
    type=str,
    required=False,
    help="Name of the deck. Defaults to the name of the folder specified by `--path`.",
)
@click.option(
    "--way",
    "way",
    default="both-ways",
    type=click.Choice(
        ["both-ways", "left-to-right", "right-to-left"],
        case_sensitive=False,
    ),
    help="How to question the cards.",
)
def main(path_in: Path, header: Optional[str], way: Way) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    header = header or path_in.stem.capitalize()

    # Determine the output directory.
    path_out = path_in / "output" / now
    path_out.mkdir(parents=True, exist_ok=True)

    # Generate the output name from the header.
    out_name = header.lower().replace(" ", "_") + ".apkg"

    # Create a logger for this deck.
    logger = logging.getLogger(header)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    # Write to standard output.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    # Also write to a file.
    file_handler = logging.FileHandler(path_out / "log.txt")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Load all lessons.
    lessons = dict(load_path(p) for p in sorted(path_in.glob("*.txt")))

    # Be sure to not duplicate decks or notes.
    seen_decks: set[int] = set()
    seen_notes: set[str] = set()

    # Generate a deck for every section in every lesson.
    decks = []
    for (lesson_num, lesson_name), sections in lessons.items():
        for (section_num, section_name), section in sections.items():
            deck_name = f"{header}::{lesson_name}::{section_name}"
            deck_id = generate_deck_id(lesson_num, section_num)
            deck = genanki.Deck(deck_id, deck_name)
            logger.info(f"Generating deck `{deck_name}` ({deck_id}).")

            # Check that the deck does not already exist.
            if deck_id in seen_decks:
                raise RuntimeError(f"Already generated deck `{deck_name}` ({deck_id}).")
            else:
                seen_decks.add(deck_id)

            for num, left, right in section:
                note_id = generate_note_id(lesson_num, section_num, num)
                logger.info(f"Adding note with ID `{note_id}`.")
                note = genanki.Note(
                    model=models[way],
                    fields=[left, right],
                    guid=note_id,
                )

                # Check that the note does not already exist.
                if note_id in seen_notes:
                    raise RuntimeError(f"Already generated note `{note_id}`.")
                else:
                    seen_notes.add(note_id)

                deck.add_note(note)
            decks.append(deck)
    package = genanki.Package(decks)
    package.write_to_file(path_out / out_name)
    logger.info(f"Written to `{(path_out / out_name).resolve()}`.")


if __name__ == "__main__":
    main()
