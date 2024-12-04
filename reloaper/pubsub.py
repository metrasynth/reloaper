import logging

import aiopubsub
from aiopubsub import Key


log = logging.getLogger(__name__)

hub = aiopubsub.Hub()


KeyPressed = Key("key", "pressed")
PlaybackAudioReplace = Key("playback", "audio", "replace")
PlaybackLoopUpdate = Key("playback", "loop", "update")
PlaybackMapReplace = Key("playback", "map", "replace")
PlaybackPlayheadSet = Key("playback", "playhead", "set")
SongAudioRendered = Key("song", "audio", "rendered")
SongContentChanged = Key("song", "content", "changed")
SongLoopUpdate = Key("song", "loop", "update")
SongMapRendered = Key("song", "map", "rendered")


def message_logger(key, message):
    log.debug("%r %r", key, message)
