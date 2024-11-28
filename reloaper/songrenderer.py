import asyncio
import ctypes
import logging
from pathlib import Path

import attrs
import numpy as np

import sunvox.api
from reloaper.pubsub import hub, Key

log = logging.getLogger(__name__)


@attrs.define
class SongRenderer:
    song_path: Path

    latest_audio: np.ndarray | None = None
    latest_audio_timestamp: float | None = None
    render_event: asyncio.Event = attrs.field(factory=asyncio.Event)

    def __attrs_post_init__(self):
        hub.add_subscriber(Key("song", "content", "changed"), self.trigger_render)

    async def render_loop(self):
        log.debug("Starting SongRenderer render loop")
        while True:
            await self.render_event.wait()
            self.render_event.clear()
            with sunvox.api.Slot(self.song_path) as slot:
                song_length_frames = slot.get_song_length_frames()
                log.debug("Rendering %r frames of song audio...", song_length_frames)
                current_frame = 0
                buffer_size = 4096
                buffer = np.zeros((buffer_size, 2), np.float32)
                new_audio = np.ndarray((song_length_frames, 2), np.float32)
                slot.play_from_beginning()
                while current_frame < song_length_frames:
                    sunvox.api.audio_callback(
                        buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                        buffer_size,
                        0,
                        sunvox.api.get_ticks(),
                    )
                    end_frame = min(current_frame + buffer_size, song_length_frames)
                    copy_size = end_frame - current_frame
                    new_audio[current_frame:end_frame] = buffer[:copy_size]
                    current_frame = end_frame
                self.latest_audio = new_audio
                self.latest_audio_timestamp = self.song_path.stat().st_mtime
                log.debug("latest_audio_timestamp %r", self.latest_audio_timestamp)
                self.publish_song_audio_rendered()

    def publish_song_audio_rendered(self):
        hub.publish(
            Key("song", "audio", "rendered"),
            SongAudioSnapshot(
                audio=self.latest_audio,
                timestamp=self.latest_audio_timestamp,
            ),
        )

    def trigger_render(self, key, message):
        self.render_event.set()


@attrs.define
class SongAudioSnapshot:
    audio: np.ndarray = attrs.field(repr=False)
    timestamp: float
