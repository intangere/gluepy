from glue import Glue, GlueProtocol

class CustomGlueProtocol(GlueProtocol):

    def on_connect(socket, response):

        print('Connected!')

        channel = socket.Channel('test')

        channel.on_message(on_message_test)

    def on_message(socket, data, channel):
        """
        onMessage for main channel
        """
        print('Received data:', data)
        socket.sendToMain('Hello world!')


def on_message_test(chan, data):
    print('Channel: %s' % chan.channel, 'Data: %s' % data)
    chan.send(data)

if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    glue = Glue(u"ws://127.0.0.1:8081/glue/ws")
    glue.factory.protocol = CustomGlueProtocol

    reactor.run()

