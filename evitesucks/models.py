from google.appengine.ext import db


class Event(db.Model):
    name = db.StringProperty()
    start = db.DateTimeProperty()
    end = db.DateTimeProperty()
    description = db.TextProperty()
    location = db.TextProperty()
    owner = db.UserProperty()

    @classmethod
    def from_vevent(cls, vevent):
        name = vevent.getChildValue('summary')
        start = vevent.getChildValue('dtstart')
        end = vevent.getChildValue('dtend')
        description = vevent.getChildValue('description')
        location = vevent.getChildValue('location')
        return cls(name=name, start=start, end=end, description=description,
                   location=location)


class Invitation(db.Model):
    event = db.ReferenceProperty(Event)
    full_name = db.StringProperty()
    email = db.EmailProperty()
    attending = db.IntegerProperty() # None = no response, 0 = No, 1+ = Yes
    comments = db.TextProperty()
    maybe = db.BooleanProperty()

    @classmethod
    def from_vcard(cls, vcard, **params):
        full_name = vcard.getChildValue('fn')
        for child in vcard.getChildren():
            if child.name == 'EMAIL' and 'pref' in child.params['TYPE']:
                email = child.value
                break
        else:
            email = vcard.getChildValue('email')
        return cls(full_name=full_name, email=email, **params)

    @classmethod
    def by_event(cls, event):
        query = cls.all()
        query.filter('event = ', event)
        query.order('full_name')
        print 'invites: %s' % query.count(1000)
        return query.fetch(1000)

    @classmethod
    def grouped_by_response(cls, event):
        invites = cls.by_event(event)
        attending = [inv for inv in invites if inv.attending >= 1 and not inv.maybe]
        possible = [inv for inv in invites if inv.attending >= 1 and inv.maybe]
        not_attending = [inv for inv in invites if inv.attending == 0]
        no_response = [inv for inv in invites if inv.attending is None]
        return attending, possible, not_attending, no_response

