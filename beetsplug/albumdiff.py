from itertools import zip_longest
from optparse import Values
from typing import Optional, List

from confuse import ConfigError, Configuration
from rich import box
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from beets.dbcore.db import Results
from beets.library import Library, Item, Album
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs

# from shlex import split

console = Console()

default_item_fmt = '$id $track $title $length $artist $album $year "$disc/$disctotal"'
default_album_fmt = "$id $albumartist $album $year $genre $mb_albumid"

def cmd_albumdiff(lib: Library, opts: Values, args, config):
    query = decargs(args)
    results = lib.albums(query)

    if len(results) > 2:
        left, right = [r for r in results][0:2]
        left_titles = [t for t in lib.items(f'album_id:{left.id}')]
        right_titles = [t for t in lib.items(f'album_id:{right.id}')]

        console.print(make_table(left, right, left_titles, right_titles))
    else:
        console.print('need at least two albums as a result to compare')

def make_style(config: Configuration) -> dict:
    cfg = {}

    try:
        cfg["box"] = getattr(box, config["style"]["box"].get(str).upper())
    except AttributeError:
        print("warning: invalid box style")
        cfg["box"] = box.MINIMAL

    cfg["show_header"] = config["style"]["show_header"].get(bool)
    cfg["row_styles"] = ["", "dim"]

    return cfg


def make_table(left: Album, right: Album, left_titles: List[Item], right_titles: List[Item]) -> Table:
    # table_style = make_style(config)
    # table = Table(**table_style)

    #album_fields = ['album', 'albumartist', 'id']

    #left = {f: left.evaluate_template(f"${f}") for f in album_fields}
    #right = {f: right.evaluate_template(f"${f}") for f in album_fields}

    table = Table()
    [ table.add_column( c ) for c in ['disc', 'track', 'artist', 'title', 'length', '', 'length', 'title', 'artist' ] ]

    for disc in range( 1, max( [left.disctotal, right.disctotal] ) + 1 ):
        total_tracks = max( *[ t.tracktotal for t in left_titles ], *[ t.tracktotal for t in right_titles ] )
        for track in range( 1, total_tracks + 1 ):
            l = next( ( t for t in left_titles if t.track == track and t.disc == disc ), None )
            r = next( ( t for t in right_titles if t.track == track and t.disc == disc ), None )

            # compare titles
            if l and r:
                if l.title == r.title:
                    left_title, right_title = f'[green]{l.title}[/green]', f'[green]{r.title}[/green]'
                else:
                    left_title, right_title = f'[red]{l.title}[/red]', f'[red]{r.title}[/red]'

                if l.artist == r.artist:
                    left_artist, right_artist = f'[green]{l.artist}[/green]', f'[green]{r.artist}[/green]'
                else:
                    left_artist, right_artist = f'[red]{l.artist}[/red]', f'[red]{r.artist}[/red]'

                left_length, right_length = str( l.length ), str( r.length )

            elif l:
                left_title, right_title = l.title, ''
                left_artist, right_artist = l.artist, ''
                left_length, right_length = str( l.length ), ''

            elif r:
                left_title, right_title = '', r.title
                left_artist, right_artist = '', r.artist
                left_length, right_length = '', str( r.length )

            else:
                raise RuntimeError() # this should not happen

            table.add_row(
                str(disc), str(track), left_artist, left_title, left_length, '', right_length, right_title, right_artist
            )

    return table

class AlbumDiffPlugin(BeetsPlugin):
    def __init__(self):
        super(AlbumDiffPlugin, self).__init__()

    def commands(self):
        cmd = Subcommand("albumdiff", help="compares two albums side by side", aliases=["ad"] )
        cmd.func = lambda lib, opts, args: cmd_albumdiff(lib, opts, args, self.config)
        return [cmd]
