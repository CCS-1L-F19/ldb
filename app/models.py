import re
from app import db, login
from sqlalchemy import JSON
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from crossref_commons.retrieval import get_publication_as_refstring as cr_getref

reference = db.Table('reference',
    db.Column('document', db.Integer, db.ForeignKey('document.id'), primary_key=True),
    db.Column('reference', db.Integer, db.ForeignKey('document.id'), primary_key=True)
)


def _trykeys(dict_, keys):
    """
    Tries a list of keys in the given order
    """
    for k in keys:
        try:
            return dict_[k]
        except KeyError:
            pass
    return None


class Document(db.Model):
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(64), index=True, unique=True)
    references = db.relationship('Document', \
            secondary=reference, \
            backref=db.backref('referenced_by', lazy=True), \
            primaryjoin=id==reference.c.document,
            secondaryjoin=id==reference.c.reference
        )
    queried = db.Column(db.Boolean, default=False)
    meta = db.Column(JSON, default=None)

    def __getitem__(self, key):
        return self.meta[key]

    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        try:
            author = self['author'][0]['family']
            if len(self['author']) > 2:
                author += ' et. al'
            elif len(self['author']) == 2:
                author += ' & {}'.format(self['author'][1]['family'])
            year = _trykeys(self.meta, ['published-print', 'issued', 'created'])
            if year is None or author == '':
                raise KeyError # FIXME make this a diff error
            year = year['date-parts'][0][0]
            return '{} ({})'.format(author, year)
        except (KeyError, IndexError):
            pass
        try:
            citation = self['unstructured']
            author = citation[:re.search('\w{3,}\.\s', citation).end() - 1]
            year = re.findall(r'\b(?:20|19)\d\d\b', citation)[0]
            return '{} ({})'.format(author, year)
        except(KeyError, IndexError, AttributeError):
            pass
        try:
            if isinstance(self['title'], list):
                return self['title'][0]
            else:
                return self['title']
        except (KeyError, IndexError):
            return self.__repr__()

    def __repr__(self):
        try:
            if isinstance(self['DOI'], list):
                return self['DOI'][0]
            else:
                return self['DOI']
        except (KeyError, IndexError):
            pass
        return '<Document {}>'.format(self.id)

 
    def refstring(self, format_='apa'):
        key = 'cr_getref_{}'.format(format_)
        try:
            return self[key]
        except KeyError:
            pass
        c = str(self.meta)
        try:
            c = self['unstructured']
        except KeyError:
            pass
        try:
            c = cr_getref(self['doi'], format_)
        except KeyError:
            try:
                c = cr_getref(self['DOI'], format_)
            except KeyError:
                pass
        # TODO for this to actually save time we need to make the JSON object mutable
        self.meta[key] = c
        return c
