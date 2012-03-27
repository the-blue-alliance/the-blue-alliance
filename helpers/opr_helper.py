# Calculates OPR
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=1129108&postcount=55

# M is 2m x n where m is # of matches and n is # of teams
# s is 2m x 1 where m is # of matches
# solve [M][x]=[s] for [x] by turning it into [A][x]=[b]

# A should end up being n x n an b should end up being n x 1
# x is OPR and should be n x 1

import sys
from time import *
import csv
from math import sqrt

from models import Event
from models import Team

class OprHelper:

    data = []
    teamdata = []
    M = []

    @classmethod
    def _init_():
        return 0

    @classmethod
    def zeros(cls,m,n):
        # returns the zero matrix for the supplied dimensions
        return [[0 for row in range(n)] for col in range(m)]

    @classmethod
    def mTranspose(cls,matrix):
        # returns the transpose of a matrix
        return map(lambda *row: list(row), *matrix)

    @classmethod
    def mInverse(cls,matrix):
        # TODO: implement matrix inversion
        # not nescessary for anything we have done thus far
        return -1

    @classmethod
    def mMult(cls,matrixA,matrixB):
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
    def getData(cls,event_key):
        #reader = csv.reader(open(file,"rb"))
        error = 0
        for num, match in enumerate(Event.get_by_key_name(event_key).match_set):
            if match.comp_level == "qm":
                num = num-error
                match.unpack_json()
                OprHelper.data.append([])
                OprHelper.data[num].append(int(match.alliances['red']['score'])) #redscore
                OprHelper.data[num].append(int(match.alliances['blue']['score'])) #bluescore
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['red']['teams'][0]).team_number)) #red1
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['red']['teams'][1]).team_number)) #red2
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['red']['teams'][2]).team_number)) #red3
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['blue']['teams'][0]).team_number)) #blue1
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['blue']['teams'][1]).team_number)) #blue2
                OprHelper.data[num].append(int(Team.get_by_key_name(match.alliances['blue']['teams'][2]).team_number)) #blue3
            else:
                error = error+1

    @classmethod
    def getTeamData(cls,event_key):
        #reader = csv.reader(open(file,"rb"))
        for num, team in enumerate(Event.get_by_key_name(event_key).teams):
            OprHelper.teamdata.append([])
            OprHelper.teamdata[num].append(num) #teamid
            OprHelper.teamdata[num].append(int(team.team.team_number)) #teamnumber

    @classmethod
    def getTeamID(cls,num):
        # returns the matrix column index associated with a team number
        for ident, row in enumerate(OprHelper.teamdata):
            if(row[1]==num):
                return ident

    @classmethod
    def getM(cls):
        # puts a 1 in a row of M for each team on an alliance
        print OprHelper.data
        print "-------------"
        print OprHelper.teamdata
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
    def gets(cls):
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
    def decompose(cls,A,ztol=1.0e-3):
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
               except ZeroDivisionError as e:
                   print e
        return(t)

    @classmethod
    def decomposeDoolittle(cls,A):
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
    def solve(cls,L,U,b):
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
    def opr(OprHelper,event_key):
        OprHelper.getTeamData(event_key)
        OprHelper.getData(event_key)
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
