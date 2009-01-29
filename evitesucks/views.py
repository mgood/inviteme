import vobject
from google.appengine.ext import db
from google.appengine.api import users, mail
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from werkzeug import Response, redirect
from werkzeug.exceptions import NotFound, Forbidden
from evitesucks import models
from evitesucks.utils import expose, render_template, render_response, url_for

@expose('/')
def index(req):
    return render_response('index.html')


@expose('/login')
def login(req):
    return redirect(users.create_login_url(url_for('index')))


@expose('/logout')
def logout(req):
    return redirect(users.create_logout_url(url_for('index')))


@expose('/create')
def create(req):
    user = users.get_current_user()
    if user is None:
        return redirect(users.create_login_url(url_for('create')))
    if user.email() != 'matt@matt-good.net':
        raise Forbidden
    if req.method == 'GET':
        return render_response('create.html', user=user)
    ics_file = req.files.get('ics')
    if not ics_file:
        return render_response('create.html', error='No file', user=user)
    vobj = vobject.readOne(ics_file)
    event = models.Event.from_vevent(vobj.vevent)
    event.owner = user
    event_key = event.put()
    return redirect(url_for('update', key=str(event_key)))


@expose('/update/<key>')
def update(req, key):
    event = models.Event.get(db.Key(key))
    if event.owner != users.get_current_user():
        raise Forbidden
    if event is None:
        raise NotFound
    if req.method == 'GET':
        attending, possible, not_attending, no_response = (
                models.Invitation.grouped_by_response(event))
        return render_response('update.html',
                               event=event,
                               attending=attending,
                               possible=possible,
                               not_attending=not_attending,
                               no_response=no_response)
    for vcard in vobject.readComponents(req.files['invitees']):
        invite = models.Invitation.from_vcard(vcard, event=event)
        invite_key = str(invite.put())
        _send_invite(invite, invite_key)
    return redirect(url_for('update', key=key))


def _send_invite(invite, invite_key):
    event = invite.event
    mail.send_mail(sender='matt@matt-good.net',
                   reply_to=event.owner.email(),
                   to='%s <%s>' % (invite.full_name, invite.email),
                   subject='Invitation to %s' % event.name,
                   body=render_template('email.txt', invite=invite,
                                        event=event, invite_key=invite_key))


@expose('/respond/<key>')
def respond(req, key):
    invite = models.Invitation.get(db.Key(key))
    if invite is None:
        raise NotFound
    if req.method == 'GET':
        if invite.attending >= 1:
            guests = invite.attending - 1
        else:
            guests = ''
        attending, possible, not_attending, no_response = (
                models.Invitation.grouped_by_response(invite.event))
        return render_response('respond.html', invite=invite, event=invite.event,
                               guests=guests, attending=attending,
                               possible=possible,
                               not_attending=not_attending)
    if 'no' in req.form:
        invite.attending = 0
    else:
        invite.attending = int(req.form['guests'] or 0) + 1
        invite.maybe = 'maybe' in req.form
    invite.email = req.form['email']
    invite.comments = req.form['comments']
    invite.put()
    _send_response(invite)
    return redirect(url_for('respond', key=key))


def _send_response(invite):
    event = invite.event
    if not invite.attending:
        status = 'will not'
    elif invite.maybe:
        status = 'might'
    else:
        status = 'will'
    subject = ('%s %s be attending %s' %
               (invite.full_name, status, event.name))
    mail.send_mail(sender='matt@matt-good.net',
                   reply_to=invite.email,
                   to=event.owner.email(),
                   subject=subject,
                   body=render_template('rsvp.txt', invite=invite, event=event))

# FIXME add wrapper to send_mail that catches OverQuotaError and retries in a second to avoid errors
