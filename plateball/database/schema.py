#! /usr/bin/env python3.5
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

import logging
from peewee import *
from plateball.database import BaseModel

logger = logging.getLogger(__name__)


class League(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    season = IntegerField()

    class Meta:
        indexes = (
            (('name', 'season'), True),
        )


class Team(BaseModel):
    id = IntegerField(primary_key=True)
    team = CharField(1)
    league = ForeignKeyField(League, related_name='teams')
    wins = IntegerField()
    losses = IntegerField()
    runs_for = IntegerField()
    runs_against = IntegerField()

    class Meta:
        indexes = (
            (('team', 'league'), True),
            (('wins', 'losses'), False),
            (('runs_for', 'runs_against'), False),
        )


class Game(BaseModel):
    id = IntegerField(primary_key=True)
    home_team = ForeignKeyField(Team, related_name='home_games')
    away_team = ForeignKeyField(Team, related_name='away_games')
    runs_home = IntegerField()
    runs_away = IntegerField()
    complete = BooleanField()

    class Meta:
        indexes = (
            (("complete",), False),
        )


class Inning(BaseModel):
    id = IntegerField(primary_key=True)
    game = ForeignKeyField(Game, related_name='innings')
    inning = IntegerField()
    runs_home = IntegerField()
    runs_away = IntegerField()
    class Meta:
        indexes = (
            (('inning',), False),
        )

