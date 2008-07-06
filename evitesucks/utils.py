import os
import sys

from babel import dates
from jinja import Environment, FileSystemLoader
from jinja import filters
from pytz import timezone
from werkzeug import Local, LocalManager, Response
from werkzeug.routing import Map, Rule

local = Local()
local_manager = LocalManager([local])
application = local('application')

url_map = Map()
def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate


def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)


def get_timezone(dt):
    tz = dt.tzinfo
    if hasattr(tz, '_tzid'): # hack for dateutil time zones
        tz = timezone(tz._tzid)
    return tz


@filters.simplefilter
def format_datetime(dt):
    return dates.format_datetime(dt, u'EEEE, MMM d, yyyy h:mm a',
                                 tzinfo=timezone(local.timezone),
                                 locale=local.locale)


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
jinja_env.globals['url_for'] = url_for
jinja_env.filters['datetime'] = format_datetime


def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')
