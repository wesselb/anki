# Anki Deck Generation for Languages

## Installation

Clone the repository and enter it:

```bash
git clone https://github.com/wesselb/anki
cd anki
```

Optionally, create a virtual environment and activate it:

```bash
virtualenv -p python3 venv
source venv/bin/activate
```

Finally, install the requirements:

```bash
pip install -r requirements.txt
```

## Usage

To generate Anki decks, you will need a folder with lesson files. For example, your folder structure may look as follows:

```
Dutch
Dutch/Lesson 1.txt
Dutch/Lesson 2.txt
Dutch/Lesson 3.txt
```

This will generate three Anki decks: `English::Lesson 1`, `English::Lesson 2`, and `English::Lesson 3`.

The syntax for a lesson file is as follows:
```
file_identifier | File Name

section_identifier | Section Name
id1 | word1 | translation1
id2 | word2 | translation2

section_identifier2 | Other Section Name
id3 | word3 | translation3
id4 | word4 | translation4
```

For example,
```
lesson1 | Les 1: Fruit en Groenten

fruit | Fruit
1 | appel | apple
2 | peer | pear

groenten | Groenten
1 | komkommer | cucumber
2 | aubergine | aubergine
3 | bloemkool | cauliflower
```

When you make changes, e.g. to correct typos, it is important that all identifiers remain the same. This will allow Anki to correctly merge changes into your existing decks and preserve your progress.

To generate the Anki `apkg`, run `generate_decks.py`, as follows:

```bash
$ python generate_decks.py --path ./Dutch
...
<Output>
...
[2024-03-13 09:31:05,792] INFO: Written to `./Dutch/output/2024-03-13_09-31-05/dutch.apkg`.
```

Then open the mentioned `apkg` at the end of the output to import your Decks into Anki.

### Options

You can adjust various options:

```bash
$ python generate_decks.py --help
Usage: generate_decks.py [OPTIONS]

  Generate an Anki deck.

Options:
  --path DIRECTORY                Path to directory with lesson files.
                                  [required]
  --name TEXT                     Name of the deck. Defaults to the name of
                                  the folder specified by `--path`.
  --way [both-ways|left-to-right|right-to-left]
                                  How to question the cards.
  --help                          Show this message and exit.
```

For the above Dutch example, to only translate from Dutch to English, run

```bash
$ python generate_decks.py --path ./Dutch --way right-to-left
```

## Existing Decks

The folder `Languages` contains some existing decks that I've been using for studying myself.
