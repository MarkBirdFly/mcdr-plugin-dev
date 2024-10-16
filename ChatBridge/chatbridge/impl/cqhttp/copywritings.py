__all__ = ['CQHelpMessage',
           'StatsHelpMessage',
           'I18nHelpMessage']

CQHelpMessage = '''
!!help: 显示本条帮助信息
!!ping: pong!!
!!mc <消息>: 向 MC 中发送聊天信息 <消息>
!!online: 显示正版通道在线列表
!!stats <类别> <内容> [<-bot>]: 查询统计信息 <类别>.<内容> 的排名
'''.strip()

StatsHelpMessage = '''
!!stats <类别> <内容> [<-bot>]
添加 `-bot` 来列出 bot
例子:
!!stats used diamond_pickaxe
!!stats custom time_since_rest -bot
'''.strip()

I18nHelpMessage = '''
!!i18n 指令用法：
!!i18n <key> 显示翻译
!!i18n <key> <value> 添加或更新翻译
!!i18n <key> -d 删除翻译
可使用json格式批量编辑翻译, 例如:
!!i18n {"key1":"value1","key2":"value2","key3":null}
(null表示删除)
'''.strip()