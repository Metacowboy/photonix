import inotify.adapters
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from photonix.photos.utils.db import record_photo
from photonix.photos.models import LibraryPath


class Command(BaseCommand):
    help = 'Watches photo directories and creates relevant database records for all photos that are added or modified.'

    def watch_photos(self):
        library_paths = LibraryPath.objects.filter(type='St', backend_type='Lo')

        for library_path in library_paths:
            print(f'Watching path for changes {library_path.path}')

            # TODO: Work out how to watch multiple paths at once
            i = inotify.adapters.InotifyTree(library_path.path)

            for event in i.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    if set(type_names).intersection(['IN_CLOSE_WRITE', 'IN_MOVED_TO', 'IN_DELETE', 'IN_MOVED_FROM']):  # TODO: Make moving photos really efficient by using the 'from' path
                        photo_path = Path(watch_path, filename)
                        if 'IN_DELETE' in type_names or 'IN_MOVED_FROM':
                            print(f'Removing photo "{photo_path}" from library "{library_path.library}"')
                        else:
                            print(f'Adding photo "{photo_path}" to library "{library_path.library}"')
                        record_photo(photo_path, library_path.library, type_names)

    def handle(self, *args, **options):
        try:
            self.watch_photos()
        except KeyboardInterrupt:
            exit(0)
