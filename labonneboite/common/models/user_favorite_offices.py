
import datetime

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship

from labonneboite.common.database import Base
from labonneboite.common.database import db_session
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.env import get_current_env, ENV_BONAPARTE


class UserFavoriteOffice(CRUDMixin, Base):
    """
    Stores the favorites offices of a user.

    Important:
    This model has a relation to the `etablissements` model via the `office_siret` field.
    But the `etablissements` table is dropped and recreated during the offices import process.
    Some entries in `etablissements` may disappear during this process.
    Therefore the `office_siret` foreign key integrity may be broken.
    The data deployment process takes care of dropping then recreating the foreign key
    during import. Favorites linked to no longer existing offices will be dropped.
    """
    __tablename__ = 'user_favorite_offices'
    __table_args__ = (
        UniqueConstraint('user_id', 'office_siret', name='_user_fav_office'),
    )

    id = Column(Integer, primary_key=True)
    # Set `ondelete` to `CASCADE`: when a `user` is deleted, all his `favorites` are deleted too.
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Set `ondelete` to `CASCADE`: when an `office` is deleted, all related `favorites` are deleted too.
    office_siret = Column(String(191), ForeignKey('etablissements.siret', ondelete='CASCADE'), nullable=True)
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship('User')
    if get_current_env() == ENV_BONAPARTE:
        # Disable relationship which mysteriously breaks on lbbdev only, not needed there anyway.
        # FIXME very ugly, try again to fix this bug. Bug happens in lbbdev environment only.
        pass
    else:
        office = relationship('Office', lazy='joined')

    __mapper_args__ = {
        'order_by': desc(date_created),  # Default order_by for all queries.
    }

    @classmethod
    def add_favorite(cls, user, office):
        """
        Add a favorite to a user.
        Avoid as much as possible replication errors by ignoring duplicates.
        """
        statement = cls.__table__.insert().prefix_with("IGNORE").values(
            user_id=user.id,
            office_siret=office.siret,
        )
        db_session.execute(statement)
        db_session.commit()

    @classmethod
    def user_favs_as_sirets(cls, user):
        """
        Returns the favorites offices of a user as a list of sirets.
        Useful to check if an office is already in the favorites of a user.
        """
        if user.is_anonymous:
            return []
        sirets = [fav.office_siret for fav in db_session.query(cls).filter_by(user_id=user.id)]
        return sirets

    @classmethod
    def user_favs_as_csv(cls, user):
        """
        Returns the favorites offices of a user as a CSV text.
        """
        header_row = cls.as_csv_header_row()

        if user.is_anonymous:
            return header_row

        rows = [fav.as_csv_row() for fav in db_session.query(cls).filter_by(user_id=user.id)]
        csv_text = "%s\r\n%s" % (
            header_row,
            "\r\n".join(rows),
        )
        return csv_text

    @classmethod
    def as_csv_header_row(cls):
        return 'siret;nom;adresse;ville;url'

    def as_csv_row(self):
        values = [
            self.office_siret,
            self.office.name,
            # add quotes to escape `,` frequently occuring in addresses
            '"%s"' % self.office.address_as_text,
            self.office.city,
            self.office.url,
        ]
        return ";".join(values)
