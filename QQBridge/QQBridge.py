# -*- coding: utf-8 -*-
import re
import time
import json
import asyncio
import threading
from logging import INFO, DEBUG
import qq_api
import pickle
import yaml
from msghandler import msghandler

import psutil
import requests
import socket
from flask import Flask, request

from config import Config
from logger import Logger

help_msg = '''
stop 关闭 QQBridge
help 获取帮助
reload config 重载配置文件
debug thread 查看线程列表
'''

with open('config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    # main_groups = config['groups']['main_groups']
    # sync_groups = config['groups']['sync_groups']
    # manager_groups = config['groups']['manager_groups']

def start_socket():
    global running
    running = True
    # 创建一个 socket 对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定 IP 地址和端口号
    server_socket.bind(('localhost', 12345))
    # 监听连接
    server_socket.listen(10)
    print("服务器已启动，等待连接...")
    try:
        while running:
            # 设置超时时间，以便能够定期检查运行状态
            server_socket.settimeout(1)
            try:
                # 接受连接 
                conn, addr = server_socket.accept()
                # 为每个客户端连接创建一个新线程
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.start()
            except socket.timeout:
                continue
    finally:
        server_socket.close()

class Console(threading.Thread):
    def __init__(self, logger, config):
        super().__init__(name='Console')
        self.process = psutil.Process()
        self.logger = logger
        self.config = config
        self.cmd = []
        self.logger.info('After startup, type "help" for help')

    def run(self):
        self.server_thread = threading.Thread(target=start_socket,name="Socket")
        self.server_thread.start()
        while True:
            try:
                raw_input = input()
                # 直接回车
                if raw_input == '':
                    continue
                # 拆分清理
                cmd_list = re.split(r'\s+', raw_input)
                self.cmd = [i for i in cmd_list if i != '']
                self.logger.debug('Console input: ')
                self.logger.debug(f'    Raw input: "{raw_input}"')
                self.logger.debug(f'    Split result: {self.cmd}')
                self.cmd_parser()
            except (EOFError, KeyboardInterrupt):
                self.exit()

    def send_msg(self, msg):
        self.logger.info(msg)

    def cmd_parser(self):
        if self.cmd[0] in ['stop', '__stop__', 'exit']:
            self.exit()
        elif self.cmd[0] == 'help':
            self.send_msg(help_msg)
        elif self.cmd[0] == 'reload':
            self.cmd_reload_parser()
        elif self.cmd[0] == 'debug':
            self.cmd_debug_parser()

    def cmd_reload_parser(self):
        if len(self.cmd)<1:
            self.cmd[1] = 'config'
        if self.cmd[1] == 'config':
            self.reload_config()

    def cmd_debug_parser(self):
        if len(self.cmd)<1:
            self.cmd[1] = 'thread'
        if self.cmd[1] == 'thread':
            thread_list = threading.enumerate()
            self.logger.info(
                f'当前线程列表, 共 {len(thread_list)} 个活跃线程:'
            )
            for i in thread_list:
                self.logger.info(f'    - {i.name}')

    def reload_config(self):
        self.logger.info('正在重载配置文件')
        self.config.reload()
        if self.config['debug_mode']:
            self.logger.set_level(DEBUG)
        else:
            self.logger.set_level(INFO)
        self.logger.info('重载配置文件完成')

    def exit(self):
        global running
        running = False
        self.logger.info('Exiting QQBridge')
        self.server_thread.join()
        self.process.terminate()

class DownstreamSocket(threading.Thread):
    def __init__():
        pass#FIXME 下游websocket通信

class QQBridge:
    def __init__(self):
        self.cqhttp = None
        self.logger = Logger()
        self.config = Config(self.logger)
        if self.config['debug_mode']:
            self.logger.set_level(DEBUG)

        # Console
        self.console = Console(self.logger, self.config)
        self.console.start()

        threading.Thread(target=self.cqhttp_init).start()
    def cqhttp_init(self):
        self.cqhttp = qq_api.RecvMessage('config.yml')
        cqhttp_init.set()
    def send(self, data, headers):
        self.logger.debug(
            f'All server list: '
            f'{json.dumps(self.config["server_list"], indent=4)}'
        )
        for server_name, i in self.config['server_list'].items():
            target = f'http://{i["host"]}:{i["port"]}'
            self.logger.info(f'Transmitting to the server {server_name}')
            self.logger.debug(f'Server address {target}')
            # 添加标识
            data['server'] = server_name
            try:
                requests.post(target, json=data, headers=headers)
                self.logger.info(f'Transmit to {server_name} success')
            except:
                self.logger.warning(f'Transmit to {server_name} failed')

cqhttp_init = threading.Event()
bridge = QQBridge()

print("ok")
cqhttp_init.wait()
final_bot = qq_api.get_bot()
event_loop = qq_api.get_event_loop()
handler = msghandler(event_loop, final_bot)
bridge.cqhttp.callback_list = {"on_message": handler.on_message}

def reload_handler(event):
    global handler
    handler = handler.reload_class(event)
    handler.reload = reload_handler
    bridge.cqhttp.callback_list = {"on_message": handler.on_message}

handler.reload = reload_handler

def handle_client(conn, addr):
    print(f"连接地址: {addr}")
    while True:
        # 接收数据
        data = conn.recv(1024)
        if not data:
            break
        try:
            message = pickle.loads(data)
            handler.server_msg(message)
            print(f"收到数据: {message}")
        except pickle.UnpicklingError:
            print("无法解析数据")
        
        # 回显数据
        conn.sendall("Get".encode())


# def send_to_main_groups(msg):
#     for i in main_groups:
#         event_loop.create_task(
#             final_bot.send_group_msg(group_id=i, message=msg)
#         )

# def send_to_sync_groups(msg):
#     for i in sync_groups:
#         event_loop.create_task(
#             final_bot.send_group_msg(group_id=i, message=msg)
#         )

# def send_to_manager_groups(msg):
#     for i in manager_groups:
#         event_loop.create_task(
#             final_bot.send_group_msg(group_id=i, message=msg)
#         )

