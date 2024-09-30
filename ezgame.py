from mcdreforged.api.command import SimpleCommandBuilder, Integer, Text, GreedyText
from mcdreforged.api.all import CommandSource, PluginServerInterface

def on_load(server: PluginServerInterface, prev_module):
    builder = SimpleCommandBuilder()
    
    def hub(source: CommandSource):
        source.get_server().execute('execute as {} run trigger hub'.format(source.player))

    # declare your commands
    builder.command('!!hub', hub)
    # builder.command('!!email remove <email_id>', remove_email)
    # builder.command('!!email send <player> <message>', send_email)

    # define your command nodes
    # builder.arg('email_id', Integer)
    # builder.arg('player', Text)
    # builder.arg('message', GreedyText)

    # done, now register the commands to the server
    builder.register(server)