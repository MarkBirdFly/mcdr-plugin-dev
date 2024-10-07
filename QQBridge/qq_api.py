import re
import time
import logging
import threading
from asyncio import AbstractEventLoop, new_event_loop, run
import yaml

from uvicorn import Config, Server
from aiocqhttp import CQHttp, Event

__all__ = [
    "MessageEvent",
    "get_event_loop",
    "get_bot",
    "RecvMessage",
]

event_loop: AbstractEventLoop
bot: CQHttp
__uvicorn_server: Server

cqhttp_init_event = threading.Event()

class MessageEvent(Event):
    content: str


# class PluginConfig(Serializable):
#     http: dict = {
#         "enable": False,
#         "api_host": "127.0.0.1",
#         "api_port": 5700,
#         "post_host": "127.0.0.1",
#         "post_port": 5701,
#     }
#     websocket: dict = {
#         "enable": False,
#         "host": "127.0.0.1",
#         "port": 5700,
#     }

class RecvMessage:
    def __init__(self, config_path:str):
        self.config_path = config_path
        self.callback_list = {}
        self.config = self.load_config()
        self.setup()
        # try:
        #     while True:
        #         input()
        # except (KeyboardInterrupt,EOFError):
        #     print("正在关闭QQ API...")
        #     try:
        #         self.stop()
        #     except:
        #         pass

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)


    def setup(self):
        api_root = None
        host = self.config['websocket']['host']
        port = self.config['websocket']['port']
        print(
            f"WebSocket mode enabled at {host}:{port}"
        )
        
        # cqhttp init
        
        def cqhttp_init():
            global event_loop, bot
            bot = CQHttp(api_root=api_root)
            event_loop = new_event_loop()
        
            async def cqhttp_main():
                global __uvicorn_server
                __uvicorn_server = Server(Config(
                    bot.server_app,
                    host=host,
                    port=port,
                    loop="none",
                    log_level=logging.CRITICAL
                ))
        
                @bot.on_message
                async def on_message(event: MessageEvent):
                    # parse content
                    event.content = event.raw_message
                    event.content = re.sub(
                        r'\[CQ:image,file=.*?]',
                        '[图片]',
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:share,file=.*?]',
                        '[链接]',
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:face,id=.*?]',
                        '[表情]',
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:record,file=.*?]',
                        '[语音]',
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:video,file=.*?]', 
                        '[视频]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:rps]', 
                        '[猜拳]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:dice]', 
                        '[掷骰子]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:shake]', 
                        '[窗口抖动]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:poke,.*?]', 
                        "[戳一戳]", 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:anonymous.*?]', 
                        "[匿名消息]", 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:contact,type=qq.*?]', 
                        "[推荐好友]", 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:contact,type=group.*?]', 
                        "[推荐群]", 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:location,.*?]', 
                        "[定位分享]", 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:music,type=.*?]', 
                        '[音乐]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:forward,id=.*?]', 
                        '[转发消息]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:file(?:,.*?)*]', 
                        '[文件]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:redbag,title=.*?]', 
                        '[红包]', 
                        event.content)
                    event.content = re.sub(
                        r'\[CQ:mface,.*?]', 
                        '[表情]', 
                        event.content)
                    event.content = event.content.replace('CQ:at,qq=', '@')
                    self.callback_list['on_message'](event)
                
                @bot.on_notice
                async def on_notice(event:MessageEvent):
                    pass
                
                @bot.on_request
                async def on_request(event:MessageEvent):
                    pass
                
                @bot.on_meta_event
                async def on_meta_event(event:MessageEvent):
                    pass
                
                cqhttp_init_event.set()
                await __uvicorn_server.serve()
            event_loop.run_until_complete(cqhttp_main())
        threading.Thread(target=cqhttp_init, name="QQ API").start()
        cqhttp_init_event.wait()
        print("QQ API started.")

    def stop(self):
        if __uvicorn_server:
            __uvicorn_server.shutdown()
        if event_loop:
            event_loop.stop()

def get_event_loop() -> AbstractEventLoop:
    """
    Get asyncio event loop
    :return: AbstractEventLoop.
    """
    return event_loop


def get_bot() -> CQHttp:
    """
    Get CQHttp instance.
    :return: CQHttp.
    """
    return bot
