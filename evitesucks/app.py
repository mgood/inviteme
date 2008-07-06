from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException

from evitesucks.utils import local, local_manager, url_map
from evitesucks import views

class EviteSucks(object):
    def __init__(self):
        local.application = self
        local.locale = 'en_US'
        local.timezone = 'US/Pacific'

    def __call__(self, environ, start_response):
        req = Request(environ)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(req, **values)
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response),
                               [local_manager.cleanup])
