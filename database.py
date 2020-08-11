import datetime
import peewee

db = peewee.SqliteDatabase("database.db")


class BaseModel(peewee.Model):
    class Meta:
        database = db


class SpectatedChat(BaseModel):
    """ORM model of the spectated chat table"""
    chat_id = peewee.IntegerField()
    title = peewee.CharField()
    invite_link = peewee.CharField(null=True, default=None)
    language = peewee.CharField(null=True, default=None)
    timezone = peewee.CharField(null=True, default=None)
    notifications = peewee.BooleanField(default=False)
    enabled = peewee.BooleanField(default=False)

    class Meta:
        database = db

    def is_spectated(chat_id):
        try:
            return SpectatedChat.get(SpectatedChat.chat_id == chat_id)
        except peewee.DoesNotExist:
            return False

    def add_to_spectated(chat_id, title, invite_link=None, language='en', timezone='utc', notifications=False,
                         enabled=False):
        title = bytes(title, 'utf-8').decode('utf-8', 'ignore')
        return SpectatedChat.create(
            chat_id=chat_id, title=title, invite_link=invite_link, language=language, timezone=timezone,
            notifications=notifications, enabled=enabled)

    def remove_from_spectated(chat_id):
        ReferralRecord.delete().where(ReferralRecord.chat_id == chat_id).execute()
        return True

    def drop_referral_records(self):
        ReferralRecord.delete().where(ReferralRecord.chat_id == self.chat_id).execute()
        return True

    def retrieve_referral_records(self):
        results = []

        records = ReferralRecord. \
            select(ReferralRecord.from_user). \
            where(ReferralRecord.joined_chat == True,
                  ReferralRecord.chat_id == self.chat_id). \
            namedtuples()

        for r in set(records):
            results.append({
                'user_id': r.from_user,
                'invited_users_count': ReferralRecord.
                    select().
                    where(ReferralRecord.joined_chat == True,
                          ReferralRecord.chat_id == self.chat_id,
                          ReferralRecord.from_user == r.from_user).count()
            })

        if len(results) == 0:
            return None

        results.sort(key=lambda x: x['invited_users_count'], reverse=True)
        return results

    def retrieve_personal_referral_records(self, from_user):
        return ReferralRecord\
            .select()\
            .where(ReferralRecord.chat_id == self.chat_id,
                   ReferralRecord.from_user == from_user,
                   ReferralRecord.joined_chat == True)\
            .count()

    def get_chats_list(enabled=None):
        if enabled is None:
            query = SpectatedChat.select()
        else:
            query = SpectatedChat.select().where(SpectatedChat.enabled == enabled)

        if query.count() == 0:
            return None

        return query

    def get_by_title(title):
        return SpectatedChat.get_or_none(SpectatedChat.title == title)

    def get_by_chat_id(chat_id):
        return SpectatedChat.get_or_none(SpectatedChat.chat_id == chat_id)

    def update_invite_link(self, invite_link=None):
        self.invite_link = invite_link
        self.save()
        return True

    def update_language(self, language='en'):
        self.language = language
        self.save()
        return True

    def update_timezone(self, timezone='en'):
        self.timezone = timezone
        self.save()
        return True

    def update_notifications(self, notifications=False):
        self.notifications = notifications
        self.save()
        return True

    def update_enabled(self, enabled=False):
        self.enabled = enabled
        self.save()
        return True

    def migrate(self, new_chat_id):
        for record in ReferralRecord.get_list(chat_id=self.chat_id):
            record.chat_id = new_chat_id
            record.save()

        self.chat_id = new_chat_id
        self.save()
        return True


class ReferralRecord(BaseModel):
    """ORM model of a user referral record"""
    chat_id = peewee.IntegerField()
    to_user_chat_id = peewee.IntegerField()
    from_user = peewee.IntegerField()
    to_user = peewee.IntegerField()
    date = peewee.DateTimeField()
    joined_chat = peewee.BooleanField(default=False)

    class Meta:
        database = db

    def add(chat_id, from_user, to_user, to_user_chat_id):
        return ReferralRecord.create(chat_id=chat_id, to_user_chat_id=to_user_chat_id, from_user=from_user,
                                     to_user=to_user, date=datetime.datetime.now(), joined_chat=False)

    def get_by_to_user(chat_id, to_user):
        return ReferralRecord.get_or_none(ReferralRecord.chat_id == chat_id, ReferralRecord.to_user == to_user)

    def get_by_from_user(chat_id, from_user):
        return ReferralRecord.get_or_none(ReferralRecord.chat_id == chat_id, ReferralRecord.from_user == from_user)

    def update_joined_chat(self, joined_chat=False):
        self.joined_chat = joined_chat
        self.save()
        return True


def database_startup():
    with db:
        db.create_tables([SpectatedChat, ReferralRecord])


def database_closeup():
    db.close()
