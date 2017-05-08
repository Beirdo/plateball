#! /usr/bin/env python3.5
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

import argparse
import json
import logging
import os
import sys
import io

import qrcode
from reportlab.platypus import SimpleDocTemplate, Table, Spacer, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black, red, blue

from plateball.loggingcore import setupLogging, debugLogging
from plateball.database.access import PlateballDatabase

class Action(object):
    def __init__(self, db, args):
        self.db = db
        self.args = args

    def doAction(self):
        func = getattr(self, "mode_%s" % self.args.mode)
        if not func or not hasattr(func, '__call__'):
            logger.error("No action defined for mode %s" % self.args.mode)
            sys.exit(1)
        return func()

    def mode_league(self):
        if not self.args.name or self.args.season is None:
            logger.error("League mode needs --name and --season")
            sys.exit(1)

        return self.db.createLeague(self.args.name, self.args.season)

    def mode_teams(self):
        if self.args.league is None or not self.args.teams:
            logger.error("Teams mode needs --league and --teams")
            sys.exit(1)

        teams = [item.upper() for item in self.args.teams]
        league = self.db.getLeagueById(self.args.league)
        return self.db.createTeams(league, teams)

    def mode_games(self):
        if self.args.season is None:
            logger.error("Games mode needs --season")
            sys.exit(1)

        return self.db.createGames(self.args.season)

    def mode_print_games(self):
        if self.args.league is None:
            logger.error("Print games mode needs --league")
            sys.exit(1)

        league = self.db.getLeagueById(self.args.league)
        limit = self.args.count
        if not limit:
            limit = 100
        games = self.db.getNextGames(league, limit)

        story = []

        outRow = Table([["", "", ""]], colWidths=3 * [0.3*cm],
                       rowHeights=1 * [0.3*cm], 
                       style=[("GRID", (0, 0), (-1, -1), 0.5, red),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ])
        outCell = Table([[outRow], [""]], colWidths=1 * [1*cm],
                        rowHeights=[0.4*cm, 0.6*cm],
                        style=[("BOX", (0, 0), (-1, -1), 1, black),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ])

        for game in games:
            row0 = ["L: %s\nG: %s" % (game.home_team.league.id, game.id)]
            row0.extend([str(item) for item in range(1,15)])
            row0.append("FIN")
            row1 = [game.away_team.team]
            row1.extend(14 * [outCell])
            row1.append("")
            row2 = [game.home_team.team]
            row2.extend(14 * [outCell])
            row2.append("")
            scoreTable = Table([row0, row1, row2], colWidths=16 * [1*cm],
                  rowHeights=3 * [1*cm],
                  style=[("GRID", (0, 0), (-1, -1), 1, black),
                         ("GRID", (-1, 1), (-1, -1), 2, blue),
                         ("TOPPADDING", (0, 0), (-1, -1), 0),
                         ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                         ("LEFTPADDING", (0, 0), (-1, -1), 0),
                         ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                         ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                         ("FONTSIZE", (0, 0), (0, 0), 5),
                         ("LINEBEFORE", (10, 0), (10, -1), 2, black),
                        ])

            qr = qrcode.QRCode(version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=100, border=4)
            qr.add_data("Game ID: %s" % game.id)
            qr.make(fit=True)
            qrimg = qr.make_image()
            qrbuf = io.BytesIO()
            qrimg.save(qrbuf, format="png")

            table = Table([[Image(qrbuf, 1*inch, 1*inch), scoreTable]],
                          colWidths=[3*cm, 16*cm],
                          rowHeights=1 * [3*cm],
                          style=[("BOX", (0, 0), (-1, -1), 2, black),
                                 ("TOPPADDING", (0, 0), (-1, -1), 0),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                 ("ALIGN", (0, 0), (0, 0), "CENTER"),
                                 ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                        ])
            story.extend([Spacer(width=1, height=0.1*inch), table])
            
        doc = SimpleDocTemplate("plateball.pdf", pagesize=letter)
        doc.build(story)

        return True

    def mode_standings(self):
        if self.args.league is None:
            logger.error("Standings mode needs --league")
            sys.exit(1)

        league = self.db.getLeagueById(self.args.league)
        teams = league.teams
        scores = []
        for team in teams:
            item = {
                "team": team.team,
                "wins": team.wins,
                "losses": team.losses,
                "plusminus": team.wins - team.losses,
                "runs_for": team.runs_for,
                "runs_against": team.runs_against,
            }
            scores.append(item)

        scores.sort(key=lambda item: item['plusminus'], reverse=True)
        top = scores[0]['plusminus']
        for score in scores:
            score['gamesbehind'] = float(top - score['plusminus']) / 2.0

        print("Standings for league #%s" % self.args.league)
        print("%4s %4s %4s %5s %5s %s" % ("Team", "W", "L", "RF", "RA", "GB"))
        print("---------------------------------")
        for score in scores:
            print("%4s %4s %4s %5s %5s %s" % 
                  (score['team'], score['wins'], score['losses'],
                   score['runs_for'], score['runs_against'],
                   score['gamesbehind']))

        return True
        
    def mode_record_scores(self):
        if not self.args.scores:
            logger.error("Record Scores mode needs --scores")
            sys.exit(1)

        with open(self.args.scores, "r") as f:
            data = json.load(f)

        count = 0
        errors = 0

        for gameData in data:
            count += 1
            gameid = gameData.get('id', None)
            if not gameid:
                logger.warning("No Game ID in record #%s, skipping" % count)
                errors += 1
                continue

            scores = gameData.get('scores', None)
            if not isinstance(scores, list):
                logger.warning("Invalid scores info in record #%2, skipping" %
                               count)
                errors += 1
                continue

            results = self.db.recordScore(gameid, scores)
            if not results:
                logger.warning("Incomplete game in record #%s, skipping" %
                               count)
                errors += 1
                continue

        return errors



if __name__ == "__main__":
    setupLogging(logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Plateball admin")
    parser.add_argument('--debug', action="store_true")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create_league', action="store_const", 
                       const="league", dest="mode",
                       help="Create a new league/season")
    group.add_argument('--create_teams', action="store_const", 
                       const="teams", dest="mode",
                       help="Create a new set of teams for a league season")
    group.add_argument('--create_games', action="store_const", 
                       const="games", dest="mode",
                       help="Create a new set of games for a season")
    group.add_argument('--print_games', action="store_const", 
                       const="print_games", dest="mode",
                       help="Print a outstanding games for a season")
    group.add_argument('--record_scores', action="store_const", 
                       const="record_scores", dest="mode",
                       help="Record scores for a league season")
    group.add_argument('--standings', action="store_const", 
                       const="standings", dest="mode",
                       help="Output standings for a particular league season")
    parser.add_argument('--name', help="League Name")
    parser.add_argument('--season', type=int, help="Season number")
    parser.add_argument('--league', type=int, help="League ID")
    parser.add_argument('--teams', help="Teams")
    parser.add_argument('--count', type=int, help="Number of games to print")
    parser.add_argument('--scores', help="Score file (JSON)")
    args = parser.parse_args()

    debugLogging(args.debug)

    basedir = os.path.realpath(os.path.dirname(sys.argv[0]))
    dbfile = os.path.join(basedir, "plateball.db")

    db = PlateballDatabase(dbfile)
    action = Action(db, args)
    result = action.doAction()

