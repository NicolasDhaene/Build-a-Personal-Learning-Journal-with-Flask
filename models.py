from peewee import *
from flask_login import UserMixin


DATABASE = SqliteDatabase("journal.db")


class User(UserMixin, Model):
    first_name = CharField()
    email = CharField(unique=True)
    password = CharField()

    class Meta:
        database = DATABASE


class Entry(Model):
    user = ForeignKeyField(User, backref="entries")
    title = CharField()
    date = DateTimeField()
    time_spent = IntegerField()
    material = TextField()
    resource = TextField()
    tagfield = TextField()
    slug = TextField(unique=True)

    def test_slug_outstanding(slugtested):
        try:
            Entry.get(Entry.slug == slugtested)
            return True
        except Entry.DoesNotExist:
            return False

    class Meta:
        database = DATABASE
        order_by = ('-date',)


class Tag(Model):
    name = CharField(unique=True)
    entries = ManyToManyField(Entry, backref="tags")

    class Meta:
        database = DATABASE


EntryTag = Tag.entries.get_through_model()


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([Entry, User, Tag, EntryTag], safe=True)
    DATABASE.close()
