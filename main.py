from glue import Glue, GlueProtocol

class CustomGlueProtocol(GlueProtocol):

    def on_connect(socket, response):
        print('onConnect callback!')

        socket.sendToMain({'token': 'kek'})

        product = socket.Channel('product')
        status = socket.Channel('status')

        product.on_message(socket.on_message_product)

    def on_message(socket, data, channel):
        """
        onMessage for main channel
        """
        print('Received data:', data)
        socket.sendToMain('this is illegal')

    def on_message_product(self, chan, data):
        print('Channel: %s' % chan.channel, 'Data: %s' % data)


if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    glue = Glue(u"ws://127.0.0.1:8081/glue/ws")
    glue.factory.protocol = CustomGlueProtocol

    reactor.run()

