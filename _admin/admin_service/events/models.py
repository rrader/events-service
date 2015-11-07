from admin_service.extensions import db


class SuggestedEvent(db.Model):
    __tablename__ = 'suggested_events'

    title = db.Column(db.Unicode(256), nullable=False)
    agenda = db.Column(db.UnicodeText(), nullable=False)
    social = db.Column(db.UnicodeText(), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    level = db.Column(db.String(20), default='NONE', nullable=False)
    place = db.Column(db.Unicode(256), nullable=True)
    when_start = db.Column(db.DateTime(), nullable=False)
    when_end = db.Column(db.DateTime(), nullable=True)
    only_date = db.Column(db.Boolean(), default=True, nullable=False)
    registration_url = db.Column(db.String(500), nullable=True)
    team = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    submitter_email = db.Column(db.String(256), nullable=False)
    secret = db.Column(db.String(256), nullable=False,
                       doc='secret key to edit the suggested event',
                       primary_key=True)
