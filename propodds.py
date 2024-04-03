from structures import Game, Line, LineCSVFinal, LinesData, OddsData, Team, OpponentPlayerPosition
import time, string, csv, math
from nba_api.stats.endpoints.leaguedashteamstats import LeagueDashTeamStats
from nba_api.stats.endpoints.playergamelogs import PlayerGameLogs
import requests
from datetime import date

class PropOdds:

    def __init__(self, dp) -> None:
        # self.ODDSAPIKEY = "3wLm2UXL3pVjmETX2P05vFRQX3WgEnfmLUkdzwd8"
        # self.ODDSAPIKEY = "0dzjbxegxBpPlBCPsSKbMZnjonG3YmM9u6vYa0nwYTI"
        # self.ODDSAPIKEY = "XnB7yI5hOcx2Hb85EvVQ1PT8n1j8GWqQ4zm4T0Nqa4"
        # self.ODDSAPIKEY = "LpBzajHI10St2NKmolOIVMwGtD5EHOhyHq3kdZo6o"
        self.ODDSAPIKEY = "wVMvWXJsXzJYMiVHEeq0px3co1NEbUzOzye1mJNuFug"
        username = 'spo8qy8rzn'
        password = '5Welf7njwt5d7iuAPL'
        self.proxy = f"http://{username}:{password}@gate.smartproxy.com:10003"
        self.all_teams = {}
        self.odds_categories = {
            "PTS": "player_points_over_under",
            "REB": "player_rebounds_over_under",
            "AST": "player_assists_over_under",
            "STL": "player_steals_over_under",
            "TOV": "player_turnovers_over_under",
            "BLK": "player_blocks_over_under",
            "3PM": "player_threes_over_under"
        }
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.day = today.day # DELETE THIS + 3
        self.last_n_games = 10
        
        data = self.getTeamStatsAgainstPlayer("G", str(self.last_n_games))
        team_stats_data = data.data_sets[0].data['data']

        for v in team_stats_data:
            team_obj = Team(v)
            self.all_teams[v[1]] = team_obj

        self.today_games : list[Game] = self.getTodayGames() # MAKE SURE TO DELETE +2 FOR TESTING
        self.mismatches : list[LineCSVFinal] = []
        
        for tg in self.today_games:
            tg.setTeams(self.all_teams[tg.homeTeamFullName],self.all_teams[tg.awayTeamFullName])
            for stat in dp:
                odds_data = self.getOddsData(stat, tg.gameId)
                if odds_data is not None:
                    odds_data = odds_data.market_outcomes
                    linesData = self.getLines(stat, tg.gameId)
                    if linesData is not None:
                        self.compareData(tg, linesData, odds_data, stat)
                    else:
                        continue
                else: 
                    continue

            
        self.generateCSV("mismatches",self.mismatches)


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
                if today_game_prop_odds_games.status_code == 401 or today_game_prop_odds_games.status_code == 403:
                    break
                time.sleep(2)
                continue
        
        return []

    def getOddsData(self, data_point : string, game_id: string) -> OddsData:
        
        category = self.odds_categories[data_point]

        odds_get_request_string = "https://api.prop-odds.com/beta/odds/"+game_id+"/"+category+"?api_key="+self.ODDSAPIKEY
        response = requests.get(odds_get_request_string)
        if response.status_code == 200:
            odds_json_data = response.json()
            odds_data = OddsData(odds_json_data, data_point)
            odds_data.getOdds("caesars",-100000, 100000)
            odds_data.getOdds("fanduel",-100000, 100000)
            # odds_data.getOdds("pinnacle",-100000, 100000)
            return odds_data

        return None

    def getTeamStatsAgainstPlayer(self, playerPosition : OpponentPlayerPosition, last_n_games : string) -> LeagueDashTeamStats:
        
        time.sleep(1)
        while True:
            try:
                season_game_stats = LeagueDashTeamStats(
                measure_type_detailed_defense='Opponent',
                per_mode_detailed="PerGame",
                player_position_abbreviation_nullable = playerPosition,
                season='2023-24',
                last_n_games=last_n_games,
                proxy=self.proxy
                )
                break
            except:
                time.sleep(1)
                continue

        return season_game_stats

    
    def getLines(self, data_point, game_id):

        category = self.odds_categories[data_point]

        lines_get_request_string = "https://api.prop-odds.com/v1/fantasy_lines/"+game_id+"/"+category+"?api_key="+self.ODDSAPIKEY
        response = requests.get(lines_get_request_string)
        if response.status_code == 200:
            odds_json_data = response.json()
            lines_data = LinesData(odds_json_data, data_point)
            return lines_data

        return None

    
    def compareData(self, game : Game, lineData: LinesData, oddsData : OddsData, stat : str):
        
        LOWER_BOUND = -145
        UPPER_BOUND = 140
        compare_dict = {}
        if lineData.bookie_association["prizepicks"] is not None:
            for player_name in lineData.bookie_association["prizepicks"]:
                away = True
                exists = False
                playerOBJ = None
                for playerData in game.homePlayers:
                    playerFullName = playerData['PLAYER_FIRST_NAME']+" "+playerData['PLAYER_LAST_NAME']
                    if player_name == playerFullName:
                        playerOBJ = playerData
                        away = False
                
                if away:
                    for playerData in game.awayPlayers:
                        playerFullName = playerData['PLAYER_FIRST_NAME']+" "+playerData['PLAYER_LAST_NAME']
                        if playerFullName == player_name:
                            playerOBJ = playerData
                            exists = True

                if exists:
                    playerLine : Line = lineData.bookie_association["prizepicks"][player_name]
                    if oddsData is not None:
                        if player_name in oddsData:
                            for playerOddsData in oddsData[player_name]:
                                diff = abs(abs(playerLine.line) - abs(playerOddsData.handicap))
                                if diff < 1 and (playerOddsData.odds <= LOWER_BOUND or playerOddsData.odds >= UPPER_BOUND):
                                    new_player_line_obj = LineCSVFinal(game.homeTeamFullName, game.awayTeamFullName, away, player_name, playerLine.line, "Prize Picks", stat, playerOddsData.odds, playerOddsData.bookie_key, playerOddsData.OVER)
                                    
                                    new_player_line_obj.LNHitRate = self.calculateLastNHitRate(playerOBJ['PERSON_ID'], playerOddsData.handicap,stat, playerOddsData.OVER, self.last_n_games)
                                    if player_name in compare_dict:
                                        before = compare_dict[player_name]
                                        if new_player_line_obj.odds < before.odds:
                                            compare_dict[player_name] = new_player_line_obj
                                    else:
                                        compare_dict[player_name] = new_player_line_obj
            for line_final_obj in compare_dict.values():
                self.mismatches.append(line_final_obj.listVersion())
        
    def generateCSV(self, csv_name, csv_data):

        header = ["Team","Opposing Team","Opposing Team Player","Fantasy Line","Fantasy Bookie", "Stat","Odds", "Sportsbook Bookie", "Bet Over/Under", "L"+str(self.last_n_games)+" Hit Rate"]
        with open(csv_name+"_"+str(self.year)+"_"+str(self.month)+"_"+str(self.day)+".csv", 'w') as csvFile: 
                # creating a csv writer object 
                csvwriter = csv.writer(csvFile) 
                    
                # writing the fields 
                csvwriter.writerow(header) 
                
                # writing the data rows 
                csvwriter.writerows(csv_data)
            
        csvFile.close()

    def calculateLastNHitRate(self, playerID, handicap, DP, OverUnder, last_n):

        # active_streak_only = "Y"
        # last_n = str(5)
        time.sleep(1)
        while True:
            try:
                last_n_games = []

                gst_stat_finder = PlayerGameLogs(player_id_nullable=playerID, last_n_games_nullable=last_n, season_nullable= "2023-24",proxy=self.proxy)
                if gst_stat_finder is not None:
                    last_n_games = gst_stat_finder.get_normalized_dict()
                
                proj_line = handicap
                hits = 0

                if DP == "3PM":
                    DP = "FG3M"

                if OverUnder:
                    for game_data in last_n_games['PlayerGameLogs']:
                        if game_data["MIN"] > 5:
                            if game_data[DP] > math.floor(proj_line):
                                hits += 1
                    return str(int((hits/self.last_n_games)*100))+"%"
                else:
                    for game_data in last_n_games['PlayerGameLogs']:
                        if game_data["MIN"] > 5:
                            if game_data[DP] < math.ceil(proj_line):
                                hits += 1
                    return str(100-int((hits/self.last_n_games)*100))+"%"
                            
            except:
                time.sleep(1)
                continue


PropOdds(["PTS","REB","AST","STL","BLK","TOV","3PM"])