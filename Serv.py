from flask import Flask, request, jsonify, make_response
import requests
import time
import threading

app = Flask(__name__)

BASE_URL = "https://lksh-enter.ru"
TOKEN = "7536eb0a1ca9af5a930174bdb83c63533d2a67ec6424751f3991c98874389746"
HEADERS = {
    "Authorization": TOKEN,
    "reason": "I want to get into parallel P because I learned it pretty quickly (basically) and want to continue learning"
}
DATA = {
    "reason": "I want to get into parallel P because I learned it pretty quickly (basically) and want to continue learning"
}
def post_reason():
    r = requests.post(f"{BASE_URL}/login", headers=HEADERS, json=DATA, timeout=600)
    if r.status_code == 429:
        time.sleep(1)
        post_reason()
def get_teams():
    r = requests.get(f"{BASE_URL}/teams", headers=HEADERS, timeout=600)
    #print("get_teams ", r.status_code)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        time.sleep(1)
        get_teams()

def get_matches():
    r = requests.get(f"{BASE_URL}/matches", headers=HEADERS, timeout=600)
    #print("get_matches ", r.status_code)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        time.sleep(1)
        get_matches()

def get_team_by_id(team_id):
    r = requests.get(f"{BASE_URL}/teams/{team_id}", headers=HEADERS, timeout=300)
    #print("get_team_by_id ", r.status_code)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 429:
        time.sleep(1)
        get_team_by_id(team_id)
    else:
        for team in teams:
            if team["id"] == team_id:
                return team
    return None

def get_goals_by_match_id(match_id):
    r = requests.get(f"{BASE_URL}/goals", params={"match_id": match_id}, headers=HEADERS, timeout=300)
    #print("get_goals_by_match_id ", r.status_code)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        time.sleep(1)
        get_goals_by_match_id(match_id)
    return None

def get_player_by_id(player_id):
    r = requests.get(f"{BASE_URL}/players/{player_id}", headers=HEADERS, timeout=300)
    #print("get_player_by_id ", r.status_code)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 429:
        time.sleep(1)
    else:
        return None

def get_player_in_match_by_number(match, number):
    for player_id in get_team_by_id2(match["team1"])["players"]:
        player = get_player_by_id2(player_id)
        if player is None:
            continue
        if player["number"] == number:
            return player
    for player_id in get_team_by_id2(match["team2"])["players"]:
        player = get_player_by_id2(player_id)
        if player is None:
            continue
        if player["number"] == number:
            return player
    return None

def get_team_by_id2(team_id):
    for team in teams:
        if team["id"] == team_id:
            return team
    return None


def get_player_by_id2(player_id):
    for player in players:
        if player["id"] == player_id:
            return player
    return None

def find_team_by_name(name):
    for team in teams:
        if team["name"].lower() == name.lower():
            return team
    return None

teams = []
matches = []
players = []
tournament = {
    "": [[]]
}


def _stats(team_name):
    scored = 0
    missed = 0
    win = 0
    lose = 0
    try:
        for game in tournament[team_name]:
            scored += game[1]
            missed += game[2]
            if game[1] > game[2]:
                win += 1
            if game[1] < game[2]:
                lose += 1
        return [win, lose, scored - missed]
    except KeyError:
        return [0, 0, 0]

def _versus(player1_id, player2_id):

    # Найдем команды игроков
    if not isinstance(player1_id, int) or not isinstance(player2_id, int):
        return 0
    player1 = get_player_by_id2(player1_id)
    player2 = get_player_by_id2(player2_id)
    if player1 is None or player2 is None:
        return 0
    player1_teams = player1["team"]
    player2_teams = player2["team"]
    if player1_teams is None or player2_teams is None or player1_teams == player2_teams:
        return 0
    total_matches = 0
    for player1_team in player1_teams:
        for game in tournament[player1_team]:
            if game is None:
                continue
            if game[0] in player2_teams:
                total_matches += 1
    return total_matches

def _goals(player1_id):
    player1 = get_player_by_id2(player1_id)
    try:
        return player1["goals"]
    except KeyError:
        return []
    except:
        return []

@app.route('/stats', methods=['GET'])
def stats():
    team_name = request.args.get('team_name')
    as_json = request.args.get('format') == 'json'

    if not team_name:
        return make_response('<h2>Ошибка: параметр team_name обязателен</h2>', 400)

    try:
        data = _stats(team_name)
    except Exception as e:
        return make_response(f'<h2>Ошибка при получении данных: {str(e)}</h2>', 500)

    return jsonify(data) if as_json else render_stats_html(data, team_name)

def render_stats_html(data, team_name):
    return make_response(f"""
    <html><body>
        <h1>Статистика команды: {team_name}</h1>
        <ul>
            <li>win: {data[0]}</li>
            <li>lose: {data[1]}</li>
            <li>scored - missed: {data[2]}</li>
        </ul>
    </body></html>
    """, 200)

@app.route('/inf1', methods=['GET'])
def inf1():
    return make_response(f'<h2>{tournament}<h2>', 200)

@app.route('/inf2', methods=['GET'])
def inf2():
    return make_response(f'<h2>{teams}<h2>', 200)

# Аналогично для /versus и /goals:
@app.route('/versus', methods=['GET'])
def versus():
    player1_id = int (request.args.get('player1_id'))
    player2_id = int (request.args.get('player2_id'))

    as_json = request.args.get('format') == 'json'

    if not player1_id or not player2_id:
        return make_response('<h2>Ошибка: нужны оба параметра player1_id и player2_id</h2>', 400)
    if not isinstance(player1_id, int) or not isinstance(player2_id, int):
        return make_response('<h2>Оба числа целыми быть должны</h2>', 400)
    try:
        data = _versus(player1_id, player2_id)
    except Exception as e:
        return make_response(f'<h2>Ошибка: {str(e)}</h2>', 500)

    return jsonify(data) if as_json else render_versus_html(data)

def render_versus_html(data):
    return make_response(f"""
    <html><body>
        <h1>Сравнение игроков</h1>
        <p>Игр друг против друга: {data}</p>
    </body></html>
    """, 200)

@app.route('/goals', methods=['GET'])
def goals():
    player_id = int (request.args.get('player_id'))
    as_json = request.args.get('format') == 'json'

    if not player_id:
        return make_response('<h2>Ошибка: параметр player_id обязателен</h2>', 400)

    try:
        data = _goals(player_id)
    except Exception as e:
        return make_response(f'<h2>Ошибка: {str(e)}</h2>', 500)

    return jsonify(data) if as_json else render_goals_html(data)

def render_goals_html(data):
    return make_response(f"""
    <html><body>
        <p>Забито голов: {data}</p>
    </body></html>
    """, 200)

flag = True

@app.route('/front/stats', methods=['GET', 'POST'])
def front_stats():
    if request.method == "POST":
    # Получаем данные из формы
        team_name = request.form.get("field1")
        if not team_name:
            return "Ошибка: заполните поле!"
        return render_stats_html(_stats(team_name), team_name)

    return '''
        <form method="POST">
            <label for="team_name">имя команды:</label>
            <input type="text" id="field1" name="field1" required><br><br>

            <button type="submit">Отправить</button>
        </form>
    '''

@app.route('/front/versus', methods=["GET", "POST"])
def front_versus():
    if request.method == "POST":
        # Получаем данные из формы
        player1_id = request.form.get("field1")
        player2_id = request.form.get("field2")

        if not player1_id or not player2_id:
            return "Ошибка: оба поля должны быть заполнены!"
        try:
            return render_versus_html(_versus(int(player1_id), int(player2_id)))
        except Exception as e:
            return render_versus_html(0)
    return '''
        <form method="POST">
            <label for="player1_id">id первого игрока:</label>
            <input type="text" id="field1" name="field1" required step="1"><br><br>

            <label for="player2_id">id второго игрока:</label>
            <input type="text" id="field2" name="field2" required step="1"><br><br>

            <button type="submit">Отправить</button>
        </form>
    '''

def preparing():
    post_reason()
    global teams
    global matches
    global tournament
    tournament.clear()
    teams = get_teams()
    matches = get_matches()
    for match in matches:
        team1 = get_team_by_id2(match["team1"])
        team2 = get_team_by_id2(match["team2"])
        if team1 is None or team2 is None or team1 == team2:
            continue
        try:
            tournament[team1["name"]].append([team2["name"], match["team1_score"], match["team2_score"]])
        except KeyError:
            tournament[team1["name"]] = [[team2["name"], match["team1_score"], match["team2_score"]]]
        try:
            tournament[team2["name"]].append([team1["name"], match["team2_score"], match["team1_score"]])
        except KeyError:
            tournament[team2["name"]] = [[team1["name"], match["team2_score"], match["team1_score"]]]
    #print(tournament)
    for team in teams:
        for player_id in team["players"]:
            player = get_player_by_id(player_id)
            if(player == None):
                continue
            try:
                player["team"].append(team["name"])
            except KeyError:
                player["team"] = [team["name"]]
            try:
                player["team_id"] = team["id"]
            except KeyError:
                player["team_id"] = [team["id"]]
            if player not in players:
                players.append(player)
    for match in matches:
        goals = get_goals_by_match_id(match["id"])
        if goals is not None:
            for goal in goals:
                player = get_player_in_match_by_number(match, goal["player"])
                if player is None:
                    continue
                try:
                    player["goals"].append({"match": match["id"], "time": goal["minute"]})
                except Exception as e:
                    player["goals"] = [{"match": match["id"], "time": goal["minute"]}]
    return

def sorted_players():
    global players
    sorted_players = sorted(players, key=lambda p: (p['name'], p['surname']))
    sorted_players2 = sorted(players, key=lambda p: (p['id']))
    players = sorted_players2
    for player in sorted_players:
        print(player["name"], player["surname"], player["team_id"], player["team"])
    return

def f():
    for player in players:
        try:
            print(player["goals"])
        except KeyError:
            print("[]")

def data_updating():
    while True:
        preparing()
        time.sleep(600)

def main():
    preparing()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    

if __name__ == "__main__":
    main()


