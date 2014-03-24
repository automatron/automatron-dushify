import urllib
from twisted.internet import defer
from twisted.python import log
from twisted.web.client import getPage
from zope.interface import implements, classProvides
from automatron.controller.plugin import IAutomatronPluginFactory
from automatron.controller.client import IAutomatronMessageHandler
import json
from automatron.core.event import STOP
from automatron.core.util import parse_user


DEFAULT_TRIGGER = '!dushi'
DEFAULT_SERVICE = 'http://dushi.nattewasbeer.nl/aapje'


class DushifyPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronMessageHandler)

    name = 'dushify'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_message(self, client, user, channel, message):
        self._on_message(client, user, channel, message)

    @defer.inlineCallbacks
    def _on_message(self, client, user, channel, message):
        config = yield self.controller.config.get_plugin_section(self, client.server, channel)

        trigger = config.get('trigger', DEFAULT_TRIGGER)
        service = config.get('service', DEFAULT_SERVICE)
        nickname = parse_user(user)[0]

        if message.startswith(trigger + ' '):
            try:
                dushi = json.loads((yield getPage(
                    service,
                    method='POST',
                    postdata=urllib.urlencode({
                        'INPUT': message[len(trigger) + 1:].strip(),
                    }),
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                )).strip())['RESULT'].encode('utf-8')
                client.msg(user, '%s: %s' % (nickname, dushi))
            except Exception as e:
                log.err(e, 'Dushify failed')
                client.msg(user, '%s: derp' % nickname)
            defer.returnValue(STOP)
