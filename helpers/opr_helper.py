# Calculates OPR
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=1129108&postcount=55

# M is 2m x n where m is # of matches and n is # of teams
# s is 2m x 1 where m is # of matches
# solve [M][x]=[s] for [x] by turning it into [A][x]=[b]

# A should end up being n x n an b should end up being n x 1
# x is OPR and should be n x 1

# TODO: This library should be broken out to be completely abstracted from the datastore
# then a layer should wrap it to fetch data from the datastore, plumb it in, and get the
# results back out. -gregmarra 31 Mar 2012

import csv
import sys
from math import sqrt
from time import *

from models.event import Event
from models.event_team import EventTeam
from models.team import Team

class OprHelper:

    data = []
    teamdata = []
    M = []

    @classmethod
    def _init_(self):
        OprHelper.data = []
        OprHelper.teamdata = []
        OprHelper.M = []
        return 0

    @classmethod
    def reset(self):
        OprHelper.data = []
        OprHelper.teamdata = []
        OprHelper.M = []

    @classmethod
    def zeros(self,m,n):
        # returns the zero matrix for the supplied dimensions
        return [[0 for row in range(n)] for col in range(m)]

    @classmethod
    def mTranspose(self,matrix):
        # returns the transpose of a matrix
        return map(lambda *row: list(row), *matrix)

    @classmethod
    def mInverse(self,matrix):
        # TODO: implement matrix inversion
        # not nescessary for anything we have done thus far
        return -1

    @classmethod
    def mMult(self,matrixA,matrixB):
        # returns result of multiplying A by B
        if len(matrixA[0]) != len(matrixB):
            print "Matrix dimension error!"
        else:
            result = OprHelper.zeros(len(matrixA),len(matrixB[0]))
            for i in range(len(matrixA)):
                 for j in range(len(matrixB[0])):
                    for k in range(len(matrixB)):
                        result[i][j] += matrixA[i][k]*matrixB[k][j]
            return result

    @classmethod
    def getData(self,event):
        #reader = csv.reader(open(file,"rb"))
        # TODO: This doesn't seem like it would support older matches with 2v2 games -gregmarra 8 Mar 2012 
        num = 0
        for match in event.match_set:
            match.unpack_json()
            if hasattr(match, 'alliances'):
                if (match.comp_level == "qm" and match.alliances['red']['score'] > -1 and match.alliances['blue']['score'] > -1):
                    OprHelper.data.append([])
                    OprHelper.data[num].append(int(match.alliances['red']['score'])) #redscore
                    OprHelper.data[num].append(int(match.alliances['blue']['score'])) #bluescore
                    OprHelper.data[num].append(int(match.alliances['red']['teams'][0][3:])) #red1
                    OprHelper.data[num].append(int(match.alliances['red']['teams'][1][3:])) #red2
                    OprHelper.data[num].append(int(match.alliances['red']['teams'][2][3:])) #red3
                    OprHelper.data[num].append(int(match.alliances['blue']['teams'][0][3:])) #blue1
                    OprHelper.data[num].append(int(match.alliances['blue']['teams'][1][3:])) #blue2
                    OprHelper.data[num].append(int(match.alliances['blue']['teams'][2][3:])) #blue3
                    num += 1

    @classmethod
    def getTeamData(self,event):
        #reader = csv.reader(open(file,"rb"))
        event_teams = event.teams.fetch(500)
        team_keys = [EventTeam.team.get_value_for_datastore(event_team).name() for event_team in event_teams]
        
        for num, team_key in enumerate(team_keys):
            OprHelper.teamdata.append([])
            OprHelper.teamdata[num].append(num) #teamid
            OprHelper.teamdata[num].append(int(team_key[3:])) #teamnumber

    @classmethod
    def teamsPlayed(self):
        played = []
        counter = 0
        for team_id,team_number in OprHelper.teamdata:
            if OprHelper.teamPlayed(team_number):
                played.append([])
                played[counter].append(team_id)
                played[counter].append(team_number)
                counter += 1
        return played

    @classmethod
    def teamPlayed(self,team):
        """
        Returns True if the team played at least one match (was present at regional)
        Returns False if the team has not played any matches (was absent from regional)
        """
        for i,row in enumerate(OprHelper.data):
            for j in range(2,7):
                if OprHelper.data[i][j]==team:
                    return True
        return False

    @classmethod
    def getTeamID(self,num):
        # returns the matrix column index associated with a team number
        for ident, row in enumerate(OprHelper.teamdata):
            if(row[1]==num):
                return ident

    @classmethod
    def getM(self):
        # puts a 1 in a row of M for each team on an alliance
        i = 0
        OprHelper.M = OprHelper.zeros(2*len(OprHelper.data),len(OprHelper.teamdata))
        while (i)<2*len(OprHelper.data):
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][2])] = 1
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][3])] = 1
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][4])] = 1

            i += 1
                
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][5])] = 1
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][6])] = 1
            OprHelper.M[i][OprHelper.getTeamID(OprHelper.data[i/2][7])] = 1
            i += 1

    @classmethod
    def gets(self):
        # gets each alliance's score for each match
        i = 0
        s = [[0] for row in range(2*len(OprHelper.data))]
        while i<2*len(OprHelper.data):
            s[i][0] = (OprHelper.data[i/2][0])
            i += 1
            s[i][0] = (OprHelper.data[i/2][1])
            i += 1
        return s

    @classmethod
    def decompose(self,A,ztol=1.0e-3):
        # Algorithm for upper triangular Cholesky factorization
        # gives U
        # NOT USED!!! SEE decomposeDoolittle below

        num = len(A)
        t = OprHelper.zeros(num, num)
        for i in range(num):
            S = sum([(t[i][k])**2 for k in range(1,i-1)])
            d = A[i][i] -S
            if abs(d) < ztol:
               t[i][i] = 0.0
            else: 
               if d < 0.0:
                  raise ValueError, "Matrix not positive-definite"
               t[i][i] = sqrt(d)
            for j in range(i+1, num):
               S = sum([t[j][k] * t[i][k] for k in range(1,i-1)])
               if abs(S) < ztol:
                  S = 0.0
               try:
                   t[j][i] = (A[j][i] - S)/t[i][i]
               except ZeroDivisionError, e:
                   print e
        return(t)

    @classmethod
    def decomposeDoolittle(self,A):
        # Algorithm for upper and lower triangular factorization
        # gives U and L; uses Doolittle factorization
        # http://math.fullerton.edu/mathews/n2003/CholeskyMod.html

        n = len(A)
        L = OprHelper.zeros(n, n)
        U = OprHelper.zeros(n, n)
        for k in range(n):
            L[k][k] = 1
            for j in range(k,n):
                U[k][j] = A[k][j]-sum(L[k][m]*U[m][j] for m in range(k))
            for i in range(k+1,n):
                L[i][k] = (A[i][k]-sum(L[i][m]*U[m][k] for m in range(k)))/float(U[k][k])
        return U,L

    @classmethod
    def solve(self,L,U,b):
        # Algorithm from http://en.wikipedia.org/wiki/Triangular_matrix
        # Ax = b -> LUx = b. Then y is defined to be Ux
        # http://math.fullerton.edu/mathews/n2003/BackSubstitutionMod.html

        y = [[0] for row in range(len(b))]
        x = [[0] for row in range(len(b))]
        
        # Forward elimination Ly = b
        for i in range(len(b)):
            y[i][0] = b[i][0]
            for j in range(i):
                y[i][0] -= L[i][j]*y[j][0]
            y[i][0] /= float(L[i][i])
            
        # Backward substitution Ux = y
        for i in range(len(y)-1,-1,-1):
            x[i][0] = y[i][0]
            for j in range(i+1,len(y)):
                x[i][0] -= U[i][j]*x[j][0]
            x[i][0] /= float(U[i][i])
        return x

    @classmethod
    def opr(self,event_key):
        OprHelper.reset()
        
        event = Event.get_by_key_name(event_key)
        OprHelper.getTeamData(event)
        OprHelper.getData(event)
        
        OprHelper.teamdata = OprHelper.teamsPlayed()
        OprHelper.getM()
        s = OprHelper.gets()
        Mtrans = OprHelper.mTranspose(OprHelper.M)
        A = OprHelper.mMult(Mtrans,OprHelper.M) # multiply M' times M to get A
        b = OprHelper.mMult(Mtrans,s) # multiply M' times s to get b
        U,L = OprHelper.decomposeDoolittle(A)
        temp = OprHelper.solve(L,U,b)
        OPR = OprHelper.zeros(len(temp),1)
        for num, blah in enumerate(list(temp)):
            OPR[num] = temp[num][0]
        temp = OprHelper.teamdata
        teams = OprHelper.zeros(len(OprHelper.teamdata),1)
        for num, blah in enumerate(list(temp)):
            teams[num] = temp[num][1]
        
        return OPR, teams
        
#if __name__ == "__main__":
#    start = clock()
#    instance = opr()
#    instance.getTeamData("worteam.csv")
#    instance.getData("wor.csv")
#    instance.test()
#    end = clock()
#    print "Took ",end-start," seconds"
