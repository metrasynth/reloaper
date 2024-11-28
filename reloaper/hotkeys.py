import asyncio

from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings, KeyPress

from reloaper.pubsub import Key, hub


bindings = KeyBindings()


async def keyboard_router():
    done = asyncio.Event()
    input = create_input()

    def keys_ready():
        key_press: KeyPress
        for key_press in input.read_keys():
            hub.publish(Key("key", "pressed", key_press.key), ())

    with input.raw_mode(), input.attach(keys_ready):
        await done.wait()
