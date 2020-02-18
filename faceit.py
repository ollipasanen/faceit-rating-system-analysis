import requests
import sqlite3
import sys
import json
import time
import random
import click
import traceback

from datetime import datetime

TOKEN = "{token}"

conn = sqlite3.connect('{db_path}')

ELO_QUERY = """
select winner, (t1elo + t2elo + t3elo + t4elo + t5elo) as fac1elo, (t6elo + t7elo + t8elo + t9elo + t10elo) as fac2elo from (
  select 
  matches.match_id,
  winner,
  map,
  t1.elo as t1elo,
  t2.elo as t2elo,
  t3.elo as t3elo,
  t4.elo as t4elo,
  t5.elo as t5elo,
  t6.elo as t6elo,
  t7.elo as t7elo,
  t8.elo as t8elo,
  t9.elo as t9elo,
  t10.elo as t10elo
  from
  matches, elo_entry as t1, elo_entry as t2, elo_entry as t3, elo_entry as t4, elo_entry as t5, elo_entry as t6, elo_entry as t7, elo_entry as t8, elo_entry as t9, elo_entry as t10 where
  matches.match_id = t1.match_id and matches.p1 = t1.user_id and
  matches.match_id = t2.match_id and matches.p2 = t2.user_id and
  matches.match_id = t3.match_id and matches.p3 = t3.user_id and
  matches.match_id = t4.match_id and matches.p4 = t4.user_id and
  matches.match_id = t5.match_id and matches.p5 = t5.user_id and
  matches.match_id = t6.match_id and matches.o1 = t6.user_id and
  matches.match_id = t7.match_id and matches.o2 = t7.user_id and
  matches.match_id = t8.match_id and matches.o3 = t8.user_id and
  matches.match_id = t9.match_id and matches.o4 = t9.user_id and
  matches.match_id = t10.match_id and matches.o5 = t10.user_id and
  matches.status = "FINISHED"
);
"""

DIFF_QUERY = """
select 
matches.match_id,
winner,
map,
t1.elo_diff as t1elo_diff,
t2.elo_diff as t2elo_diff,
t3.elo_diff as t3elo_diff,
t4.elo_diff as t4elo_diff,
t5.elo_diff as t5elo_diff,
t6.elo_diff as t6elo_diff,
t7.elo_diff as t7elo_diff,
t8.elo_diff as t8elo_diff,
t9.elo_diff as t9elo_diff,
t10.elo_diff as t10elo_diff,
t1.elo as t1elo,
t2.elo as t2elo,
t3.elo as t3elo,
t4.elo as t4elo,
t5.elo as t5elo,
t6.elo as t6elo,
t7.elo as t7elo,
t8.elo as t8elo,
t9.elo as t9elo,
t10.elo as t10elo
from
matches, elo_entry as t1, elo_entry as t2, elo_entry as t3, elo_entry as t4, elo_entry as t5, elo_entry as t6, elo_entry as t7, elo_entry as t8, elo_entry as t9, elo_entry as t10 where
matches.match_id = t1.match_id and matches.p1 = t1.user_id and
matches.match_id = t2.match_id and matches.p2 = t2.user_id and
matches.match_id = t3.match_id and matches.p3 = t3.user_id and
matches.match_id = t4.match_id and matches.p4 = t4.user_id and
matches.match_id = t5.match_id and matches.p5 = t5.user_id and
matches.match_id = t6.match_id and matches.o1 = t6.user_id and
matches.match_id = t7.match_id and matches.o2 = t7.user_id and
matches.match_id = t8.match_id and matches.o3 = t8.user_id and
matches.match_id = t9.match_id and matches.o4 = t9.user_id and
matches.match_id = t10.match_id and matches.o5 = t10.user_id and
matches.status = "FINISHED"
ORDER BY matches.timestamp ASC;
"""

DISTR_QUERY = """
select elo, max(timestamp) from elo_entry group by user_id;
"""

@click.group()
def main():
  pass

@main.command()
def init_db():
  conn.execute("CREATE TABLE IF NOT EXISTS elo_entry (user_id TEXT, match_id TEXT, name TEXT, elo REAL, timestamp TEXT, elo_diff REAL);")
  conn.execute("CREATE TABLE IF NOT EXISTS matches (match_id TEXT, created_at TEXT, p1 TEXT, p2 TEXT, p3 TEXT, p4 TEXT, p5 TEXT, o1 TEXT, o2 TEXT, o3 TEXT, o4 TEXT, o5 TEXT, winner TEXT, map TEXT, status TEXT, timestamp TEXT);")

def log(arg):
  print("[{}]: {}".format(datetime.now().isoformat(), arg), flush=True)

@main.command()
def get_ongoing_matches():
  log("Getting ongoing matches")

  url = "https://api.faceit.com/match/v1/matches/list?entityType=matchmaking&game=csgo&limit=10&offset=0&region=EU&state=ONGOING"
  r = requests.get(url).json()

  newcount = 0

  for match in r["payload"]:
    match_id = match["id"]

    if match_exists(match_id):
      log("Match exists: {}".format(match_id))
      continue

    log("New match {}".format(match_id))
    conn.execute("INSERT INTO matches (match_id, status, created_at) VALUES(?,?,?)", (match_id, "ONGOING", int(time.time())))
    newcount += 1

    if newcount == 4:
      conn.commit()
      return

  conn.commit()
  
def match_exists(match_id):
  q = conn.execute("SELECT * FROM matches WHERE match_id=?", (match_id, ))
  return bool(q.fetchone())

def get_match_details(match_id):
  url = "https://open.faceit.com/data/v4/matches/{}".format(match_id)
  r = requests.get(url, headers={"Authorization": "Bearer {}".format(TOKEN)})
  return r.json()

@main.command()
def crawl_one():
  log("Crawling one")

  try:
    rows = conn.execute("SELECT match_id FROM matches WHERE status = 'ONGOING' AND created_at is not null ORDER BY created_at DESC LIMIT 5 OFFSET 12;")
  except Exception as e:
    log("Failed with exception")
    log(str(e))

  one_ok = False

  for match in rows:
    match_id = match[0]

    log("Crawling {}".format(match_id))

    resp = get_match_details(match_id)
    log("Response ok, status='{}'".format(resp["status"]))

    if resp["status"] not in ("FINISHED", "ONGOING"):
      log("Weird match state, updating db")
      conn.execute("UPDATE matches SET status=? WHERE match_id=?", (resp["status"], match_id))
      conn.commit()
      continue

    if resp["status"] != "FINISHED":
      log("Not finished yet")
      time.sleep(0.514)
      continue

    one_ok = True
    break

  if not one_ok:
    log("Nothing we can do.")
    return

  # First fill the match details

  time.sleep(2)
  log("Filling match details")

  team1 = resp["teams"]["faction1"]["roster"]
  team2 = resp["teams"]["faction2"]["roster"]

  ids1 = tuple(x["player_id"] for x in team1)
  ids2 = tuple(x["player_id"] for x in team2)

  winner = resp["results"]["winner"]
  map_pick = resp["voting"]["map"]["pick"][0]

  data = ids1 + ids2 + (winner, map_pick, resp["status"], resp["started_at"], match_id)

  conn.execute("UPDATE matches SET p1=?, p2=?, p3=?, p4=?, p5=?, o1=?, o2=?, o3=?, o4=?, o5=?, winner=?, map=?, status=?, timestamp=? WHERE match_id=?", data)

  log("Match details committed, crawl user elos")

  users = ids1 + ids2
  for user_id in users:
    log("Getting elo stats for {}".format(user_id))

    url = "https://api.faceit.com/stats/v1/stats/time/users/{}/games/csgo?page=0&size=30".format(user_id)
    r = requests.get(url)
    matches = r.json()

    prev_elo = None
    prev_match = None
    have_diff = True
    found = False

    for match in matches:
      if "elo" not in match or "status" not in match or match["status"] != "APPLIED":
        #log("No elo for this match!")
        have_diff = False
        continue

      q = conn.execute("SELECT * FROM elo_entry WHERE user_id=? AND match_id=?", (user_id, match["matchId"]))

      if not q.fetchone():
        if match["matchId"] == match_id:
          log("Found a matching elo entry for this match.")
          found = True
        #log("Elo entry missing for this match.")
        conn.execute("INSERT INTO elo_entry (user_id, match_id, name, elo, timestamp) VALUES (?,?,?,?,?)", (user_id, match["matchId"], match["nickname"], match["elo"], match["created_at"]))

      # Update elo diff if we have it
      if have_diff:
        elo_diff = 100 # impossible to get
        new_elo = int(match["elo"])

        if prev_elo is not None:
          elo_diff = new_elo - prev_elo

        if elo_diff != 0 and prev_match is not None:
          # only update if match was successful, 0 is not good
          # print("User: {} Match: {} Diff: {}".format(user_id, prev_match, -elo_diff))
          conn.execute("UPDATE elo_entry SET elo_diff=? WHERE user_id=? AND match_id=?", (-elo_diff, user_id, prev_match))

        prev_elo = new_elo
        prev_match = match["matchId"]


    if not found:
      log("No matching elo entry found! :(")

    time.sleep(random.randint(2, 5))

  log("Crawl done")
  conn.commit()

@main.command()
def get_elo_stats():
  rows = conn.execute(ELO_QUERY)
  for row in rows:
    print("\t".join(str(x) for x in row))

@main.command()
def get_elo_diff():
  rows = conn.execute(DIFF_QUERY)
  for row in rows:
    print("\t".join(str(x) for x in row))

@main.command()
def export_data():
  with open("team_elo.txt", "w") as f:
    for row in conn.execute(ELO_QUERY):
      f.write("\t".join(str(x) for x in row) + "\n")
  with open("elo_diff.txt", "w") as f:
    for row in conn.execute(DIFF_QUERY):
      f.write("\t".join(str(x) for x in row) + "\n")
  with open("elo_distribution.txt", "w") as f:
    for row in conn.execute(DISTR_QUERY):
      f.write("\t".join(str(x) for x in row) + "\n")

if __name__ == '__main__':
  try:
    main()
  except Exception as e:
    traceback.print_exc(file=sys.stdout)
    log("Failed successfully")
