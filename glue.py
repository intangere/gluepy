#Simple implementation of the basic Glue protocol WebSockets

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet import reactor

from json import dumps, loads

VERSION = '1.9.1'
MAINCHANNELNAME = 'm'
MAXCHANNELLENGTH = 1024

COMMANDS = {
  'Len' : 2,
  'Init' : 'in',
  'Ping' : 'pi',
  'Pong' : 'po',
  'Close' : 'cl',
  'Invalid' : 'iv',
  'DontAutoReconnect' : 'dr',
  'ChannelData': 'cd'
}

STATES = {
  'Disconnected' : 'disconnected',
  'Connecting' : 'connecting',
  'Reconnecting' : 'reconnecting',
  'Connected' : 'connected'
}

class GlueProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        self.glue_state = 'Connecting'
        self.init()
        self.factory.resetDelay()
        self.on_connect(response)

    def on_connect(self, response):
        print('connected not overridden')

    def on_message(self, response):
        print('connected not overridden')

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print('Unimplemented')
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
            packet = self.parse(payload.decode('utf8'))
            self.handle(packet)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.glue_state = 'Disconnected'

    def init(self):
        self.sendMessage(('%s%s' % (COMMANDS['Init'], dumps({'version' : VERSION}))).encode())

    def sendToChan(self, data, channel = ''):
        self.sendMessage(self.buildChanData(data, channel), isBinary = False)

    def sendToMain(self, data):
        self.sendMessage(self.buildChanData(data, MAINCHANNELNAME), isBinary = False)

    def buildChanData(self, data, channel = ''):
        if type(data) != str:
           data = dumps(data)

        chan_len = len(channel)
        packed = ('%s%s&%s%s' % (COMMANDS['ChannelData'], chan_len, channel, data)).encode()

        print('Built Chan Data:', repr(packed))
        return packed

    def parseChanData(self, data):
        args = data.split('&', 1)

        if len(args[0]) < MAXCHANNELLENGTH:
           try:
              chan_length = int(args[0])
           except ValueError:
              raise Exception('InvalidCommand')
        else:
              raise Exception('InvalidChannelLength')

        return args[1][0:chan_length], \
               args[1][chan_length:]


    def handle(self, packet):

        command = packet.get('command', None)
        data = packet.get('data', None)

        if not command:
           self.invalid()

        if command == 'in':
           self._id = loads(data)['socketID']

        if command == 'cd':
           channel, data = self.parseChanData(data)

           if channel == MAINCHANNELNAME:
              self.on_message(data, channel)
           else:
              if channel in self._channels:
                 chan = self._channels.get(channel)
                 chan.on_message(chan, data)

        if command == 'pi':
           self.sendMessage('po'.encode())

    def on_message(self, data, chan=''):
        print('on_message not overridden!')

    def ping(self):
        self.sendMessage(COMMANDS['Ping'])

    def pong(self):
        self.sendMessage(COMMANDS['Pong'])

    def invalid(self):
        ...

    def parse(self, payload):
        command = payload[0:2]
        data = payload[2:]

        return {'command': command, 'data': data}

    def Channel(self, channel):

        if not getattr(self, '_channels', None):
           self._channels = dict()

        chan = Channel(self, channel)

        self._channels[channel] = chan

        return chan

class GlueFactory(WebSocketClientFactory, ReconnectingClientFactory):

    protocol = GlueProtocol
    factor = 1

    def clientConnectionFailed(self, connector, reason):
        print("Client connection failed .. retrying ..")
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        print("Client connection lost .. retrying ..")
        self.retry(connector)

    def buildProtocol(self, address):
        proto = WebSocketClientFactory.buildProtocol(self, address)
        self.connectedProtocol = proto
        return proto

class Channel():

    def __init__(self, socket, channel):
        self.socket = socket
        self.channel = channel

    def send(self, data):
        self.socket.sendToChan(data, self.channel)

    def on_message(self, onRead=None):

        if not onRead:
           print('on_message not overridden!')
           return

        self.on_message = onRead

class Glue():

    def __init__(self, websocket_url):
        self.sockets = dict()
        self.ws_url = websocket_url
        self.factory = GlueFactory(self.ws_url)

        base_url = websocket_url.split('/')[2]
        host, port = base_url.split(':')

        reactor.connectTCP(host, int(port), self.factory)

        self.factory.protocol.onConnectCbk = self.onConnect
        self.factory.protocol.onMessageCbk = self.onMessage

    def getSocket(self):
        return self.factory.connectedProtocol

    def onConnect(self, response):
        print('onConnect not overridden')

    def onMessage(self, response):
        print('onMessage not overridden')

