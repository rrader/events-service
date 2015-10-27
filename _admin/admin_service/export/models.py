from sqlalchemy.dialects.postgresql import ARRAY, JSON
from admin_service.extensions import db
from sqlalchemy.orm import backref, relationship


class ExportICSConfig(db.Model):
    __tablename__ = 'exportics_configs'
    id = db.Column(db.Integer, primary_key=True)
    calendar_prodid = db.Column(db.String(100))
    query = db.Column(db.String(200))
    config_slug = db.Column(db.String(200))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team = relationship("Team", backref=backref("exportics_config", uselist=False))
