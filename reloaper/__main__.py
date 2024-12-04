import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

import sunvox.api
from reloaper.audioplayer import AudioPlayer
from reloaper.hotkeys import keyboard_router
from reloaper.loopmanager import LoopManager
from reloaper.playbackmanager import PlaybackManager
from reloaper.pubsub import KeyPressed, hub, Key, message_logger
from reloaper.songmapper import SongMapper
from reloaper.songrenderer import SongRenderer
from reloaper.songwatcher import SongWatcher

log = logging.getLogger(__name__)


DEFAULT = "(default)"


def entrypoint(
    song_path: Path,
    freq: int = 44100,
    output_device: Annotated[str | None, typer.Option()] = None,
):
    # disable_echo_for_process()
    song_path = song_path.resolve()
    init_logging()
    init_sunvox(freq=freq)
    init_hub_logging()
    hub.add_subscriber(KeyPressed + ["q"], quitter)
    asyncio.run(main(song_path=song_path, output_device=output_device))


def init_hub_logging():
    hub.add_subscriber(Key("*"), message_logger)


def init_logging():
    FORMAT = "[%(name)s] %(message)s"
    logging.basicConfig(
        level=logging.NOTSET,
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    suppress_rust_notify_timeout()
    log.debug("Logging initialized")


def suppress_rust_notify_timeout():
    logging.getLogger("watchfiles.main").setLevel(logging.INFO)


def init_sunvox(*, freq: int):
    flags = (
        sunvox.api.INIT_FLAG.USER_AUDIO_CALLBACK
        | sunvox.api.INIT_FLAG.ONE_THREAD
        | sunvox.api.INIT_FLAG.AUDIO_FLOAT32
    )
    sunvox.api.init(None, freq, 2, flags)
    log.debug("Initialized SunVox library")


async def main(*, song_path: Path, output_device: str | None):
    song_watcher = SongWatcher(song_path=song_path)
    song_mapper = SongMapper()
    song_renderer = SongRenderer()
    audio_player = AudioPlayer(interface_name=output_device)
    _playback_manager = PlaybackManager()
    _loop_manager = LoopManager()
    await asyncio.gather(
        song_watcher.watch(),
        song_mapper.render_loop(),
        song_renderer.render_loop(),
        audio_player.audio_loop(),
        keyboard_router(),
    )


def quitter(key, data):
    exit(0)


if __name__ == "__main__":
    typer.run(entrypoint)
