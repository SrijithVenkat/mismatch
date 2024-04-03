import csv

class FantasyProsDataStruct:

    def __init__(self, row : list[str], position) -> None:
        self.teamAbbreviation = row[0][1:4]
        list_data = row[1 if len(row) == 2 else 2].split(',')
        self.team_name = row[0][4:]
        secondPartName = ("" if len(row) == 2 else row[1]+" ")+list_data[0] 
        self.team_name = self.team_name+" "+secondPartName
        self.data = [float(i) for i in list_data[1:]]
        self.position = position
        self.team_id = None

        self.association = { \

            "GP" : self.data[0],
            "PTS" : self.data[1],
            "REB" : self.data[2],
            "AST" : self.data[3],
            "3PM" : self.data[4],
            "STL" : self.data[5],
            "BLK" : self.data[6],
            "TOV" : self.data[7],
            "SB_PTS" : self.data[8],
            "PTS_RANK" : None,
            "AST_RANK" : None,
            "REB_RANK" : None,
            "3PM_RANK" : None,
        }
    
    def add(self, otherTeam):

        for ind in range(len(self.data)):
            total = self.data[ind] + otherTeam.data[ind]
            self.data[ind] = float(total/2)

class FantasyPros:

    def __init__(self) -> None:
        
        self.guard_dict = {}
        self.forward_dict = {}
        self.center_dict = {}

        self.position_association = { \
            "G" : self.guard_dict,
            "F" : self.forward_dict,
            "C" : self.center_dict,
        }

        self.currentDPList  = {}

        with open('FantasyPros03_23.csv', newline='') as csvfile:
            counter = 0
            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in spamreader:
                if len(set(row[0])) == 1:
                    counter += 1
                    continue
                elif "TEAM" in row[0] or len(row) == 1:
                    continue

                if counter < 2:
                    fp_team =  FantasyProsDataStruct(row, "G")
                    self.addPlayerToPositionDict("G", fp_team)
                elif counter < 4:
                    fp_team =  FantasyProsDataStruct(row, "F")
                    self.addPlayerToPositionDict("F", fp_team)
                else:
                   fp_team =  FantasyProsDataStruct(row, "C")
                   self.addPlayerToPositionDict("C", fp_team)
                
    def addPlayerToPositionDict(self, position, fpTeam : FantasyProsDataStruct):
        
        position_dict = self.position_association[position]

        if fpTeam.team_name not in position_dict:
            position_dict[fpTeam.team_name] = fpTeam
        else:
            before : FantasyProsDataStruct = position_dict[fpTeam.team_name]
            before.add(fpTeam)
            position_dict[fpTeam.team_name] = before

    def sortByCriteria(self, dp, position, team_stats_data):

        current_dp_dict = {}
        position_list = list(self.position_association[position[0]].values())
        position_list.sort(key=lambda teamOBJ : teamOBJ.association[dp])

        bottom_5 = []
        top_5 = []

        for rank, team in enumerate(position_list):
            if team.team_name == "Los Angeles Clippers":
                team.team_name = "LA Clippers"

            if rank + 1 <= 5:
                top_5.append(team.team_name)
            if rank + 1 >= len(position_list) - 4:
                bottom_5.append(team.team_name)

            team.association[dp+"_RANK"] = rank+1
            current_dp_dict[team.team_name] = team

        for team in team_stats_data:
            current_dp_dict[team[1]].team_id = team[0]

        return bottom_5, top_5, current_dp_dict