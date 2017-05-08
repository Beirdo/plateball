#! /usr/bin/env python3.4
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

import logging
from random import shuffle
from plateball.database import Database
from plateball.database.schema import *
from plateball.singleton import Singleton

logger = logging.getLogger(__name__)

class PlateballDatabase(Database, Singleton):
    def __init__(self, filename):
        tables = [League, Team, Game, Inning]
        foreignKeys = {}
        Database.__init__(self, filename, tables, foreignKeys)

    def createLeague(self, name, season):
        item = {
            "name": name,
            "season": season,
        }
        league = League(**item)
        league.save()
        return league

    def createTeams(self, league, teams):
        success = True
        for name in teams:
            item = {
                "team": name,
                "league": league,
                "wins": 0,
                "losses": 0,
                "runs_for": 0,
                "runs_against": 0,
            }
            team = Team(**item)
            team.save()

        return success

    def createGames(self, season):
        leagues = self.getLeagues(season)
        
        games = {league.name: [] for league in leagues}
        
        for league in leagues:
            leagueTeams = league.teams
            nonLeagueTeams = self.getNonLeagueTeams(league)

            for team1 in leagueTeams:
                gameList = games[team1.league.name]
                for team2 in leagueTeams:
                    if team2 == team1:
                        continue
                    gameItem = {
                        "home_team": team1,
                        "away_team": team2,
                    }
                    gameList.append(gameItem)
                    gameList.append(gameItem)
                    gameList.append(gameItem)
                    gameList.append(gameItem)

                for team2 in nonLeagueTeams:
                    if team2 == team1:
                        continue

                    gameItem = {
                        "home_team": team1,
                        "away_team": team2,
                    }
                    gamelist.append(gameItem)
                    games[team2.league.name].append(gameItem)

        for (leagueName, gameList) in games.items():
            shuffle(gameList)
            for item in gameList:
                item.update({
                    "runs_home": 0,
                    "runs_away": 0,
                    "complete": 0,
                })
                game = Game(**item)
                with self.execution_context():
                    game.save()


    def getLeagues(self, season):
        query = League.select().where(League.season == season)
        return query


    def getNonLeagueTeams(self, league):
        query = Team.select().join(League)\
            .where(League.season == league.season,
                   Team.league != league.id)
        return query

    def getNextGames(self, league, limit):
        HomeTeam = Team.alias()
        AwayTeam = Team.alias()
        query = Game.select(Game, HomeTeam, AwayTeam, League) \
            .join(HomeTeam, on=HomeTeam.home_games) \
            .join(League) \
            .switch(Game) \
            .join(AwayTeam, on=AwayTeam.away_games) \
            .where(League.id == league.id,
                   Game.complete == 0).limit(limit)
        return query

    def recordScore(self, gameid, data):
        game = self.getGameById(gameid)
        runs_home = 0
        runs_away = 0
        innings = []
        complete = False
        for (inning, score) in enumerate(data):
            print(inning, score)
            away = score[0]
            if inning < 8 or runs_home <= runs_away:
                # Remember, enumerate starts at 0, this is inning 9+
                home = score[1]
            else:
                home = 0

            item = {
                "game": game,
                "inning": inning + 1,
                "runs_home": home,
                "runs_away": away,
            }
            newInning = Inning(**item)
            innings.append(newInning)

            runs_home += home
            runs_away += away

            if inning >= 8 and runs_home != runs_away:
                # Fat lady has sung, game over
                complete = True
                break

        if complete:
            game.complete = True
            game.runs_home = runs_home
            game.runs_away = runs_away

            homeTeam = game.home_team
            homeTeam.runs_for += runs_home
            homeTeam.runs_against += runs_away
            if runs_home > runs_away:
                homeTeam.wins += 1
            else:
                homeTeam.losses += 1

            awayTeam = game.away_team
            awayTeam.runs_for += runs_away
            awayTeam.runs_against += runs_home
            if runs_away > runs_home:
                awayTeam.wins += 1
            else:
                awayTeam.losses += 1

            with self.execution_context():
                game.save()
                homeTeam.save()
                awayTeam.save()
                for inning in innings:
                    inning.save()
            return True

        logger.error("Game incomplete (id %s)" % gameid)
        return False

    def getGameById(self, gameid):
        query = Game.select().where(Game.id == gameid).get()
        return query

    def getLeagueById(self, leagueid):
        query = League.select().where(League.id == leagueid).get()
        return query
