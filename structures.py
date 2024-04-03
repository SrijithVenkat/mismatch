from collections import defaultdict
from enum import Enum
from sqlite3 import Time
from threading import Timer
from nba_api.stats.endpoints import PlayerIndex

class Team:
    def __init__(self, data) -> None:
        self.team_id = data[0]
        self.team_name = data[1]
        self.games_played = data[2]
        self.wins = data[3]
        self.losses = data[4]
        self.win_percentage = data[5]
        self.minutes = data[6]
        self.opponent_field_goal_made = data[7]
        self.opponent_field_goal_attempted = data[8]
        self.opponent_field_goal_percentage = data[9]
        self.opponent_field_goal_3_made = data[10]
        self.opponent_field_goal_3_attempted = data[11]
        self.opponent_field_goal_3_percentage = data[12]
        self.opponent_free_throw_made = data[13]
        self.opponent_free_throw_attempted = data[14]
        self.opponent_free_throw_percentage = data[15]
        self.opponent_offensive_rebounds = data[16]
        self.opponent_defensive_rebounds = data[17]
        self.opponent_rebounds = data[18]
        self.opponent_assists = data[19]
        self.opponent_turnovers = data[20]
        self.opponent_steals = data[21]
        self.opponent_blocks = data[22]
        self.opponent_blocks_against = data[23]
        self.opponent_personal_fouls = data[24]
        self.opponent_personal_fouls_drawn = data[25]
        self.opponent_points = data[26]
        self.plus_minus_odds = data[27]
        self.games_played_rank = data[28]
        self.win_rank = data[29]
        self.loss_rank = data[30]
        self.win_percentage_rank = data[31]
        self.minutes_rank = data[32]
        self.opponent_field_goal_made_rank = data[33]
        self.opponent_field_goal_attempted_rank = data[34]
        self.opponent_field_goal_percentage_rank = data[35]
        self.opponent_field_goal_3_made_rank = data[36]
        self.opponent_field_goal_3_attempted_rank = data[37]
        self.opponent_field_goal_3_percentage_rank = data[38]
        self.opponent_free_throw_made_rank = data[39]
        self.opponent_free_throw_attempted_rank = data[40]
        self.opponent_free_throw_percentage_rank = data[41]
        self.opponent_offensive_rebounds_rank = data[42]
        self.opponent_defensive_rebounds_rank = data[43]
        self.opponent_rebounds_rank = data[44]
        self.opponent_assists_rank = data[45]
        self.opponent_turnovers_rank = data[46]
        self.opponent_steals_rank = data[47]
        self.opponent_blocks_rank = data[48]
        self.opponent_blocks_attempted_rank = data[49]
        self.opponent_personal_fouls_rank = data[50]
        self.opponent_personal_fouls_drawn_rank = data[51]
        self.opponent_points_rank = data[52]
        self.plus_minus_odds_rank = data[53]

        self.association = \
        {
            "TEAM_ID" : self.team_id,
            "TEAM_NAME" : self.team_name,
            "GP" : self.games_played,
            "W" : self.wins,
            "L" : self.losses,
            "W_PCT" : self.win_percentage,
            "MIN" : self.minutes,
            "FGM" : self.opponent_field_goal_made,
            "FGA" : self.opponent_field_goal_attempted,
            "FG_PCT" : self.opponent_field_goal_percentage,
            "FG3M" : self.opponent_field_goal_3_made,
            "FG3A" : self.opponent_field_goal_3_attempted,
            "FG3_PCT" : self.opponent_field_goal_3_percentage,
            "FTM" : self.opponent_free_throw_made,
            "FTA" : self.opponent_free_throw_attempted,
            "FT_PCT" : self.opponent_free_throw_percentage,
            "OREB": self.opponent_offensive_rebounds,
            "DREB" : self.opponent_defensive_rebounds,
            "REB" : self.opponent_rebounds,
            "AST" : self.opponent_assists,
            "TOV" : self.opponent_turnovers,
            "STL" : self.opponent_steals,
            "BLK" : self.opponent_blocks,
            "BLKA" : self.opponent_blocks_against,
            "PF" : self.opponent_personal_fouls,
            "PFD" : self.opponent_personal_fouls_drawn,
            "PTS" : self.opponent_points,
            "PLUS_MINUS" : self.plus_minus_odds,
            "GP_RANK" : self.games_played_rank,
            "W_RANK" : self.win_rank,
            "L_RANK" : self.loss_rank,
            "W_PCT_RANK" : self.win_percentage_rank,
            "MIN_RANK" : self.minutes_rank,
            "FGM_RANK" : self.opponent_field_goal_made_rank,
            "FGA_RANK" : self.opponent_field_goal_attempted_rank,
            "FG_PCT_RANK" : self.opponent_field_goal_percentage_rank,
            "FG3M_RANK" : self.opponent_field_goal_3_made_rank,
            "FG3A_RANK" : self.opponent_field_goal_3_attempted_rank,
            "FG3_PCT_RANK" : self.opponent_field_goal_3_percentage_rank,
            "FTM_RANK" : self.opponent_free_throw_made_rank,
            "FTA_RANK" : self.opponent_free_throw_attempted_rank,
            "FT_PCT_RANK" : self.opponent_free_throw_percentage_rank,
            "OREB_RANK" : self.opponent_offensive_rebounds_rank,
            "DREB_RANK" : self.opponent_defensive_rebounds_rank,
            "REB_RANK" : self.opponent_rebounds_rank,
            "AST_RANK" : self.opponent_assists_rank,
            "TOV_RANK" : self.opponent_turnovers_rank,
            "STL_RANK" : self.opponent_steals_rank,
            "BLK_RANK" : self.opponent_blocks_rank,
            "BLKA_RANK" : self.opponent_blocks_attempted_rank,
            "PF_RANK" : self.opponent_personal_fouls_rank,
            "PFD_RANK" : self.opponent_personal_fouls_drawn_rank,
            "PTS_RANK" : self.opponent_points_rank,
            "PLUS_MINUS_RANK" : self.plus_minus_odds_rank
        }

class Game:

    def __init__(self, data_dict, proxy) -> None:
        self.gameId = data_dict['game_id']
        self.homeTeamFullName = data_dict['home_team']
        self.awayTeamFullName = data_dict['away_team']
        self.startTimestamp = data_dict['start_timestamp']    

        self.homeTeamAssociation : Team = None
        self.awayTeamAssociation : Team = None

        self.homePlayers = []
        self.awayPlayers = []
        self.proxy = proxy
  
    def populatePlayers(self):
        if len(self.homePlayers) == 0:
            self.homePlayers = PlayerIndex(team_id_nullable=self.homeTeamAssociation.team_id, proxy=self.proxy).get_normalized_dict()['PlayerIndex']
        if len(self.awayPlayers) == 0:
            self.awayPlayers = PlayerIndex(team_id_nullable=self.awayTeamAssociation.team_id, proxy=self.proxy).get_normalized_dict()['PlayerIndex']
    
    def setTeams(self, home_teamOBJ, away_teamOBJ):
        self.homeTeamAssociation = home_teamOBJ
        self.awayTeamAssociation = away_teamOBJ
        if len(self.homePlayers) == 0 or len(self.awayPlayers) == 0 and self.homeTeamAssociation and self.awayTeamAssociation:
            self.populatePlayers()

class Player:
    def __init__(self, data_dict) -> None:
        self.playerId = data_dict['personId']
        self.playerTeamId = data_dict['teamId']
        self.playerFirstName = data_dict['firstName']
        self.playerLastName = data_dict['lastName']
        self.playerFullName = data_dict['playerName']
        self.playerLineupStatus = data_dict['lineupStatus']
        self.playerPosition = data_dict['position']
        self.rosterStatus = data_dict['rosterStatus']
        self.timestamp = data_dict['timestamp']

class OddsData:

    def __init__(self, data_dict, data_point) -> None:
        self.game_id = data_dict['game_id']
        self.fanduel = None
        self.draftkings = None
        self.data_point = data_point
        self.pinnacle = None
        self.caesars = None
        self.betmgm = None
        self.barstool = None
        self.pointsbet = None
        self.fliff = None
        self.betrivers = None
        for bookie in data_dict['sportsbooks']:
            if bookie["bookie_key"] == 'draftkings':
                self.draftkings = bookie
            if bookie["bookie_key"] == 'fanduel':
                self.fanduel = bookie
            if bookie["bookie_key"] == 'pinnacle':
                self.pinnacle = bookie 
            if bookie["bookie_key"] == 'casears':
                self.caesars = bookie
            if bookie["bookie_key"] == 'betmgm':
                self.betmgm = bookie
            if bookie["bookie_key"] == 'barstool':
                self.barstool = bookie
            if bookie["bookie_key"] == 'betrivers':
                self.betrivers = bookie
            if bookie["bookie_key"] == 'pointsbet':
                self.pointsbet = bookie
            if bookie["bookie_key"] == 'fliff':
                self.fliff = bookie
        
        self.market_outcomes = {}
    
        self.bookie_association = { \
            "fanduel" : self.fanduel,
            "draftkings" : self.draftkings,
            "pinnacle" : self.pinnacle,
            "caesars" : self.caesars,
            "betmgm" : self.betmgm,
            "barstool" : self.barstool,
            "betrivers" : self.betrivers,
            "pointsbet" : self.pointsbet,
            "fliff" : self.fliff,
        }

    def getOdds(self, bookie_key, LOWER_BOUND, UPPER_BOUND):
        
        if self.bookie_association[bookie_key] is not None:
            for outcome in self.bookie_association[bookie_key]['market']['outcomes']:
                player_name = outcome["participant_name"]
                odds = outcome["odds"]
                desc = outcome["description"]
                if odds >= LOWER_BOUND and odds <= UPPER_BOUND and "Alt" not in desc:
                    if player_name in self.market_outcomes:
                        self.market_outcomes[player_name].append(StatOdds(outcome, player_name, odds, desc, bookie_key))
                    else:
                        self.market_outcomes[player_name] = [StatOdds(outcome, player_name, odds, desc, bookie_key)]
            for player in self.market_outcomes:
                self.market_outcomes[player].sort(key= lambda x : x.odds)
            return True
        return False
    
class StatOdds:
    def __init__(self, data_dict, player_name, odds, desc, bookie_key) -> None:
        self.player_name = player_name
        self.odds = odds
        self.handicap = data_dict['handicap']
        self.props_player_id = data_dict['participant']
        self.name = data_dict['name']
        self.timestamp = data_dict['timestamp']
        self.OVER = True if "Over" in data_dict['name'] else False
        self.description = desc
        self.bookie_key = bookie_key

class Line:
    def __init__(self, player_id : int, player_name : str, line : float) -> None:
        self.player_id = player_id
        self.player_name = player_name
        self.line = line

class LinesData:

    def __init__(self, data_dict, data_point) -> None:
        self.game_id = data_dict['game_id']
        self.data_point = data_point
        self.draftkings = None
        self.prizepicks  = None
        self.underdog = None
        for bookie in data_dict['fantasy_books']:
            # if bookie["bookie_key"] == 'underdog':
            #     self.underdog = bookie
            # if bookie["bookie_key"] == 'draftkings':
            #     self.draftkings = bookie
            if bookie["bookie_key"] == 'prizepicks':
                self.prizepicks = bookie 
                break
        
        self.bookie_association = { \
            # "draftkings" : self.draftkings,
            "prizepicks" : self.prizepicks,
            # "underdog" : self.underdog,
        }

        self.setLines()

    def setLines(self):
        for bookie_key in self.bookie_association:
            if self.bookie_association[bookie_key] is not None:
                for line in self.bookie_association[bookie_key]['market']['lines']:
                    player_name = line["participant_name"]
                    player_id = line["participant"]
                    line = line["line"]

                    self.bookie_association[bookie_key][player_name] = Line(player_id, player_name, line)

        # if self.prizepicks is not None:
        #     for player in self.prizepicks.items():

class LineCSVFinal: 

    def __init__(self, homeTeamFullName, awayTeamFullName, away, playerName, fantasy_line, fantasy_sportsbook, data_point, odds, bookie_name, over) -> None:
        self.away = away
        self.playerTeamName = None
        self.otherTeamName = None
        self.playerName = playerName
        if self.away:
            self.playerTeamName = awayTeamFullName
            self.otherTeamName = homeTeamFullName
        else:
            self.playerTeamName = homeTeamFullName
            self.otherTeamName = awayTeamFullName
        self.fantasy_line = fantasy_line
        self.fantasy_sportsbook = fantasy_sportsbook
        self.odds = odds
        self.bookie_name = bookie_name
        self.over = over
        self.data_point = data_point
        self.LNHitRate = None

    def listVersion(self):
        return [self.otherTeamName, self.playerTeamName, self.playerName, self.fantasy_line, self.fantasy_sportsbook, self.data_point, self.odds, self.bookie_name, "OVER" if self.over else "UNDER", self.LNHitRate if self.LNHitRate else ""]

class CSVFinal:
    def __init__(self, opposingTeam, opposingTeamId, opposingTeamCriteriaValue, opposingTeamCriteriaRank, opposingTeamCriteriaDP, position, player : Player, teamName,  handicap : float,  odds: int, overUnder : bool, playerID, L10HitRate = "") -> None:
        self.opposingTeam  = opposingTeam
        self.opposingTeamId  = opposingTeamId
        self.opposingTeamCriteriaValue = opposingTeamCriteriaValue
        self.opposingTeamCriteriaRank = opposingTeamCriteriaRank
        self.opposingTeamCriteriaDP = opposingTeamCriteriaDP

        self.playerPosition = position
        self.playerName = player
        self.playerTeamName = teamName

        self.handicap = handicap
        self.odds = odds
        self.betOverUnder = overUnder
        self.playerID = playerID
        self.LNHitRate = L10HitRate
    
    def listVersion(self):
        return [self.opposingTeam, self.opposingTeamCriteriaRank, self.opposingTeamCriteriaDP, self.playerPosition, self.playerName, self.playerTeamName, self.handicap, self.odds, self.LNHitRate]

class OpponentPlayerPosition(Enum):

    CENTER = ("C")
    FORWARD = ("F","SF","PF")
    GUARD = ("G","SG","PG")

class FantasyProsCSVFinal:
    def __init__(self, opposingTeam, opposingTeamCriteriaRank, opposingTeamCriteriaDP, position, player : Player, teamName,  handicap : float,  odds: int, L10HitRate = "") -> None:
        self.opposingTeam  = opposingTeam
        self.opposingTeamCriteriaRank = opposingTeamCriteriaRank
        self.opposingTeamCriteriaDP = opposingTeamCriteriaDP

        self.playerPosition = position
        self.playerName = player
        self.playerTeamName = teamName

        self.handicap = handicap
        self.odds = odds
        self.L10HitRate = L10HitRate
    
    def listVersion(self):
        return [self.opposingTeam, self.opposingTeamCriteriaRank, self.opposingTeamCriteriaDP, self.playerPosition, self.playerName, self.playerTeamName, self.handicap, self.odds, self.L10HitRate]
