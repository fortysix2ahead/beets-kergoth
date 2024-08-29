"""Identify albums whose tracks have inconsistent album fields."""

from __future__ import absolute_import, division, print_function

from collections import defaultdict

from beets import ui
from beets.library import Album
from beets.plugins import BeetsPlugin
from beets.ui import decargs, print_


class InconsistentAlbumTracks(BeetsPlugin):
    def __init__(self):
        super(InconsistentAlbumTracks, self).__init__()

        self.config.add({
            'ignored_fields': ['added'],
            'included_fields': ['*'],
        })

    def commands(self):
        cmd = ui.Subcommand(
            u'inconsistent-album-tracks', help=u'Identify albums whose tracks have inconsistent album fields.'
        )
        cmd.parser.add_option(
            '-i', '--include-fields', default=self.config['included_fields'].as_str_seq(),
            action='append', metavar='FIELD', dest='included_fields',
            help='comma separated list of fields to show',
        )
        cmd.parser.add_option(
            '-x', '--exclude-fields', default=self.config['ignored_fields'].as_str_seq(),
            action='append', metavar='FIELD', dest='ignored_fields',
            help='comma separated list of fields to exclude/ignore',
        )
        cmd.func = self.command
        return [cmd]

    def set_fields(self):
        self.ignored_fields = set(self.config['ignored_fields'].as_str_seq())
        if '' in self.ignored_fields:
            self.ignored_fields.clear()

        self.album_fields = set(Album.item_keys) - self.ignored_fields
        self.included_fields = set()
        for fields in self.config['included_fields'].as_str_seq():
            fields = fields.split(',')
            if '' in fields or not fields:
                self.included_fields.clear()
            elif '*' in fields:
                self.included_fields |= self.album_fields
            else:
                self.included_fields |= set(fields)
        self.included_fields -= self.ignored_fields

    def command(self, lib, opts, args):
        self.config.set_args(opts)
        self.set_fields()

        query = decargs(args)
        for album in lib.albums(query):
            inconsistent_fields = defaultdict(list)
            album_items = album.items()

            for item in album_items:
                for field in self.included_fields:
                    if item.get(field, with_album=False) != album[field]:
                        inconsistent_fields[field].append(item)

            for field in sorted(inconsistent_fields):
                items = inconsistent_fields[field]
                if len(items) == len(album_items):
                    print_(f'{album}: field `{field}` has album value `{album[field]}` but all track values are `{items[0][field]}`')
                else:
                    for item in items:
                        print_(
                            "{}: field `{}` has value `{}` but album value is `{}`".format(
                                item,
                                field,
                                item.get(field, with_album=False),
                                album[field],
                            )
                        )
