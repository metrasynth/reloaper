import asyncio
import ctypes
import logging
from datetime import datetime
from pathlib import Path

import attrs
import numpy as np

import sunvox.api
from reloaper.pubsub import SongContentChanged, SongMapRendered, hub
from reloaper.songwatcher import SongChanged


log = logging.getLogger(__name__)


@attrs.define
class SongMapper:
    latest_map: np.ndarray | None = None
    latest_map_timestamp: float | None = None
    render_queue: asyncio.Queue[Path] = attrs.field(factory=asyncio.Queue)

    def __attrs_post_init__(self):
        hub.add_subscriber(SongContentChanged, self.trigger_render)

    async def render_loop(self):
        log.debug("Starting SongMapper render loop")
        while True:
            song_path = await self.render_queue.get()
            log.debug("Rendering song map...")
            with sunvox.api.Slot(song_path) as slot:
                song_length_lines = slot.get_song_length_lines()
                new_map = np.zeros(song_length_lines, np.uint32)
                get_time_map_result = slot.get_time_map(
                    start_line=0,
                    len=song_length_lines,
                    dest=new_map.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
                    flags=sunvox.api.TIME_MAP.FRAMECNT,
                )
                log.debug("get_time_map_result %r", get_time_map_result)
                self.latest_map = new_map
                self.latest_map_timestamp = song_path.stat().st_mtime
                log.debug("latest_map[:5] %r", self.latest_map[:5])
                log.debug("latest_map_timestamp %r", self.latest_map_timestamp)
                self.publish_song_map_rendered()

    def publish_song_map_rendered(self):
        hub.publish(
            SongMapRendered,
            SongMapSnapshot(
                line_frame_map=self.latest_map,
                timestamp=self.latest_map_timestamp,
            ),
        )

    def trigger_render(self, key, message: SongChanged):
        self.render_queue.put_nowait(message.path)


@attrs.define
class SongMapSnapshot:
    line_frame_map: np.ndarray = attrs.field(repr=False)
    timestamp: float
