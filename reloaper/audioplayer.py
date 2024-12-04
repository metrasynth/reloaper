from __future__ import annotations

import asyncio
import logging

import attrs
import numpy as np
import sounddevice

from reloaper.pubsub import (
    KeyPressed,
    PlaybackAudioReplace,
    PlaybackLoopUpdate,
    PlaybackPlayheadSet,
    hub,
)

log = logging.getLogger(__name__)


class CannotFindOutputDevice(RuntimeError):
    pass


@attrs.define
class AudioPlayer:
    interface_name: str | None
    audio: np.ndarray = attrs.field(factory=lambda: np.zeros((44100, 2), np.float32))
    audio_len: int = 44100
    finished: asyncio.Event = attrs.field(factory=asyncio.Event)
    start_frame: int = 0
    end_frame: int = 44100
    current_frame: int = 0
    playing: bool = True

    def __attrs_post_init__(self):
        hub.add_subscriber(
            PlaybackAudioReplace,
            self.handle_audio_replace,
        )
        hub.add_subscriber(
            PlaybackLoopUpdate,
            self.handle_loop_update,
        )
        hub.add_subscriber(
            PlaybackPlayheadSet,
            self.handle_playhead_set,
        )
        hub.add_subscriber(
            KeyPressed + [" "],
            self.handle_key_pressed_space,
        )

    def handle_audio_replace(self, key, audio: np.ndarray):
        self.audio = audio
        self.audio_len = len(audio)

    def handle_loop_update(self, key, loop: PlaybackLoop):
        self.start_frame = loop.start_frame
        self.end_frame = loop.end_frame or self.audio_len

    def handle_playhead_set(self, key, playhead: Playhead):
        self.current_frame = playhead.frame

    def handle_key_pressed_space(self, key, data):
        self.playing = not self.playing

    async def audio_loop(self):
        output_stream = self.create_output_stream()
        with output_stream:
            await self.finished.wait()

    def create_output_stream(self):
        return sounddevice.OutputStream(
            device=self.find_device_id(self.interface_name),
            samplerate=44100,
            channels=2,
            blocksize=4096,
            callback=self.output_stream_callback,
            finished_callback=self.finished.set,
        )

    def output_stream_callback(
        self,
        data: np.ndarray,
        frames: int,
        time: float,
        status: sounddevice.CallbackFlags,
    ):
        if not self.playing:
            data[:] = np.zeros((len(data), 2), np.float32)
            return
        data_frame_start = 0
        data_frames = len(data)
        while data_frame_start < data_frames:
            start_frame = self.current_frame
            data_frames_left = frames - data_frame_start
            end_frame = min(
                start_frame + data_frames_left,
                min(self.audio_len, self.end_frame),
            )
            copy_size = end_frame - start_frame

            data_frame_end = data_frame_start + copy_size
            extracted_audio = self.audio[start_frame:end_frame]
            if len(extracted_audio):
                data[data_frame_start:data_frame_end] = extracted_audio
            data_frame_start += copy_size
            self.current_frame += copy_size
            if self.current_frame >= self.end_frame:
                self.current_frame = self.start_frame

    @staticmethod
    def find_device_id(interface_name: str | None):
        if interface_name is None:
            device_id = sounddevice.default.device[1]
            log.info(f"Using default output device {device_id}")
            return device_id
        for device_id, device_detail in enumerate(sounddevice.query_devices()):
            if device_detail["name"] == interface_name:
                break
        else:
            raise CannotFindOutputDevice()
        return device_id


@attrs.define
class PlaybackLoop:
    start_frame: int
    end_frame: int


@attrs.define
class Playhead:
    frame: int
