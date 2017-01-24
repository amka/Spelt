[![Codacy Badge](https://api.codacy.com/project/badge/Grade/321b490ed3db4fdab961f202198492d7)](https://www.codacy.com/app/meamka/Spelt?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=amka/Spelt&amp;utm_campaign=Badge_Grade)

# Spelt


Spelt is a small python application aimed
to allow users to backup their photo from https://vk.com to local storage.

It's made as reincarnation of [VKPorter](https://github.com/amka/VKPorter/)


## Installation

1. Download or clone to your computer.
2. Unpack if needed
3. Go to Spelt forlder and install via `pip`:

  ```bash
  $ cd spelt
  $ pip install .
  ```


## Usage

Synopsis:

    $ spelt [-h] [--username USERNAME] [--password PASSWORD] [--output OUTPUT] [--verbose]

See also `spelt --help`.

### Examples

    $ spelt -u amka 
    
photo albums will be exported to `./Spelt`.

    $ spelt -u amka  --output ~/Pictures/Gallery
    
photo albums will be exported to `~/Pictures/Gallery`.

