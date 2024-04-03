from datetime import date
from structures import Game, LineCSVFinal, Team, OpponentPlayerPosition
import csv, time, math, requests
from nba_api.stats.endpoints.leaguedashteamstats import LeagueDashTeamStats
from nba_api.stats.endpoints.playergamelogs import PlayerGameLogs

class StatChecker:

    def __init__(self) -> None:
    
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.day = today.day - 1# DELETE THIS + 3
        self.last_n_games = 1

        self.ODDSAPIKEY = "3wLm2UXL3pVjmETX2P05vFRQX3WgEnfmLUkdzwd8"
        # self.ODDSAPIKEY = "0dzjbxegxBpPlBCPsSKbMZnjonG3YmM9u6vYa0nwYTI"
        # self.ODDSAPIKEY = "XnB7yI5hOcx2Hb85EvVQ1PT8n1j8GWqQ4zm4T0Nqa4"
        # self.ODDSAPIKEY = "LpBzajHI10St2NKmolOIVMwGtD5EHOhyHq3kdZo6o"
        username = 'spo8qy8rzn'
        password = '5Welf7njwt5d7iuAPL'
        self.proxy = f"http://{username}:{password}@gate.smartproxy.com:10000"

        data = self.getTeamStatsAgainstPlayer("G", str(1))
        team_stats_data = data.data_sets[0].data['data']

        self.all_teams = {}

        for v in team_stats_data:
            team_obj = Team(v)
            self.all_teams[v[1]] = team_obj

        self.today_games : list[Game] = self.getTodayGames() # MAKE SURE TO DELETE +2 FOR TESTING
        self.over_list = []
        self.under_list = []
        self.new_over = []
        self.new_under = []


        with open('over_fantasy_bet_last15_picks_2024_3_5.csv', newline='') as csvfile:

                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    if "Team" in row[0]:
                        continue
                    self.over_list.append(row)
        
        with open('under_fantasy_bet_last15_picks_2024_3_5.csv', newline='') as csvfile:

                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    if "Team" in row[0]:
                        continue
                    self.under_list.append(row)
                    

        for tg in self.today_games:
            tg.setTeams(self.all_teams[tg.homeTeamFullName],self.all_teams[tg.awayTeamFullName])
            for before_values in self.over_list:
                for awayPlayer in tg.awayPlayers:
                    playerFullName = awayPlayer['PLAYER_FIRST_NAME']+" "+awayPlayer['PLAYER_LAST_NAME']
                    playerID = awayPlayer['PERSON_ID']
                    if playerFullName == before_values[4]:
                        hit = self.calculateLastGameHit(playerID, before_values[6],before_values[2], True)
                        before_values.append(hit)
                        self.new_over.append(before_values)
                        break

            for before_values in self.under_list:
                for awayPlayer in tg.awayPlayers:
                    playerFullName = awayPlayer['PLAYER_FIRST_NAME']+" "+awayPlayer['PLAYER_LAST_NAME']
                    playerID = awayPlayer['PERSON_ID']
                    if playerFullName == before_values[4]:
                        hit = self.calculateLastGameHit(playerID, before_values[6],before_values[2], False)
                        before_values.append(hit)
                        self.new_under.append(before_values)
        
        self.generateCSV("over_fantasy_bet_CHECKED_picks", self.new_over)
        self.generateCSV("under_fantasy_bet_CHECKED_picks", self.new_under)

    def generateCSV(self, csv_name, csv_data):
    
        header = ["Team","Defense Rank","Stat","Position","Opposing Player", "Opposing Player Team", "PRJ Line","Odds", "L"+str(self.last_n_games)+" Hit Rate", "Correct"]
        with open(csv_name+"_"+str(self.year)+"_"+str(self.month)+"_"+str(self.day)+".csv", 'w') as csvFile: 
                # creating a csv writer object 
                csvwriter = csv.writer(csvFile) 
                    
                # writing the fields 
                csvwriter.writerow(header) 
                
                # writing the data rows 
                csvwriter.writerows(csv_data)
            
        csvFile.close()
                    
    
    def getTeamStatsAgainstPlayer(self, playerPosition : str, last_n_games : str) -> LeagueDashTeamStats:
        
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
                #if today_game_prop_odds_games.status_code == 401 or today_game_prop_odds_games.status_code == 403:
                #    break
                time.sleep(2)
                continue

    def calculateLastGameHit(self, playerID, handicap, DP, OverUnder) -> bool:

        time.sleep(1)
        while True:
            try:
                last_n_games = []

                gst_stat_finder = PlayerGameLogs(player_id_nullable=playerID, last_n_games_nullable="1", season_nullable= "2023-24",proxy=self.proxy)
                if gst_stat_finder is not None:
                    last_n_games = gst_stat_finder.get_normalized_dict()

                if DP == "3PM":
                    DP = "FG3M"
                if len(last_n_games['PlayerGameLogs']) == 1:
                    if OverUnder:
                        return last_n_games['PlayerGameLogs'][0][DP] >= float(handicap)
                    else:
                        return last_n_games['PlayerGameLogs'][0][DP] <=  float(handicap)
                return False
            except: 
                time.sleep(1)
                continue

StatChecker()