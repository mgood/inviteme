import os
import sys

from babel import dates
from jinja import Environment, FileSystemLoader
from jinja import filters
from dateutil.tz import gettz
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


def abs_url_for(endpoint, **values):
    return url_map.bind('inviteme.matt-good.net').build(endpoint, values, force_external=True)


@filters.simplefilter
def format_datetime(dt):
    return dates.format_datetime(dt, u'EEEE, MMM d, yyyy h:mm a',
                                 tzinfo=gettz(local.timezone),
                                 locale=local.locale)


@filters.simplefilter
def format_date(dt):
    tz = gettz(local.timezone)
    dt = dt.replace(tzinfo=tz)
    dt = tz.fromutc(dt)
    return dates.format_date(dt, u'EEEE, MMM d, yyyy', locale=local.locale)


@filters.simplefilter
def format_time(dt):
    return dates.format_time(dt, u'h:mm a',
                             tzinfo=gettz(local.timezone),
                             locale=local.locale)


@filters.simplefilter
def attriter(values, *attrs):
    import operator
    getter = operator.attrgetter(*attrs)
    return [getter(v) for v in values]


@filters.stringfilter
def breaklines(text):
    return (text.replace('\r\n', '\n')
                .replace('\r', '\n')
                .replace('\n', '<br>\n'))


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
jinja_env.globals['url_for'] = url_for
jinja_env.globals['abs_url_for'] = abs_url_for
jinja_env.filters['datetime'] = format_datetime
jinja_env.filters['date'] = format_date
jinja_env.filters['time'] = format_time
jinja_env.filters['breaklines'] = breaklines
jinja_env.filters['attriter'] = attriter


def render_response(template, **context):
    return Response(render_template(template, **context), mimetype='text/html')


def render_template(template, **context):
    return jinja_env.get_template(template).render(**context)
