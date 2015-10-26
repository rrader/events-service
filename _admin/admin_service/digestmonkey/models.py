from admin_service.extensions import db
from sqlalchemy.orm import backref, relationship


class DigestMonkeyConfig(db.Model):
    __tablename__ = 'mailchimpkeys'
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_key = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team = relationship("Team", backref=backref("digestmonkey_config", uselist=False))
