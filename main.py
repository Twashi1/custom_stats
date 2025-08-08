# We enter information in sequence
# 1. name of player
# 2. champ
# 3. win/loss
# 4. kda
# 5. cs
# 6. role
# can enter this as a table

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Ben Zed W 9/2/7 238 M
playerAlias = {
    "Ben": ["ben", "combo", "bennayy"],
    "Will": ["will", "colue"],
    "Zamo": ["zamo", "w larp"],
    "Henry": ["henry", "jocersyce"],
    "Oli": ["oli", "erufun", "xxalphaleaderxx"],
    "Panda": ["panda"],
    "Inzi": ["inzi"],
    "Fearless": ["fearless", "xantarespeek"],
    "Yang": ["ysng"],
    "Xt": ["xt", "xtt"]
}

roleMap = {
    "m": "Mid",
    "j": "Jungle",
    "t": "Top",
    "s": "Support",
    "b": "Bot"
}

# We wil turn this into a pandas DataFrame
class PlayerGameInstance:
    def __init__(self):
        self.name = ""
        self.champion = ""
        self.kills = 0
        self.deaths = 0
        self.assists = 0
        # CS per minute
        self.cspm = 0
        self.role = ""
        self.won = False
        self.gameLengthSeconds = 0

    def __str__(self) -> str:
        return f"{self.name}: {self.champion} {self.kills}/{self.deaths}/{self.assists} {self.cspm:.2f} {self.role} {'W' if self.won else 'L'}"

    def __repr__(self) -> str:
        return self.__str__()


def warn(message: str):
    print(f"[WARN] {message}")

# Returns the game length
def parseGameHeader(line: str) -> int:
    # TODO: use regex
    date, time = line[2:].split(" ")
    minutes, seconds = map(int, time.split(":"))

    return minutes * 60 + seconds

def readGames(filename: str) -> list[PlayerGameInstance]:
    playerInstanceList = []
    
    with open(filename, "r") as f:
        currentGameLength = 0
        numberOfPlayers = 0
        lineNumber = 0

        for line in f.readlines():
            lineNumber += 1

            # Ignore comments
            if line.startswith("//"):
                continue

            if line.startswith("#"):
                currentGameLength = parseGameHeader(line)
                continue

            if len(line.rstrip(" \n").split(" ")) != 6:
                warn(f"Line {lineNumber} is malformed: {line.rstrip()}")
                continue

            name, champ, win, kda, cs, role = line.rstrip(" \n").split(" ")

            numberOfPlayers += 1

            # TODO: check for name alias
            instance = PlayerGameInstance()
            instance.name = name.lower()
            instance.champion = champ
            instance.name = name.lower()
            instance.role = roleMap.get(role.lower(), "Unknown")
            instance.won = (win.lower() == "w")
            instance.kills, instance.deaths, instance.assists = map(int, kda.split("/"))
            instance.cspm = int(cs) / (currentGameLength / 60)
            instance.gameLengthSeconds = currentGameLength

            playerInstanceList.append(instance)

    return playerInstanceList

def getPlayerDataFrames(gameInstances: list[PlayerGameInstance]) -> dict[str, pd.DataFrame]:
    playerDataFrames = {}

    for game in gameInstances:
        if game.name not in playerDataFrames:
            playerDataFrames[game.name] = pd.DataFrame(columns=["Champion", "KDA", "CSPM", "Role", "Won", "Game Length"])

        playerDataFrames[game.name] = pd.concat([playerDataFrames[game.name], pd.DataFrame([{
            "Champion": game.champion,
            "KDA": (game.kills + game.assists) / max(1, game.deaths),
            "CSPM": game.cspm,
            "Role": game.role,
            "Won": game.won,
            "Game Length": game.gameLengthSeconds
        }])], ignore_index=True)

    return playerDataFrames

def getPlayerSummary(df: pd.DataFrame) -> pd.Series:
    wins = df["Won"].sum()
    losses = len(df) - df["Won"].sum()
    winrate = wins / (losses + wins) * 100

    summary = {
        "Total games": len(df),
        "Winrate": winrate,
        "Median KDA": df["KDA"].median(),
        "Median CSPM": df["CSPM"].median(),
        "Most common role": df["Role"].mode()[0],
        "Most common champion": df["Champion"].mode()[0]
    }

    return pd.Series(summary)

# TODO
def getOffrolePerformanceDifference(df: pd.DataFrame) -> pd.Series:
    pass

def getCombinedPlayerDataFrame(playerDataFrames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    combinedDf = pd.DataFrame()

    for player, playerDf in playerDataFrames.items():
        playerDf["Player"] = player
        combinedDf = pd.concat([combinedDf, playerDf], ignore_index=True)

    return combinedDf

def getWinrateByGameLength(df: pd.DataFrame) -> pd.DataFrame:
    dfFiltered = filterPlayersByGames(df, 5)
    dfFiltered["Game Length Bins"] = pd.cut(dfFiltered["Game Length"], bins=[15*60, 20*60, 25*60, 30*60, 35*60, 1000*60], labels=["15m-20m", "20-25m", "25-30m", "30-35m", "35m+"])

    dfFiltered["Won"] = dfFiltered["Won"].astype(float)
    grouped = dfFiltered.groupby(["Player", "Game Length Bins"])["Won"].mean().reset_index(name="Winrate")
    grouped["Winrate"] = grouped["Winrate"] * 100

    grouped["Winrate"] = grouped["Winrate"].fillna(0.0)

    grouped = grouped.pivot(columns="Game Length Bins", index="Player", values="Winrate")
    sns.heatmap(grouped, annot=True, fmt=".1f")
    plt.title("Winrate by Game Length Bucket")
    plt.ylabel("Player")
    plt.xlabel("Game Length")
    plt.tight_layout()
    plt.show()

    return grouped

def filterPlayersByGames(df: pd.DataFrame, minGames: int) -> pd.DataFrame:
    playerCounts = df["Player"].value_counts()
    validPlayers = playerCounts[playerCounts >= minGames].index
    return df[df["Player"].isin(validPlayers)]

def getPlayerSummarys(df: pd.DataFrame) -> pd.DataFrame:
    playerSummarys = {}

    for player in df["Player"].unique():
        playerDf = df[df["Player"] == player]
        playerSummarys[player] = getPlayerSummary(playerDf)

    summaryDf = pd.DataFrame.from_dict(playerSummarys, orient="index")
    summaryDf.index.name = "Player"
    return summaryDf

def getRoleBreakdown(df: pd.DataFrame, player: str) -> pd.DataFrame:
    playerDf = df[df["Player"] == player]
    roleBreakdown = playerDf["Role"].value_counts().reset_index()
    roleBreakdown.columns = ["Role", "Count"]
    roleBreakdown = roleBreakdown.sort_values(by="Count", ascending=False)
    return roleBreakdown

def otpScore(df: pd.DataFrame, player: str) -> pd.DataFrame:
    playerDf = df[df["Player"] == player]
    topChampion = playerDf["Champion"].mode()[0]
    gamesOnTopChampion = playerDf[playerDf["Champion"] == topChampion].shape[0]
    percentOtp = gamesOnTopChampion / len(playerDf) * 100.0

    if percentOtp < 33.0: return None

    winsOnTopChampion = playerDf[playerDf["Champion"] == topChampion]["Won"]
    winrateOtp = winsOnTopChampion.astype(float).mean() * 100.0

    return pd.Series({"OTP Percentage": percentOtp, "OTP Winrate": winrateOtp, "Top Champion": topChampion})

def allPlayersOTPScore(df: pd.DataFrame) -> pd.DataFrame:
    dfFiltered = filterPlayersByGames(df, 5)
    otpScores = {}

    for player in dfFiltered["Player"].unique():
        otp = otpScore(dfFiltered, player)

        if otp is not None:
            otpScores[player] = otp

    otpDf = pd.DataFrame.from_dict(otpScores, orient="index")
    otpDf.index.name = "Player"
    otpDf = otpDf.sort_values(by="OTP Percentage", ascending=False)
    return otpDf

def getCSPerRole(df: pd.DataFrame, player: str) -> pd.DataFrame:
    playerDf = df[df["Player"] == player]
    roleCSPM = playerDf.groupby("Role")["CSPM"].mean().reset_index()
    roleCSPM = roleCSPM.sort_values(by="CSPM", ascending=False)
    return roleCSPM

def getRoleAdjustedCSPMSummary(df: pd.DataFrame) -> pd.DataFrame:
    # Get all players with at least 5 games off support
    dfFiltered = filterPlayersByGames(df, 5)
    # Calculate average CSPM across all roles except support
    dfFiltered = dfFiltered[dfFiltered["Role"] != "Support"]
    
    roleCSPM = dfFiltered.groupby("Player")["CSPM"].agg(**{
        "Average CSPM": "mean",
        "Median CSPM": "median"
    }).reset_index()
    roleCSPM = roleCSPM.sort_values(by="Average CSPM", ascending=False)
    roleCSPM.index.name = "Player"
    
    return roleCSPM

def main():
    playerInstances = readGames("stats.txt")
    dataframes = getPlayerDataFrames(playerInstances)
    combined = getCombinedPlayerDataFrame(dataframes)
    summaryStats = getPlayerSummarys(filterPlayersByGames(combined, 5))
    summaryStats = summaryStats.sort_values(by="Winrate", ascending=False)
    print(summaryStats)
    
    print(getRoleAdjustedCSPMSummary(combined))
    
if __name__ == "__main__":
    main()