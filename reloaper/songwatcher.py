import logging
from collections.abc import AsyncIterable
from pathlib import Path

import attrs
import contextlib
from watchfiles import awatch, Change

from reloaper.pubsub import SongContentChanged, hub

log = logging.getLogger(__name__)


@attrs.define
class SongWatcher:
    song_path: Path

    async def watch(self):
        watch_dir = self.song_path.is_dir()
        log.debug("Watching %r", self.song_path)
        if not watch_dir:
            log.debug("Initial change to kick off rendering.")
            self.publish_change(self.song_path)
        async for change, path in self.wrapped_awatch(self.song_path):
            if not watch_dir and path != self.song_path:
                continue
            if watch_dir and path.suffix != ".sunvox":
                continue
            if not watch_dir and change != Change.modified:
                continue
            if watch_dir and change == Change.deleted:
                continue
            self.publish_change(path)

    async def wrapped_awatch(self, path) -> AsyncIterable[tuple[Change, Path]]:
        with contextlib.suppress(RuntimeError):
            async for changes in awatch(path):
                for change, path in changes:
                    yield change, Path(path)

    def publish_change(self, path):
        hub.publish(
            SongContentChanged,
            SongChanged(path=path),
        )


@attrs.define
class SongChanged:
    path: Path
