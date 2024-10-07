from qq_api import MessageEvent
import json
from aiocqhttp import CQHttp
from asyncio import AbstractEventLoop
import yaml
import threading
import importlib
import sys

config:dict
test = "123"
with open("data.json", "r", encoding='utf-8') as f:
    data = json.load(f)
with open("config.yml", "r", encoding='utf-8') as f:
    config = yaml.safe_load(f)
class msghandler:
    def __init__(self,event_loop:AbstractEventLoop,final_bot:CQHttp):
        self.event_loop = event_loop
        self.final_bot = final_bot
        self.reload:callable = None
    def server_msg(self, msg:dict):#服务器消息处理
        pass#FIXME 服务器消息处理
    def on_message(self, event:MessageEvent):#qq消息处理
        content = event.content
        self.event = event
        is_command = False
        prefix = None
        for prefix in config["command_prefix"]:
            if prefix != "" and content.startswith(prefix):
                is_command = True
                break
        if is_command:
            self.on_qq_command(event)
        if event.group_id in config["groups"]["sync_groups"]:
            user_id = str(event.user_id)
            if user_id in data["data"].keys():
                # 管理员提示为绿色ID
                if user_id in config["admins"]:
                    pass#FIXME 向mc服务器发送消息
                else:
                    pass#FIXME 向mc服务器发送消息
            else:
                self.reply(event,f"[CQ:at,qq={user_id}] 无法转发您的消息，请通过/bound <Player>绑定游戏ID")
    def reply(self, event:MessageEvent, message:str):
        self.event_loop.create_task(
            self.final_bot.send(event,message)
            )
    def send(self, msg:dict):
        for i in msg["groups"]:
            self.event_loop.create_task(
                self.final_bot.send(group_id=i,message=msg["massage"])
            )
    def parse_command_list(self,msg: str, prefix: str):# 指令格式化
        # 如果prefix长度大于1，与实际指令之间需要加空格
        if len(prefix) > 1:
            command = msg.split()
            if len(command) == 1 and command[0] == prefix:
                # 只有指令前缀，则当做help
                return ["help"]
            else:
                # 去掉前缀，保留指令本身
                return command[1:]
        else:
            return msg[1:].split()
    def on_qq_command(self, event:MessageEvent):
        global config, data
        command = self.parse_command_list(event.content, config["command_prefix"][0])
        if command[0] == "help":        #/help
            self.help(command)
        elif command[0] == "reload":    #/reload
            if len(command)==1:
                with open("config.yml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.reply(event, "配置文件和数据文件已重载")
            elif command[1] == "config":
                with open("config.yml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                self.reply(event, "配置文件已重载")
            elif command[1] == "data":
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.reply(event, "数据文件已重载")
            elif command[1] == "bot":
                self.reload(event)
            else:
                self.reply(event,"命令参数错误\n正确用法:/reload [config|data]")
        elif command[0] == "debug":     #/debug
            if len(command)==1:
                self.reply(event,"命令缺少参数\n正确用法:/debug thread")
            elif command[1] == "thread":
                thread_list = threading.enumerate()
                self.reply(event, f'当前线程列表, 共 {len(thread_list)} 个活跃线程:\n{thread_list}')
            elif command[1] == "test":
                self.reply(event,test)
            else:
                self.reply(event,"命令参数错误\n正确用法:/debug thread")
        elif command[0] == "list":      #/list WIP
            self.wip()#FIXME /list
        elif command[0] == "server":    #/server WIP
            self.wip()#FIXME /server
        elif command[0] == "say":       #/say WIP
            self.wip()#FIXME /say
        elif command[0] == "bound":     #/bound
            if len(command)==1:
                self.reply(event,"命令缺少参数\n正确用法:/bound <player>")
            elif len(command)>=3:
                self.reply(event,"命令参数过多\n正确用法:/bound <player>")
            else:
                qq_id = str(event.user_id)
                if qq_id in data["data"].keys():
                    _id = data["data"][qq_id]
                    if _id == command[1]:
                        self.reply(event,f"你已绑定到玩家{_id}，无需修改")
                    elif command[1] in dict.values(data["data"]):
                        self.reply(event,f"玩家{command[1]}已经被绑定过了，请换一个玩家名")
                    else:
                        data["data"][qq_id] = command[1]
                        self.save_data()
                        self.reply(event,f"你绑定的玩家从{_id}更改到{command[1]}")
                else:
                    if command[1] in dict.values(data["data"]):
                        self.reply(event,f"玩家{command[1]}已经被绑定过了，请换一个玩家名")
                    else:
                        data["data"][qq_id] = command[1]
                        self.save_data()
                        self.reply(event,f"成功绑定到玩家{command[1]}")
        elif command[0] == "query":     #/query
            if len(command)==1:
                qq_id = str(event.user_id)
                if qq_id in data["data"].keys():
                    self.reply(event,f"你绑定的玩家是{data['data'][qq_id]}")
                else:
                    self.reply(event,"你尚未绑定任何玩家,请使用/bound <player>绑定玩家")
            elif len(command)>=4:
                self.reply(event,"命令参数过多\n正确用法:/query [qq|mc] [<qq>|<player>]")
            else:
                if command[1] == "qq":
                    if len(command)==2:
                        qq_id = str(event.user_id)
                        if qq_id in data["data"].keys():
                            self.reply(event,f"你绑定的玩家是{data['data'][qq_id]}")
                        else:
                            self.reply(event,"你尚未绑定任何玩家,请使用/bound <player>绑定玩家")
                    else:
                        qq_id = command[2]
                        if qq_id.startswith("[@"):
                            qq_id = qq_id[2:-1]
                        if qq_id in data["data"].keys():
                            self.reply(event,f"qq{qq_id}绑定的玩家是{data['data'][qq_id]}")
                        else:
                            self.reply(event,f"qq{qq_id}尚未绑定任何玩家")
                elif command[1] == "mc":
                    if len(command)==2:
                        qq_id = str(event.user_id)
                        if qq_id in data["data"].keys():
                            self.reply(event,f"你绑定的玩家是{data['data'][qq_id]}")
                        else:
                            self.reply(event,"你尚未绑定任何玩家,请使用/bound <player>绑定玩家")
                    else:
                        player = command[2]
                        if player in dict.values(data["data"]):
                            for i in data["data"].keys():
                                if data["data"][i] == player:
                                    self.reply(event,f"玩家{player}绑定的QQ是{i}")
                        else:
                            self.fuzzy_search(player,event)
                else:
                    if len(command)==3:
                        self.reply(event,"参数错误\n正确用法:/query [qq|mc] [<qq>|<player>]")
                    elif command[1].startswith("[@"):
                        qq_id = command[1][2:-1]
                        if qq_id in data["data"].keys():
                            self.reply(event,f"qq{qq_id}绑定的玩家是{data['data'][qq_id]}")
                        else:
                            self.reply(event,f"qq{qq_id}尚未绑定任何玩家")
                    elif command[1].isdigit():
                        qq_id = command[1]
                        if qq_id in data["data"].keys():
                            self.reply(event,f"qq{qq_id}绑定的玩家是{data['data'][qq_id]}")
                        else:
                            self.reply(event,f"qq{qq_id}尚未绑定任何玩家")
                    else:
                        player = command[1]
                        if player in dict.values(data["data"]):
                            for i in data["data"].keys():
                                if data["data"][i] == player:
                                    self.reply(event,f"玩家{player}绑定的QQ是{i}")
                        else:
                            self.fuzzy_search(player,event)
        elif command[0] == "command":   #/command WIP
            self.wip()#FIXME /command
        else:                           #未知指令
            self.reply(event, "未知指令,输入/help查看帮助")
    def help(self,command:dict):        #/help指令处理
        help_msg = config["help_msg"]
        need_help_commands = config["need_help_commands"]
        if len(command) == 1:
            self.reply(self.event,help_msg["help"])
        else:
            if command[1] in need_help_commands:
                self.reply(self.event,help_msg[command[1]])
            else:
                self.reply(self.event,help_msg["help"])
    def save_data(self):                #保存数据
        with open("data.json","w") as f:
            json.dump(data,f,indent=4)
    def fuzzy_search(self, player:str, event:MessageEvent):#模糊搜索
        if len(player)>=3:
            search_term = player
            matches = [qq_id for qq_id, p in data["data"].items() if search_term in p]
            if matches:
                matches_player = [data["data"][i] for i in matches]
                matches_list = ""
                for qq_id, player in zip(matches, matches_player):
                    matches_list += f"\n{player}({qq_id})"
                self.reply(event, f"玩家{search_term}尚未绑定任何QQ\n你可能想查询的是: {matches_list}")
    def wip(self):                      # W.I.P
        self.reply(self.event,"该指令开发中……")
    def reload_class(self,event:MessageEvent):
        module_name = self.__class__.__module__
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            print(f"模块 {module_name} 已重新加载")
            self.reply(event,"命令处理器已重载")
            return msghandler(self.event_loop, self.final_bot)