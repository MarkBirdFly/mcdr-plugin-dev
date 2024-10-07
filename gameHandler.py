import re

from mcdreforged.handler.impl import VanillaHandler


class MyHandler(VanillaHandler):
    def get_name(self) -> str:
        return 'gameHandler'

    def parse_server_stdout(self, text: str):
        info = super().parse_server_stdout(text)
        if info.player is None:
            m = re.fullmatch(r'(\[Not Secure] )?\[CHAT][^\|]*\| (?P<name>[^:]+): (?P<message>.*)', info.content)
            if m is not None and self._verify_player_name(m['name']):
                info.player, info.content = m['name'], m['message']
        return info


def on_load(server, prev_module):
    server.register_server_handler(MyHandler())