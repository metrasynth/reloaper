# Reloaper: The Reloading Looper for SunVox

Reloaper gives you an alternative way to play SunVox songs while you're composing them.
Instead of real-time rendering inside SunVox, it pre-renders the song.
You can then select a loop region in the song to repeat.

This can be especially useful when you are composing SunVox projects programmatically.
Instead of loading a project in SunVox and manually triggering playback,
you can keep hacking on your composition while you're continuously listening to portions of it.

The magic happens when you change your song project file and save it.
Reloaper will detect changes to the file and re-render the song.
Playback continues seamlessly without interruption when the new audio is swapped in.

## Installation

1. Clone this repository: `git clone https://github.com/metrasynth/reloaper`
2. Make sure you have installed [`uv`](https://docs.astral.sh/uv/).

## Usage

Run Reloaper by passing the path to your SunVox song project file:

```bash
uv run python -m reloaper path/to/song.sunvox
```

More help: 

```bash
uv run python -m reloaper --help
```

## Keybindings

| Key | Action |
| --- | --- |
| Up | Increase length of loop region |
| Down | Decrease length of loop region |
| Left | Decrease start of loop region |
| Right | Increase start of loop region |
| Space | Play/Pause |
| Q | Quit |

## Features / TODO list

- [x] Watches a SunVox song file for changes.
- [x] When a change is detected (not currently rendering):
  - [x] Renders the audio for the song to a WAV in memory.
  - [x] Renders the time map for the song to memory.
- [x] When a change is detected (currently rendering):
  - [x] Schedules a re-render to start after the current one finishes.
- [x] When a song and time map are both rendered:
  - [x] Replaces the current playback audio with the new render.
  - [ ] If the frames for the current loop region in the time map have changed:
    - [ ] Moves the playhead to the start frame of the current loop. 
- [x] When starting playback:
  - [x] If the loop region is unset, starts playing at line 0.
  - [x] If the loop region is set, starts playing at the first frame of the loop beginning.
- [x] During playback:
  - [x] If the loop region is set, audio loops when the last frame of the last line is reached.
- [ ] Display:
  - [ ] Playback state.
  - [ ] Rendering state.
  - [ ] Current line is shown.
  - [ ] Current time position in song is shown.
- [x] Initial state:
  - [x] Playing the song.
  - [x] No loop region.
- [x] User can perform these actions:
  - [x] Adjust start + length of loop region, specified by line number.
  - [x] Play audio
  - [x] Pause audio
  - [x] Quit

