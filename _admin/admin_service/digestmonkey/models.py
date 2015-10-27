from sqlalchemy.dialects.postgresql import ARRAY, JSON
from admin_service.extensions import db
from sqlalchemy.orm import backref, relationship


class DigestMonkeyConfig(db.Model):
    __tablename__ = 'mailchimpkeys'
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_key = db.Column(db.String(100))
    templates_uri = db.Column(db.String(100))
    github_key = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team = relationship("Team", backref=backref("digestmonkey_config", uselist=False))


class PublishedDigest(db.Model):
    __tablename__ = 'digests'
    id = db.Column(db.Integer, primary_key=True)
    events_data = db.Column(JSON)
    events_ids = db.Column(ARRAY(db.Integer))
    template = db.Column(db.String(100))
    preview = db.Column(db.Text)
    s_list = db.Column(db.String(20))
    s_list_name = db.Column(db.String(100))
    from_name = db.Column(db.String(100))
    from_email = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    campaign_id = db.Column(db.String(20))
    web_id = db.Column(db.String(20))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team = relationship("Team", backref=backref("digests"))
