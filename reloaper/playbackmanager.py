import logging

import attrs
import numpy as np

from reloaper.pubsub import (
    PlaybackAudioReplace,
    PlaybackMapReplace,
    SongAudioRendered,
    SongMapRendered,
    hub,
)
from reloaper.songmapper import SongMapSnapshot
from reloaper.songrenderer import SongAudioSnapshot

log = logging.getLogger(__name__)


@attrs.define
class PlaybackManager:
    latest_audio: np.ndarray | None = None
    latest_audio_timestamp: float | None = None
    latest_map: np.ndarray | None = None
    latest_map_timestamp: float | None = None

    def __attrs_post_init__(self):
        hub.add_subscriber(
            SongAudioRendered,
            self.handle_song_audio_rendered,
        )
        hub.add_subscriber(
            SongMapRendered,
            self.handle_song_map_rendered,
        )

    def handle_song_audio_rendered(self, key, song_audio_snapshot: SongAudioSnapshot):
        self.latest_audio = song_audio_snapshot.audio
        self.latest_audio_timestamp = song_audio_snapshot.timestamp
        self.update_playback_if_map_and_audio_match()

    def handle_song_map_rendered(self, key, song_map_snapshot: SongMapSnapshot):
        self.latest_map = song_map_snapshot.line_frame_map
        self.latest_map_timestamp = song_map_snapshot.timestamp
        self.update_playback_if_map_and_audio_match()

    def update_playback_if_map_and_audio_match(self):
        if self.latest_audio_timestamp == self.latest_map_timestamp:
            self.update_playback()

    def update_playback(self):
        hub.publish(
            PlaybackAudioReplace,
            self.latest_audio,
        )
        hub.publish(
            PlaybackMapReplace,
            SongMapSnapshot(
                line_frame_map=self.latest_map,
                timestamp=self.latest_map_timestamp,
            ),
        )
