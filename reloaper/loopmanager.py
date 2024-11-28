import logging

import attrs
import numpy as np
from prompt_toolkit.keys import Keys

from reloaper.audioplayer import PlaybackLoop, Playhead
from reloaper.pubsub import hub, Key
from reloaper.songmapper import SongMapSnapshot


log = logging.getLogger(__name__)


@attrs.define
class LoopManager:
    start_line: int = 0
    length_lines: int = 0
    song_length: int = 0
    line_frame_map: np.ndarray | list = [0]
    last_published_loop: PlaybackLoop | None = None

    def __attrs_post_init__(self):
        hub.add_subscriber(
            Key("key", "pressed", Keys.Up),
            self.on_key_up,
        )
        hub.add_subscriber(
            Key("key", "pressed", Keys.Down),
            self.on_key_down,
        )
        hub.add_subscriber(
            Key("key", "pressed", Keys.Left),
            self.on_key_left,
        )
        hub.add_subscriber(
            Key("key", "pressed", Keys.Right),
            self.on_key_right,
        )
        hub.add_subscriber(
            Key("playback", "map", "replace"),
            self.on_playback_map_replace,
        )

    def on_key_up(self, key, data):
        self.increase_length()

    def on_key_down(self, key, data):
        self.decrease_length()

    def on_key_left(self, key, data):
        self.decrease_start()

    def on_key_right(self, key, data):
        self.increase_start()

    def on_playback_map_replace(self, key, data: SongMapSnapshot):
        self.song_length = len(data.line_frame_map)
        self.line_frame_map = data.line_frame_map
        self.update_constraints()
        self.publish_loop()

    def increase_length(self):
        self.length_lines += 1
        self.update_constraints()
        self.publish_loop()

    def decrease_length(self):
        self.length_lines -= 1
        self.update_constraints()
        self.publish_loop()

    def increase_start(self):
        self.start_line += 1
        self.update_constraints()
        self.publish_loop()

    def decrease_start(self):
        self.start_line -= 1
        self.update_constraints()
        self.publish_loop()

    def update_constraints(self):
        self.start_line = max(0, self.start_line)
        self.start_line = min(self.start_line, len(self.line_frame_map) - 1)
        self.length_lines = min(self.song_length - self.start_line, self.length_lines)
        self.length_lines = max(0, self.length_lines)

    def publish_loop(self):
        start_frame = self.line_frame_map[self.start_line]
        if self.length_lines:
            end_line = self.start_line + self.length_lines
            if end_line >= len(self.line_frame_map):
                end_frame = 0
            else:
                end_frame = self.line_frame_map[end_line]
        else:
            end_line = 0
            end_frame = 0
        new_song_loop = SongLoop(
            start_line=self.start_line,
            length_lines=self.length_lines,
        )
        new_playback_loop = PlaybackLoop(start_frame=start_frame, end_frame=end_frame)
        hub.publish(Key("playback", "loop", "update"), new_playback_loop)
        hub.publish(Key("song", "loop", "update"), new_song_loop)
        if new_playback_loop != self.last_published_loop:
            hub.publish(Key("playback", "playhead", "set"), Playhead(frame=start_frame))
            self.last_published_loop = new_playback_loop


@attrs.define
class SongLoop:
    start_line: int
    length_lines: int
