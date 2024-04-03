# from nba_api.stats.static import teams
# from nba_api.stats.endpoints import leaguegamefinder
# from nba_api.stats.endpoints._base import Endpoint
# from nba_api.stats.library.http import NBAStatsHTTP
# from nba_api.stats.library.parameters import DayOffset, GameDate, LeagueID
# from nba_api.stats.endpoints.teamdashlineups import TeamDashLineups
from datetime import date
import json
import csv
from math import ceil
import math
import string
import time
from weakref import proxy
import requests
from fantasypros import FantasyPros
from structures import CSVFinal, Game, OddsData, Player, Team, OpponentPlayerPosition
from nba_api.stats.endpoints.leaguedashteamstats import LeagueDashTeamStats
from nba_api.stats.endpoints.playergamelogs import PlayerGameLogs

# Today's Score Board
# games = scoreboard.ScoreBoard()


class NBA_Diagnostics:

    def __init__(self, last_n_games : int, OppPlayerPosition : list[OpponentPlayerPosition], dp : list[str], pass_through) -> None:
        self.over_list : list[CSVFinal] = []
        self.under_list : list[CSVFinal] = []
        self.bottom_5_teams : list[Team] = []
        self.top_5_teams : list[Team] = []
        self.all_teams : list[Team] = {}

        # self.ODDSAPIKEY = "3wLm2UXL3pVjmETX2P05vFRQX3WgEnfmLUkdzwd8"
        # self.ODDSAPIKEY = "0dzjbxegxBpPlBCPsSKbMZnjonG3YmM9u6vYa0nwYTI"
        # self.ODDSAPIKEY = "XnB7yI5hOcx2Hb85EvVQ1PT8n1j8GWqQ4zm4T0Nqa4"
        # self.ODDSAPIKEY = "LpBzajHI10St2NKmolOIVMwGtD5EHOhyHq3kdZo6o"
        # self.ODDSAPIKEY = "wVMvWXJsXzJYMiVHEeq0px3co1NEbUzOzye1mJNuFug"
        username = 'spo8qy8rzn'
        password = '5Welf7njwt5d7iuAPL'
        self.proxy = f"http://{username}:{password}@gate.smartproxy.com:7000"
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.day = today.day # DELETE THIS + 3

        self.odds_categories = {
            "PTS": "player_points_over_under",
            "REB": "player_rebounds_over_under",
            "AST": "player_assists_over_under",
            "STL": "player_steals_over_under",
            "TOV": "player_turnovers_over_under",
            "BLK": "player_blocks_over_under",
            "3PM": "player_threes_over_under"
        }
        
        self.last_n_games = last_n_games
        self.today_games : list[Game] = self.getTodayGames() # MAKE SURE TO DELETE +2 FOR TESTING

        if not pass_through:
            self.run(OppPlayerPosition, dp)
        else:
            fp = FantasyPros()
            self.runFP(OppPlayerPosition,fp,dp)

        # else:
        #     for game in self.today_games:
        #         self.calculateL10HitRate()

    def getTodayGames(self) -> list[Game]:

        while True:
            try:
                get_games_prop_odds_string = "https://api.prop-odds.com/beta/games/nba?date=%d-%02d-%02d&api_key=%s&tz=America/Chicago"%(self.year,self.month,self.day, self.ODDSAPIKEY)
                today_game_prop_odds_games = requests.get(get_games_prop_odds_string)
                prop_odds_games_list =  sorted(today_game_prop_odds_games.json()["games"], key= lambda k: k["home_team"])

                all_today_games : list[Game] = []
                for game in prop_odds_games_list:
                    curr_game = Game(game, self.proxy)
                    all_today_games.append(curr_game)
                return all_today_games  
            except:
                if today_game_prop_odds_games.status_code == 401:
                    print("401 Error")
                    break
                time.sleep(2)
                continue


    def addPlayerToFinal(self, game : Game, position : OpponentPlayerPosition, data_points : tuple[str]):

        homeTeamFullName = game.homeTeamAssociation.team_name
        awayTeamFullName = game.awayTeamAssociation.team_name
        odd_data = self.getOddsData(data_points[0], game.gameId)
    
        if (odd_data is None) or (awayTeamFullName not in self.bottom_5_teams and awayTeamFullName not in self.top_5_teams and \
             homeTeamFullName not in self.bottom_5_teams and homeTeamFullName not in self.top_5_teams):
            return None

        odd_data = odd_data.market_outcomes

        if homeTeamFullName in self.bottom_5_teams:
            self.evaluatePlayers(game.awayPlayers, game, False, True, position, data_points, odd_data)
        elif homeTeamFullName in self.top_5_teams:
            self.evaluatePlayers(game.awayPlayers, game, False, False, position, data_points, odd_data)

        if awayTeamFullName in self.bottom_5_teams:
            self.evaluatePlayers(game.homePlayers, game, True, True, position, data_points, odd_data)
        elif awayTeamFullName in self.top_5_teams:
            self.evaluatePlayers(game.homePlayers, game, True, False, position, data_points, odd_data)
    
    def evaluatePlayers(self, players_list, game : Game, away, bottom_5, position : OpponentPlayerPosition, data_points : tuple[str], odd_data):
        for player in players_list:
            playerPosition = player['POSITION']
            playerFullName = player['PLAYER_FIRST_NAME']+" "+player['PLAYER_LAST_NAME']
            playerID = player['PERSON_ID']

            if playerPosition and playerPosition in position.value and playerPosition != '':
                opposingTeamName = game.homeTeamAssociation.team_name if not away else game.awayTeamAssociation.team_name
                otherTeamName = game.homeTeamAssociation.team_name if away else game.awayTeamAssociation.team_name
                teamOBJ = self.all_teams[opposingTeamName]

                if bottom_5:
                    if playerFullName in odd_data:
                        res = odd_data[playerFullName]
                        for prop_player_odd in res:
                            if prop_player_odd.OVER:
                                csv_final_obj = CSVFinal(opposingTeamName, teamOBJ.team_id, round(teamOBJ.association[data_points[0]]), teamOBJ.association[data_points[1]], data_points[0], playerPosition, playerFullName, otherTeamName, prop_player_odd.handicap , int(prop_player_odd.odds), True, playerID)
                                csv_final_obj.LNHitRate = self.calculateLastNHitRate(csv_final_obj, self.last_n_games)
                                self.over_list.append(csv_final_obj.listVersion())
                else:
                    if playerFullName in odd_data:
                        res = odd_data[playerFullName]
                        for prop_player_odd in res:
                            if not prop_player_odd.OVER:
                                csv_final_obj = CSVFinal(opposingTeamName, teamOBJ.team_id, round(teamOBJ.association[data_points[0]]), teamOBJ.association[data_points[1]], data_points[0], playerPosition, playerFullName, otherTeamName, prop_player_odd.handicap , int(prop_player_odd.odds), False, playerID)
                                csv_final_obj.LNHitRate = self.calculateLastNHitRate(csv_final_obj, self.last_n_games)
                                self.under_list.append(csv_final_obj.listVersion())

    def printBottom5Top5(self, data_points : list[str], bottom_5_teams : list[Team], top_5_teams : list[Team]):

        print()
        print("************************************")
        print("***********BOTTOM 5 TEAMS***********")
        for bottom_team in bottom_5_teams:
            print(bottom_team.team_name)
            for dp in data_points:
                print(dp," - ",bottom_team.association[dp])
            print()
        print("************************************")
        print()
        print("************************************")
        print("***********TOP 5 TEAMS**************")
        for top_team in top_5_teams:
            print(top_team.team_name)
            for dp in data_points:
                print(dp," - ",top_team.association[dp])
            print()
        print("************************************")
        print()

    def getTeamStatsAgainstPlayer(self, playerPosition : OpponentPlayerPosition, last_n_games : string) -> LeagueDashTeamStats:
        
        time.sleep(1)
        while True:
            try:
                season_game_stats = LeagueDashTeamStats(
                measure_type_detailed_defense='Opponent',
                per_mode_detailed="PerGame",
                player_position_abbreviation_nullable = playerPosition.value[0],
                season='2023-24',
                last_n_games=last_n_games,
                proxy=self.proxy
                )
                break
            except:
                time.sleep(1)
                continue

        return season_game_stats
    
    def getOddsData(self, data_point : string, game_id: string):
        if data_point == "FG3M":
            data_point = "3PM"
        
        category = self.odds_categories[data_point]

        odds_get_request_string = "https://api.prop-odds.com/beta/odds/"+game_id+"/"+category+"?api_key="+self.ODDSAPIKEY
        response = requests.get(odds_get_request_string)
        if response.status_code == 200:
            odds_json_data = response.json()
            odds_data = OddsData(odds_json_data, data_point)
            odds_data.getOdds("draftkings", -150, 150)
            odds_data.getOdds("fanduel", -150, 150)
            return odds_data

        return None
    
    def generateCSV(self, csv_name, csv_data, pass_thru):
        
        if not pass_thru:
            header = ["Team","Defense Rank","Stat","Position","Opposing Player", "Opposing Player Team", "PRJ Line","Odds", "L"+str(self.last_n_games)+" Hit Rate"]
            with open(csv_name+"_"+str(self.year)+"_"+str(self.month)+"_"+str(self.day)+".csv", 'w') as csvFile: 
                    # creating a csv writer object 
                    csvwriter = csv.writer(csvFile) 
                        
                    # writing the fields 
                    csvwriter.writerow(header) 
                    
                    # writing the data rows 
                    csvwriter.writerows(csv_data)
                
            csvFile.close()

    def calculateLastNHitRate(self, PickData, last_n):

        # active_streak_only = "Y"
        # last_n = str(5)
        time.sleep(1)
        while True:
            try:
                last_n_games = []

                gst_stat_finder = PlayerGameLogs(player_id_nullable=PickData.playerID, last_n_games_nullable=last_n, season_nullable= "2023-24",proxy=self.proxy)
                if gst_stat_finder is not None:
                    last_n_games = gst_stat_finder.get_normalized_dict()
                else:
                    print(gst_stat_finder)
                
                proj_line = PickData.handicap
                hits = 0

                if PickData.opposingTeamCriteriaDP == "3PM":
                    PickData.opposingTeamCriteriaDP = "FG3M"

                if PickData.betOverUnder:
                    for game_data in last_n_games['PlayerGameLogs']:
                        if game_data["MIN"] > 5:
                            if game_data[PickData.opposingTeamCriteriaDP] > math.floor(proj_line):
                                hits += 1
                    return str(int((hits/self.last_n_games)*100))+"%"
                else:
                    for game_data in last_n_games['PlayerGameLogs']:
                        if game_data["MIN"] > 5:
                            if game_data[PickData.opposingTeamCriteriaDP] < math.ceil(proj_line):
                                hits += 1
                    return str(100-int((hits/self.last_n_games)*100))+"%"   
            except:
                time.sleep(1)
                continue

    def runFP(self,OppPlayerPosition : list[OpponentPlayerPosition], fp : FantasyPros, dp):
        data = self.getTeamStatsAgainstPlayer(OppPlayerPosition[0], str(self.last_n_games))
        team_stats_data = data.data_sets[0].data['data']

        for position in OppPlayerPosition:
            for stat in dp:
                data_point_rank = stat + "_RANK"
                self.bottom_5_teams, self.top_5_teams, self.all_teams = fp.sortByCriteria(stat,position.value, team_stats_data)
                for tg in self.today_games:
                    tg.setTeams(self.all_teams[tg.homeTeamFullName],self.all_teams[tg.awayTeamFullName])
                    self.addPlayerToFinal(tg,position, (stat, data_point_rank))
            self.all_teams = {}
        
 
        lastn_str = "season" if self.last_n_games == 0 else "last"+str(self.last_n_games)
        self.generateCSV("over_fantasy_bet_"+lastn_str+"_picks", self.over_list, False)
        self.generateCSV("under_fantasy_bet_"+lastn_str+"_picks", self.under_list, False)
                

    def run(self, OppPlayerPosition, data_point) -> None:
        
        for player_position in OppPlayerPosition:

            self.playerPosition = player_position       
            data = self.getTeamStatsAgainstPlayer(self.playerPosition, str(self.last_n_games))
            team_stats_data = data.data_sets[0].data['data']

            for v in team_stats_data:
                team_obj = Team(v)
                self.all_teams[v[1]] = team_obj
            
            for game in self.today_games:
                game.setTeams(self.all_teams[game.homeTeamFullName], self.all_teams[game.awayTeamFullName])

            for stat in data_point:
                data_point_rank = stat + "_RANK"
                self.bottom_5_teams = []
                self.top_5_teams = []
                for team_name, team_obj in self.all_teams.items():
                    if team_obj.association[data_point_rank] <= 5:
                        self.top_5_teams.append(team_name)
                    elif team_obj.association[data_point_rank] >= len(team_stats_data) - 4:
                        self.bottom_5_teams.append(team_name)
                
                for tg in self.today_games:
                    self.addPlayerToFinal(tg, self.playerPosition, (stat, data_point_rank))
            
            self.all_teams : list[Team] = {}
            
        self.over_list.sort(key = lambda x : x[0])
        self.under_list.sort(key = lambda x : x[0])
        
        lastn_str = "season" if self.last_n_games == 0 else "last"+str(self.last_n_games)
        self.generateCSV("over_bet_"+lastn_str+"_picks", self.over_list, False)
        self.generateCSV("under_bet_"+lastn_str+"_picks", self.under_list, False)

        print("ITR DONE")
    
if __name__ == '__main__': 
    nba_inst = NBA_Diagnostics(15,[OpponentPlayerPosition.CENTER, OpponentPlayerPosition.GUARD,  OpponentPlayerPosition.FORWARD], ["PTS","REB","AST"], True)
# "STL","TOV","BLK","3PM"


# center_inst.getOddsData("PTS","9907407880bcd9aa9517c4ac7b780dd8")



# today_games = scoreboard.ScoreBoard().games.get_dict()
# for gameId in today_games:
#     for gameDetails in today_games:
#         homeTeamId = gameDetails['homeTeam']['teamId']
#         awayTeamId = gameDetails['awayTeam']['teamId']
#         print()

# df = stats.get_data_frames()[0]

# last_10_game_stats = LeagueDashTeamStats(
#     measure_type_detailed_defense='Opponent',
#     per_mode_detailed='PerGame',
#     player_position_abbreviation_nullable='C',
#     season='2023-24',
#     last_n_games='10'
# )
# last_5_game_stats = LeagueDashTeamStats(
#     measure_type_detailed_defense='Opponent',
#     per_mode_detailed='PerGame',
#     player_position_abbreviation_nullable='C',
#     season='2023-24',
#     last_n_games='5'
# )


# game_lineup = TeamDashLineups(team_id = '1610612738', opponent_team_id='1610612751', game_id_nullable = '0022300771')
# print(game_lineup.get_json())

# nba_teams = teams.get_teams()
# # Select the dictionary for the Celtics, which contains their team ID
# celtics = [team for team in nba_teams if team['abbreviation'] == 'BOS'][0]
# celtics_id = celtics['id']

# nba_teams = teams.get_teams()
# Select the dictionary for the Celtics, which contains their team ID
# celtics = [team for team in nba_teams if team['abbreviation'] == 'BOS'][0]
# celtics_id = celtics['id']

# date_str = str(date.today()) # '2024-02-12'


# ep = Endpoint()
# future_games_inst = ScoreboardV2(ep)
# future_games_inst.get_request()
# for k,v in future_games_inst.DataSet.data:
#     print(k," - ",v)


# #Query to get all Games - Only 1 API Call (As of now) - Will most likely be first query before rest run.
# #Provides all else to call the rest of the APIs
# gamefinder = leaguegamefinder.LeagueGameFinder()

# games = gamefinder.get_data_frames()[0]
# temp = games[games.GAME_DATE.str.contains('2024-02-13')]
# # temp = games[games.SEASON_ID.str.contains('2024')]
# print(games.head())


#TOP 5 & Bottom 5
# "TEAM_ID"
# "TEAM_NAME"

# "OPP_REB_RANK",
# "OPP_AST_RANK",
# "OPP_PTS_RANK",
#note - query directly since it is JSON, or use dataframe from pandas