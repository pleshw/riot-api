
# ---------------------------------- Import.
    #Http request
import requests as Request
import re
    #Flask
from flask import Flask, render_template, url_for
from flask import request

    #Other
from collections import Counter

# ---------------------------------- Global variables.
    #Key handlers.
Key = ""
KeyEmbed = "?api_key=" + Key

    #Flask variables.
App = Flask(__name__)

    #RIOT API
DDragonVersionRequest = "https://ddragon.leagueoflegends.com/api/versions.json"

NORMAL_BLIND = 430
NORMAL_DRAFT = 400
RANKED = 420
RANKED_FLEX = 440


    #Cache variables
PlayerCache = {}
User = None
MatchList = None

# ---------------------------------- Request code.

SummonerRequest = "https://br1.api.riotgames.com/lol/summoner/v4/summoners/"
MatchListRequest = "https://br1.api.riotgames.com/lol/match/v4/matchlists/by-account/"
EloRequest = "https://br1.api.riotgames.com/lol/league/v4/positions/by-summoner/"
# ---------------------------------- Headers.
Headers = {
    "Origin": None,
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Riot-Token": Key,
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ---------------------------------- Methods

    #Usual
def FormatUsername( name ):
    return re.sub('[^A-Za-z0-9]+', '', name).lower()

def TranslateRole( role ):
    if "DUO_CARRY" in role:
        return "ADC"
    if "DUO_SUPPORT" in role:
        return "SUPPORT"
    if role == "DUONONE" or "JUNGLE" in role:
        return "JUNGLE"
    if role == "SOLOMID" or role == "NONEMID":
        return "MID"
    if role == "SOLOTOP" or role == "NONETOP":
        return "TOP"


    #Server shutdown.
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


    
    #Request problem handling
def ServerProblem():
    return "Server error."    
def BadRequest():
    return "Request given in an invalid format."
    


    #Check the problem of a given request.
def RequestIsValid ( req ):
    if req.status_code == 400:
        return BadRequest()
    if req.status_code == 500 or req.status_code == 503:
        return ServerProblem()



    #Return the request with a selected pattern.
def ProcessRequest( req, responseType ):
    if responseType == "json":    
        return req.json()



    #Checks if a request response is valid.
def SafeRequest  ( req, responseType = "json" ):
    if int(req.status_code) == 200:
        return ProcessRequest( req, responseType )
    
    #Requesting summoner info.
def RequestSummonerByName ( name ):
    requestCode = SummonerRequest + "by-name/" + name
    req = Request.get(requestCode, headers = Headers )
    return SafeRequest( req )

def RequestSummonerByAccountId ( accountId ):
    requestCode = SummonerRequest + "by-account/" + accountId
    req = Request.get(requestCode, headers = Headers )
    return SafeRequest( req )



    #Get summoner info.

def SummonerId ( name ):
    return PlayerInfo()["id"]

def SummonerAccountId( name ):
    return PlayerInfo()["accountId"]

def SummonerName ( accountId ):
    return PlayerInfo()["name"]

def GetSummonerSafeInfoByName( name ):
    return {
        "Name": PlayerInfo()["name"],
        "Level": PlayerInfo()["summonerLevel"],
        "IconId": PlayerInfo()["profileIconId"]
    }
    
    
    
    #Get matches info
def RequestMatchList( accountId, beginIndex = 0, endIndex = 20, queue = RANKED ):
    Configs = "?queue=" + str(queue) + "&endIndex=" + str(endIndex) + "&beginIndex=" + str(beginIndex)
    requestCode = MatchListRequest + accountId + Configs
    req =  Request.get(requestCode, headers = Headers )
    return SafeRequest( req )

def RequestEloInfo( userId ): # if user is unranked only the tier will be returned
    requestCode = EloRequest + userId
    req =  Request.get(requestCode, headers = Headers )
    result = SafeRequest( req )
    if len(result) > 0:
        return result
    else: return [{"tier": "UNRANKED"}]


    #Check for existing player data
def PlayerExists( name ):
    global PlayerCache
    if FormatUsername(name) in PlayerCache: return True
    return False 

def SignUp( name ):
    global PlayerCache
    Username = FormatUsername(name)
    if PlayerExists( Username ): 
        Login( Username )
        return False
    Summoner =  RequestSummonerByName( name )
    PlayerCache[Username] = {
            "PlayerInfo": Summoner, 
            "MatchHistory": RequestMatchList(Summoner["accountId"])["matches"],
            "Tier": RequestEloInfo(Summoner["id"])[0]["tier"]
    }
    
    Login( Username )
    
    return True

def Login( name ):
    global User
    User = PlayerCache[FormatUsername(name)]
    return True

def PlayerInfo():
    return User["PlayerInfo"]

def PlayerHistory():
    return User["MatchHistory"]

def PlayerTier():
    return User["Tier"]

def PlayerMostPlayedRoles(): # Get the two most played roles
    c = Counter()
    for match in PlayerHistory():
        mRole = TranslateRole(str(match['role']) + str(match['lane']))
        c[mRole] += 1
    return c.most_common(2)



    #Player match info
def GetMatch( n ):
    if n < len(PlayerHistory()) and n >= 0:    
        return PlayerHistory()[n]
    else: return -1

def GetMatchChampion( n ):
    if n < len(PlayerHistory()) and n >= 0:    
        return GetMatch(n)["champion"]
    else: return -1

def GetMatchRole( n ):
    if n < len(PlayerHistory()) and n >= 0:    
        return GetMatch(n)["role"]
    else: return -1


    
# ---------------------------------- Server
@App.route('/')
def index():
    return render_template( "index.html" )
    

@App.route('/<string:Username>')
def Userpage(Username):
    if PlayerExists( Username ):
        Login( FormatUsername(Username) )
    else:
        SignUp( Username )
    
    return render_template( 
            "userpage.html",
            User = GetSummonerSafeInfoByName( Username ),
            Role = PlayerMostPlayedRoles(),
            Elo = PlayerTier(),
            MatchList = PlayerHistory(),
            DataDragonVersion = SafeRequest(Request.get(DDragonVersionRequest))[0]
    )
    
with App.test_request_context():
    url_for('static', filename='common.css')
    url_for('static', filename='userpage.css')
    url_for('static', filename='userpage.js')
    url_for('static', filename='index.css')
    
App.run()

