import requests
from bs4 import BeautifulSoup
import re

def get_json_data(markets):
    #change according to what data
    API_KEY = 'YOUR_API_KEY'
    SPORT = 'upcoming'
    REGIONS = 'us'
    if markets == 1:
        MARKETS = 'h2h'
    elif markets == 2:
        MARKETS = 'spreads'
    elif markets == 3:
        MARKETS = 'h2h,spreads'
    else:
        return 'Invalid markets'
    ODDS_FORMAT = 'decimal'
    DATE_FORMAT = 'iso'
    #get sports response
    odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?apiKey={API_KEY}&regions=us&markets={MARKETS}&oddsFormat=american',
    params={
        'api_key': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
    }
    )
    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')
    else:
        odds_json = odds_response.json()
        # print('Number of events:', len(odds_json))
        # Check the usage quota
        #print('Remaining requests', odds_response.headers['x-requests-remaining'])
        #print('Used requests', odds_response.headers['x-requests-used'])
        return odds_json
    
def get_data_array(data):
    data_array = []
    for game in data:
        game_id = game['id']
        sport_key = game['sport_key']
        sport_title = game['sport_title']
        commence_time = game['commence_time']
        home_team = game['home_team']
        away_team = game['away_team']
        for bookmaker in game['bookmakers']:
            if bookmaker['key'] == 'draftkings':  # Check if the bookmaker is DraftKings
                bookmaker_key = bookmaker['key']
                bookmaker_title = bookmaker['title']
                last_update = bookmaker['last_update']

                for market in bookmaker['markets']:
                    market_key = market['key']
                    last_update_market = market['last_update']
                    outcomes = market['outcomes']

                    first_outcome = outcomes[0]
                    point = first_outcome.get('point')
                    team1 = first_outcome.get('name')
                    second_outcome = outcomes[1]
                    team2 = second_outcome.get('name')
                    data_array.append([team1, team2, point])
                    if len(data_array) == 14:
                        # catch max games
                        return data_array
                    for outcome in outcomes:
                        team_name = outcome['name']
                        price = outcome.get('price')
                        point = outcome.get('point')

                        #print(f"Team: {team_name}")
                        #print(f"Price: {price}")
                        #print(f"Point: {point}")

    return data_array
   
def format_spread_data(data):
    new_data = []
    for item in data:
        first_team_space = item[0].rindex(' ')
        item[0] = item[0][first_team_space:].strip()
        second_team_space = item[1].rindex(' ')
        item[1] = item[1][second_team_space:].strip()
        point = item[2]
        if point > 0:
            #now formatted as [winning team, losing team, spread]
            item[0], item[1] = item[1], item[0]
        new_data.append([item[0], item[1], abs(point)])
    return new_data   
            
def print_data_array(data_array):
    for item in data_array:
        point = item[2]
        print(f"{item[0]} vs {item[1]}, {item[0]} favored by {point} points")
        
def get_fpi_predictions(fpi_url):
    url = fpi_url
    # Send a GET request to the URL pretending to be a browser (not doing this leads to 403 error)
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all text within HTML tags
        all_text = ' '.join(tag.get_text() for tag in soup.find_all())

        # Use regular expression to find patterns like "FPI favorite: ..."
        pattern = r'FPI favorite:\s*([\w\s]+?[\d.]+)\s*\(([\d.]+%)\s*to\s*win\s*outright\)'
        matches = re.findall(pattern, all_text)
        entries = []
        # Print or store the matched patterns
        for match in matches:
            # entry in format (winning team, exp points over, chance of winning)
            by_index = match[0].index('by')
            winning_team = match[0][0:by_index-1]
            exp_points = match[0][by_index+3:]
            winning_chance = match[1][0:-1]
            entry = [winning_team, exp_points, winning_chance]
            entries.append(entry)
        entries = list(set(map(tuple, entries)))
        return entries
    else:
        print(f'Failed to retrieve the webpage. Status code: {response.status_code}')  
          
def print_entries(entries):
    for entry in entries:
        print(f'{entry[0]} favored to win by {entry[1]}. ({entry[2]}% chance to win outright)')
        
def combine_spread_and_fpi(spreads, fpi):
    to_return = []
    # spreads formatted - (winning team, losing team, point spread )
    # fpi formatted - (winning team, expected points)
    for spread in spreads:
        # look for fpi
        diff = None
        for fpi_pred in fpi:
            if fpi_pred[0] == spread[0]:
                diff = round(spread[2] - float(fpi_pred[1]), 1)
            elif fpi_pred[0] == spread[1]:
                diff = round(float(fpi_pred[1]) - spread[2], 1)
        to_return.append([spread[0], spread[1], diff])
    return to_return

def sort_diffs(diffs):
    diffs = sorted(diffs, key=lambda x: abs(x[2]), reverse=True)
    return diffs

def print_betters(betters):
    for better in betters:
        print(f"{better[0]} and {better[1]} with {better[2]}")
        
def print_suggested_bets(diffs, num):
    i = 0
    while i < num:
        print_one_bet(diffs[i])
        i = i + 1
        
def print_one_bet(bet):
    if bet[2] > 0:
        print(f'In the {bet[0]} vs {bet[1]} game, you should bet for {bet[1]} to cover as the FPI prediction and DraftKings spread differs by {bet[2]}.') 
    elif bet[2] < 0:
        print(f'In the {bet[0]} vs {bet[1]} game, you should bet for {bet[0]} to cover as the FPI prediction and DraftKings spread differs by {bet[2] * -1}.') 
    else:
        print(f'In the {bet[0]} vs {bet[1]} game, you should not bet as the FPI prediction and DraftKings spread are equal.') 
     
def main():          
    data = get_json_data(2)
    data_array = get_data_array(data)
    data_array = format_spread_data(data_array)
    url = 'URL' # in format like https://www.espn.com/espn/betting/story/_/id/39187320/week-17-nfl-games-betting-odds-lines-picks-spreads-more
    entries = get_fpi_predictions(url)
    diff_between_fpi_spreads = combine_spread_and_fpi(data_array, entries)
    diff_between_fpi_spreads = sort_diffs(diff_between_fpi_spreads)    
    num_bets = input('Enter num of suggested bets: ')
    num_bets = int(num_bets)
    print('-'*30)
    print_suggested_bets(diff_between_fpi_spreads, num_bets)
    print_all_output = input('Do you want the DraftKing odds and FPI predictions (Enter Y/N): ')
    if print_all_output == 'Y':
        print('-'*30)
        print('DraftKings odds (-110)')
        print('-'*30)
        print_data_array(data_array)
        print('=' * 30)
        print('FPI Predictions')
        print('-' * 30)
        print_entries(entries)
    print('Thanks for using')
        
main()
