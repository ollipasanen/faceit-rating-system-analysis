import math

class Histogram:
  def __init__(self, A, B, N):
    self.step = (B - A) / N
    self.N = N
    self.A = A
    self.B = B
    self.buckets = [[] for x in range(N)]
    self.bucketranges = [(self.A + i*self.step, self.A + (i+1)*self.step) for i in range(N)]
    self.cnt = 0

  def add(self, value, x=None):
    if x is None:
      x = value

    for i, t in enumerate(self.bucketranges):
      a, b = t
      if x >= a and x < b:
        self.buckets[i].append(value)
        self.cnt += 1
        return

# Parse the output data

with open("team_elo.txt", "r") as f:
  data = f.read()

team_elo = []

for line in data.split("\n"):
  if not line:
    continue
  s = line.split()
  team_elo.append((s[0], float(s[1]), float(s[2])))

with open("elo_diff.txt", "r") as f:
  data = f.read()

elo_diff = []

for line in data.split("\n"):
  if not line:
    continue
  s = line.split()
  match_id = s[0]
  winner = s[1]
  map_ = s[2]
  team1_diffs = [float(x) if x != "None" and x != "100.0" else None for x in s[3:3+5]]
  team2_diffs = [float(x) if x != "None" and x != "100.0" else None for x in s[3+5:3+10]]

  # if we are missing diffs and all known diffs are equal, set the missing ranks to the known diff

  tmp = [x for x in team1_diffs if x is not None]

  if not tmp:
    # useless data as we don't know the elo diffs
    continue

  if all(x == tmp[0] for x in tmp):
    team1_diffs = [tmp[0]] * 5 

  tmp = [x for x in team2_diffs if x is not None]

  if not tmp:
    # useless data as we don't know the elo diffs
    continue

  if all(x == tmp[0] for x in tmp):
    team2_diffs = [tmp[0]] * 5 

  team1_elo = [float(x) for x in s[3+10:3+15]]
  team2_elo = [float(x) for x in s[3+15:3+20]]

  elo_diff.append((winner, map_, team1_diffs, team2_diffs, team1_elo, team2_elo))


with open("elo_distribution.txt", "r") as f:
  data = f.read()

current_elos = []

for line in data.split("\n"):
  if not line:
    continue
  s = line.split()
  current_elos.append(float(s[0]))


##########################

def figure1():
  print("Histogram[{", end="")

  for entry in elo_diff:

    if any(x is None for x in entry[2]) or \
      any(x is None for x in entry[3]):
      continue

    team1_elo = sum(x - d for d, x in zip(entry[2], entry[4])) / 5.0
    team2_elo = sum(x - d for d, x in zip(entry[3], entry[5])) / 5.0

    abs_diff = abs(team1_elo - team2_elo)
    #avg_elo = (entry[1] + entry[2]) / 10

    print("{:.2f},".format(abs_diff), end="")

  print("}}, {{0,200,5}}, ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Team Elo difference (n={})\", \"Number of matches\"}}, PlotRangeClipping -> True]".format(len(elo_diff)))

##########################


def figure2():
  print("Histogram[{", end="")

  for entry in elo_diff:

    if any(x is None for x in entry[2]) or \
      any(x is None for x in entry[3]):
      continue

    team1_elo = sum(x - d for d, x in zip(entry[2], entry[4])) / 5.0
    team2_elo = sum(x - d for d, x in zip(entry[3], entry[5])) / 5.0

    abs_diff = abs(team1_elo - team2_elo)
    #avg_elo = (entry[1] + entry[2]) / 10

    print("{:.2f},".format(abs_diff), end="")

  print("}}, {{0,200,5}}, \"CDF\", ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Team Elo difference (n={})\", \"Number of matches\"}}, PlotRangeClipping -> True]".format(len(elo_diff)))


##########################

def figure3():
  print("DensityHistogram[{", end="")
  cnt = 0

  for entry in elo_diff:
    winner = entry[0]

    if any(x is None for x in entry[2]) or \
      any(x is None for x in entry[3]):
      continue

    team1_elo = sum(x - d for d, x in zip(entry[2], entry[4])) / 5.0
    team2_elo = sum(x - d for d, x in zip(entry[3], entry[5])) / 5.0

    avg_elo = (team1_elo + team2_elo) / 2.0
    abs_diff = abs(team1_elo - team2_elo)

    if avg_elo > 2600 or abs_diff > 300:
      continue

    cnt += 1
    
    print("{{{:.2f}, {:.2f}}},".format(avg_elo, abs_diff), end="")

  print("}}, {{40, 40}}, ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Average Elo in the match (n={})\", \"Difference between teams' average Elos\"}}]".format(cnt))

##########################

def figure4():

  fig4 = Histogram(800, 2500, 100)
  print("ListPlot[{", end="")

  for entry in elo_diff:
    if any(x is None for x in entry[2]) or \
      any(x is None for x in entry[3]):
      continue

    team1_elo = sum(x - d for d, x in zip(entry[2], entry[4])) / 5.0
    team2_elo = sum(x - d for d, x in zip(entry[3], entry[5])) / 5.0

    avg_elo = (team1_elo + team2_elo) / 2.0
    abs_diff = abs(team1_elo - team2_elo)

    fig4.add(abs_diff, x=avg_elo)

  for i, t in enumerate(fig4.bucketranges):
    a, b = t
    bu = fig4.buckets[i]
    if len(bu) < 2:
      continue
    m = sum(bu) / len(bu)
    var_res = (sum((xi - m) ** 2 for xi in bu) / (len(bu) - 1))

    #for y in bu:
    print("{{{:.2f}, {:.2f}}},".format((a+b)/2., var_res), end="")

  print("}}, ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Average Elo in the match (n={})\", \"Variance of the teams' Elo differences\"}}, Filling -> Axis]".format(fig4.cnt))


def figure5():
  print("fig4data={", end="")
  l = []

  for entry in elo_diff:
    if entry[2][0] is None or entry[2][0] == 100:
      continue

    if not all(x == entry[2][0] for x in entry[2]) or not all(x == entry[3][0] for x in entry[3]):
      continue

    team1_elo = sum(x - entry[2][0] for x in entry[4]) / len(entry[4])
    team2_elo = sum(x - entry[3][0] for x in entry[5]) / len(entry[5])

    if entry[0] == "faction1":
      # team 1 won

      # players in team 1 gained
      for p in entry[2]:
        if p is None or p == 100.0:
          continue
        l.append("{{{:.2f}, {:.2f}}}".format(p, team1_elo - team2_elo))

    if entry[0] == "faction2":
      # team 2 won

      # players in team 2 gained
      for p in entry[3]:
        if p is None or p == 100.0:
          continue
        l.append("{{{:.2f}, {:.2f}}}".format( p, team2_elo - team1_elo))


  print(",".join(l), end="")
  print("}}; ListPlot[fig4data, ImageSize -> Large, PlotRange-> {{{{0,40}}, {{-200,400}}}}, FrameLabel -> {{\"Elo gained by winning team (n={})\", \"Team Elo difference\"}}, PlotTheme -> \"Scientific\"]".format(len(l)))

##########################


def figure6():
  print("BarChart[{", end="")

  level_boundaries = [
    (1, 800),
    (801, 950),
    (951, 1100),
    (1101, 1250),
    (1251, 1400),
    (1401, 1550),
    (1551, 1700),
    (1701, 1850),
    (1851, 2000),
    (2001, 20000)
  ]

  cnt = {i: 0 for i in range(1, 11)}

  for entry in current_elos:
    for i, t in enumerate(level_boundaries):
      a, b = t
      if entry >= a and entry <= b:
        cnt[i+1] += 1

  percentages = {k: v / float(len(current_elos)) * 100.0 for k, v in cnt.items()}

  for level, p in percentages.items():
    print("Labeled[{:.2f}, \"Level {}\"],".format(p, level), end="")

  print("}, FrameLabel -> {None, \"Estimated % of active players\"}, ImageSize -> Large, PlotTheme -> \"Scientific\"]")

##########################

def figure7():
  print("Histogram[{", end="")

  level_boundaries = [
    (1, 800),
    (801, 950),
    (951, 1100),
    (1101, 1250),
    (1251, 1400),
    (1401, 1550),
    (1551, 1700),
    (1701, 1850),
    (1851, 2000),
    (2001, 20000)
  ]

  cnt = {i: 0 for i in range(1, 11)}

  for entry in current_elos:
    print("{:.2f},".format(entry), end="")

    for i, t in enumerate(level_boundaries):
      a, b = t
      if entry >= a and entry <= b:
        cnt[i+1] += 1

  percentages = {k: v / float(len(current_elos)) * 100.0 for k, v in cnt.items()}

  print("}}, {{0,3000,100}}, ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Elo distribution (n={})\", \"Number of players\"}}, PlotRangeClipping -> True]".format(len(current_elos)))

  print("| Rank | Level | Est. population % | Est. Cumulative population % |")
  print("|---|---|---|--|")
  t = 0.0
  for level in range(1, 11):
    t += percentages[level]
    a, b = level_boundaries[level-1]
    f = "{}-{}".format(a, b)
    if level == 10:
      f = "2001+"
    print("| {} | {} | {:.2f} % | {:.2f} % |".format(f, level, percentages[level], t))


##########################

def figure8():
  print("Histogram[{", end="")

  for entry in current_elos:
    print("{:.2f},".format(entry), end="")

  print("}}, {{0,3000,100}}, \"CDF\", ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Cumulative Elo distribution (n={})\", \"Number of players\"}}, PlotRangeClipping -> True]".format(len(current_elos)))

def figure9():
  fig9 = Histogram(0, 1, 10)

  print("Show[ListPlot[{", end="")

  def confidence(wins, losses):
      n = wins + losses

      if n == 0:
          return 0

      z = 1.96 #1.44 = 85%, 1.96 = 95%
      phat = float(wins) / n
      return ((phat + z*z/(2*n) - z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n), (phat + z*z/(2*n) + z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))

  for entry in elo_diff:
    if entry[2][0] is None or entry[2][0] == 100:
      continue

    if not all(x == entry[2][0] for x in entry[2]) or not all(x == entry[3][0] for x in entry[3]):
      continue

    team1_elo = sum(x - entry[2][0] for x in entry[4]) / len(entry[4])
    team2_elo = sum(x - entry[3][0] for x in entry[5]) / len(entry[5])
    prob = 1/(1 + 10**((team1_elo - team2_elo)/400))

    fig9.add(prob)

  for i, t in enumerate(fig9.bucketranges):
    a, b = t
    l = fig9.buckets[i]
    n = len(l)

    wins = sum(l)
    losses = n - wins

    if n == 0:
      continue
      p = 0.5
      upper_error = 0.5
      lower_error = 0.5
    else:
      p = float(wins) / n
      upper, lower = confidence(wins, losses)
      upper_error = upper - p
      lower_error = lower - p

    print(n)

    pos = float(a + b) / 2
    print("{{{:.4f}, Around[{:.4f},{{{:.3f}, {:.3f}}}]}}".format(pos, p, upper_error, lower_error), end="")

    if i != fig9.N - 1:
      print(",", end="")

  print("}},PlotTheme -> \"Detailed\", PlotMarkers -> {{Graphics[{{Disk[]}}], 0.03}}, ImageSize -> Large, PlotTheme -> \"Scientific\", FrameLabel -> {{\"Estimated win probability (n={})\", \"Observed win probability\"}}, PlotRangeClipping -> True], Plot[t,{{t,0,1}}, PlotStyle -> {{Dashed, Darker[Green]}}], PlotRange->{{{{0, 1}},{{0, 1}}}}]".format(fig9.cnt))

if __name__ == '__main__':
  figure6()