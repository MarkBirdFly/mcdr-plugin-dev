import html
import json
from typing import Optional

import websocket

from chatbridge.common.logger import ChatBridgeLogger
from chatbridge.core.client import ChatBridgeClient
from chatbridge.core.network.protocol import ChatPayload, CommandPayload, CustomPayload
from chatbridge.impl import utils
from chatbridge.impl.cqhttp.config import CqHttpConfig
from chatbridge.impl.cqhttp.copywritings import *
from chatbridge.impl.cqhttp.copywritings import *
from chatbridge.impl.tis.protocol import StatsQueryResult, OnlineQueryResult
from chatbridge.tools.i18n import I18n
from chatbridge.tools.i18n import I18n

ConfigFile = 'ChatBridge_CQHttp.json'
cq_bot: Optional['CQBot'] = None
chatClient: Optional['CqHttpChatBridgeClient'] = None
i18n: Optional['CQ_I18n'] = None
config: Optional[CqHttpConfig] = None

class CQ_I18n(I18n):
    def __init__(self):
        super().__init__()
        self.logger = ChatBridgeLogger('CQ_I18n', file_handler=chatClient.logger.file_handler)
    def update_word(self, word_dict, group_id):
        if not word_dict:
            cq_bot.send_text('json不能为空', group_id)
            return
        response = self._update_word(word_dict)
        self.word.update(word_dict)
        self.write_word()
        self.logger.info(response)
        cq_bot.send_text(response, group_id)

class CQBot(websocket.WebSocketApp):
    def __init__(self, config: CqHttpConfig):
        self.config = config
        websocket.enableTrace(True)
        url = 'ws://{}:{}/'.format(self.config.ws_address, self.config.ws_port)
        if self.config.access_token is not None:
            url += '?access_token={}'.format(self.config.access_token)
        self.logger = ChatBridgeLogger('Bot', file_handler=chatClient.logger.file_handler)
        self.logger.info('Connecting to {}'.format(url))
        self.group_id = None
        super().__init__(url, on_message=self.on_message, on_close=self.on_close)

    def start(self):
        self.run_forever()

    def on_message(self, _, message: str):
        try:
            if chatClient is None:
                return
            data = json.loads(message)
            if data.get('post_type') == 'message' and data.get('message_type') == 'group':
                if data['group_id'] in self.config.react_groups_id:
                    self.group_id = data['group_id']
                    self.logger.info('QQ chat message: {}'.format(data))
                    args = data['raw_message'].split(' ')

                    if len(args) == 1 and args[0] == '!!help':
                        self.logger.info('!!help command triggered')
                        self.send_text(CQHelpMessage)

                    if len(args) == 1 and args[0] == '!!ping':
                        self.logger.info('!!ping command triggered')
                        self.send_text('pong!!')

                    if len(args) >= 2 and args[0] == '!!mc':
                        self.logger.info('!!mc command triggered')
                        sender = data['sender']['card']
                        if len(sender) == 0:
                            sender = data['sender']['nickname']
                        text = html.unescape(data['raw_message'].split(' ', 1)[1])
                        chatClient.broadcast_chat(text, sender)

                    if len(args) == 1 and args[0] == '!!online':
                        self.logger.info('!!online command triggered')
                        if not self.config.client_to_query_online:
                            self.logger.info('!!online command is not enabled')
                            self.send_text('!!online 指令未启用')
                            return

                        if chatClient.is_online():
                            command = args[0]
                            client = self.config.client_to_query_online
                            self.logger.info('Sending command "{}" to client {}'.format(command, client))
                            chatClient.send_command(client, command, {"group_id":self.group_id})
                        else:
                            self.send_text('ChatBridge 客户端离线')

                    if len(args) >= 1 and args[0] == '!!stats':
                        self.logger.info('!!stats command triggered')
                        if not self.config.client_to_query_stats:
                            self.logger.info('!!stats command is not enabled')
                            self.send_text('!!stats 指令未启用')
                            return

                        command = '!!stats rank ' + ' '.join(args[1:])
                        if len(args) == 0 or len(args) - int(command.find('-bot') != -1) != 3:
                            self.send_text(StatsHelpMessage)
                            return
                        if chatClient.is_online:
                            client = self.config.client_to_query_stats
                            self.logger.info('Sending command "{}" to client {}'.format(command, client))
                            chatClient.send_command(client, command, {"group_id":self.group_id})
                        else:
                            self.send_text('ChatBridge 客户端离线')
                    
                    if len(args) >= 1 and args[0] == '!!i18n':
                        self.logger.info('!!i18n command triggered')
                        group = data['group_id']
                        if args[1].startswith('{'):
                            try:
                                i18n_dict = json.loads(message['raw_message'].lstrip('!!i18n '))
                                i18n.update_word(i18n_dict, group)
                            except:
                                self.send_text('参数错误',group_id=group)
                                return
                        if len(args) == 2:
                            if args[1] in i18n.i18n:
                                self.send_text(f'“{args[1]}”的翻译是“{i18n(args[1])}”')
                            else:
                                self.send_text(f'“{args[1]}”暂无翻译')
                        elif len(args) == 3:
                            i18n.update_word({args[1]:args[2]}, self.group_id)
                        else:
                            self.send_text(I18nHelpMessage)
        except:
            self.logger.exception('Error in on_message()')

    def on_close(self, *args):
        self.logger.info("Close connection")

    def _send_text(self, text, group_id):
        data = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": text
            }
        }
        self.send(json.dumps(data))

    def send_text(self, text, group_id=None):
        if group_id == None:
            group_id = self.group_id
        msg = ''
        length = 0
        lines = text.rstrip().splitlines(keepends=True)
        for i in range(len(lines)):
            msg += lines[i]
            length += len(lines[i])
            if i == len(lines) - 1 or length + len(lines[i + 1]) > 500:
                self._send_text(msg, group_id)
                msg = ''
                length = 0

    def send_message(self, sender: str, message: str, group_id = None):
        self.send_text('[{}] {}'.format(sender, message), group_id)


class CqHttpChatBridgeClient(ChatBridgeClient):
    def on_chat(self, sender: str, payload: ChatPayload):
        global cq_bot
        if cq_bot is None:
            return
        try:
            if payload.type == 'chat':
                try:
                    prefix, message = payload.message.split(' ', 1)
                except:
                    pass
                else:
                    for group_id in config.sync_groups_id:
                        cq_bot.send_message(sender, payload.formatted_str(), group_id)
                    if prefix == '!!qq':
                        self.logger.info('Triggered command, sending message {} to qq'.format(payload.formatted_str()))
                        payload.message = message
                        cq_bot.send_message(sender, payload.formatted_str(), config.main_group_id)
            if payload.type == 'start_stop':
                for group_id in config.react_groups_id:
                    cq_bot.send_message(sender, payload.message, group_id)
            if payload.type == 'join_leave':
                for group_id in config.sync_groups_id:
                    cq_bot.send_message(sender, payload.message, group_id)
        except:
            self.logger.exception('Error in on_message()')

    def on_command(self, sender: str, payload: CommandPayload):
        if not payload.responded:
            return
        if payload.command.startswith('!!stats '):
            result = StatsQueryResult.deserialize(payload.result)
            group_id = payload.params.get("group_id")
            if result.success:
                messages = ['====== {} ======'.format(i18n(result.stats_name))]
                messages.extend(result.data)
                messages.append('总数：{}'.format(result.total))
                cq_bot.send_text('\n'.join(messages), group_id)
            elif result.error_code == 1:
                cq_bot.send_text('统计信息未找到', group_id)
            elif result.error_code == 2:
                cq_bot.send_text('StatsHelper 插件未加载', group_id)
        elif payload.command == '!!online':
            result = OnlineQueryResult.deserialize(payload.result)
            cq_bot.send_text('====== 玩家列表 ======\n{}'.format('\n'.join(result.data)))

    def on_custom(self, sender: str, payload: CustomPayload):
        global cq_bot
        if cq_bot is None:
            return
        try:
            __example_data = {
                'cqhttp_client.action': 'send_text',
                'text': 'the message you want to send'
            }
            if payload.data.get('cqhttp_client.action') == 'send_text':
                text = payload.data.get('text')
                self.logger.info('Triggered custom text, sending message {} to qq'.format(text))
                for groups in payload.data.get('group_id'):
                    cq_bot.send_text(text, groups)
        except:
            self.logger.exception('Error in on_custom()')


def main():
    global chatClient, cq_bot, i18n, config
    config = utils.load_config(ConfigFile, CqHttpConfig)
    chatClient = CqHttpChatBridgeClient.create(config)
    utils.start_guardian(chatClient)
    utils.register_exit_on_termination()
    print('Starting CQ Bot')
    i18n = CQ_I18n()
    cq_bot = CQBot(config)
    cq_bot.start()
    print('Bye~')


if __name__ == '__main__':
    main()
