import vobject
from google.appengine.ext import db
from werkzeug import Response, redirect
from evitesucks import models
from evitesucks.utils import expose, render_template, url_for

@expose('/')
def index(req):
    return render_template('index.html')


@expose('/create')
def create(req):
    ics_file = req.files.get('ics')
    if not ics_file:
        return render_template('create.html', error='No file', method=req.method)
    vobj = vobject.readOne(ics_file)
    event = models.Event.from_vevent(vobj.vevent)
    event_key = event.put()
    return redirect(url_for('update', key=str(event_key)))


@expose('/update/<key>')
def update(req, key):
    event = models.Event.get(db.Key(key))
    if req.method == 'GET':
        attending, not_attending, no_response = (
                models.Invitation.grouped_by_response(event))
        return render_template('update.html',
                               event=event,
                               attending=attending,
                               not_attending=not_attending,
                               no_response=no_response)
    for vcard in vobject.readComponents(req.files['invitees']):
        invite = models.Invitation.from_vcard(vcard, event=event)
        invite.put()
    return redirect(url_for('update', key=key))

# TODO action to send out invitations

@expose('/respond/<key>')
def respond(req, key):
    invite = models.Invitation.get(db.Key(key))
    if req.method == 'GET':
        if invite.attending >= 1:
            guests = invite.attending - 1
        else:
            guests = ''
        attending, not_attending, no_response = (
                models.Invitation.grouped_by_response(invite.event))
        total_attending = sum(invite.attending for invite in attending)
        return render_template('view.html', invite=invite, event=invite.event,
                               total_attending=total_attending,
                               guests=guests, attending=attending,
                               not_attending=not_attending)
    if 'yes' in req.form:
        invite.attending = int(req.form['guests'] or 0) + 1
    else:
        invite.attending = 0
    invite.email = req.form['email']
    invite.comments = req.form['comments']
    invite.put()
    return redirect(url_for('respond', key=key))
