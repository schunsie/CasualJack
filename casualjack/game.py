from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, session
)
import random

from casualjack.setup import chips_required, shuffle_deck

bp = Blueprint('game', __name__)

@bp.route('/', methods=['GET', 'POST'])
@chips_required
def index():
    winner = None
    
    # if round has not yet begun
    if session.get('bet') == None and session['chips'] != 0:
        error = None
        
        if request.method == 'POST':
            bet = request.form.get('bet')
            try:
                bet = int(bet)
            except ValueError or TypeError:
                error = 'Invalid bet made'
            else:
                if bet <= 0 or bet > session['chips']:
                    error = 'Unable to pay bet'
            
            if error is None:
                session['bet'] = bet
                session['chips'] -= bet
                return redirect(url_for('index'))

            flash(error)
    
    # if round has begun (read: bet has been made)
    else:
        if not session.get('hands'):
            # configure initial hands for the round
            dealer_cards = deal_card(1)
            player_cards = deal_card(2)

            session['stand'] = False
            
            session['hands'] = {
                'cards_dealer' : dealer_cards,
                'cards_player' : player_cards,
                'totals' : {
                    'dealer' : hand_total(dealer_cards),
                    'player' : hand_total(player_cards)
                }
            }

        # determine winner outcome
        if session['hands']['totals']['player'] > 21:
            return(render_template("game/index.html", bust=True))
        elif session['stand']:
            dealer_pull()
            winner = determine_winner(session['hands']['totals'])
            match winner:
                case 'player':
                    session['chips'] += session['bet'] * 2
                case 'tie':
                    session['chips'] += session['bet']
            
            # removes bet so conditions are met for new round to start
            session.pop('bet')
                    
    return render_template('game/index.html', winner=winner)
    

def deal_card(n):
    '''
    Takes an integer n and returns a list
    
    Retrieves the sequence of card numbers named 'deck' within the session data in combination
    with the pointer to the next card

    Determines if the next card exceeds the limits of the playing deck. If so,
    calls function to create new deck

    Subsequently takes n numbers from deck list, and returns the numbers as a list of
    dictionaries containing information about the cards
    
    '''

    # determine if whole deck has been played
    if session['pnt_card'] + n > len(session['deck']):
        # if so, create new deck and reset card pointer
        session['deck'] = shuffle_deck()
        session['pnt_card'] = 0
        print('new deck')

    if n == 1:
        card_nums = [session['deck'][session['pnt_card']]]
        session['pnt_card'] += 1
    else:
        card_nums = session['deck'][session['pnt_card']:(session['pnt_card']+n)]
        session['pnt_card'] += n
    
    cards = []

    # TODO: determine if redundancy can be reduced if using objects for cards
    for card_num in card_nums:
        # divide by 13 to distinguish the different suits: each suit has 13 cards. 
        match int(card_num/13):
            # first 13 cards
            case 0:
                cards.append({
                    'suit' : 'heart',
                    'suit_uni' : '&#9829;',
                    'value' : valuate_card(card_num),
                    'value_num' : valuate_card(card_num, True)
                })
            # second 13 cards
            case 1:
                cards.append({
                    'suit' : 'diamond',
                    'suit_uni' : '&#9830;',
                    'value' : valuate_card(card_num),
                    'value_num' : valuate_card(card_num, True)
                })
            # etc. 
            case 2:
                cards.append({
                    'suit' : 'spade',
                    'suit_uni' : '&#9824;',
                    'value' : valuate_card(card_num),
                    'value_num' : valuate_card(card_num, True)
                })
            case 3:
                cards.append({
                    'suit' : 'club',
                    'suit_uni' : '&#9827;',
                    'value' : valuate_card(card_num),
                    'value_num' : valuate_card(card_num, True)
                })

    return cards


def valuate_card(card_num, numeric=False):
    # retrieve relative card_number, unaffected by suit
    value = card_num % 13

    # determine if value has to be returned as a numerical value
    # or as face card name / ace
    if numeric == False:
        match value:
            case 0:
                return 'A' # Ace
            case 10:
                return 'J' # Jack
            case 11:
                return 'Q' # Queen
            case 12:
                return 'K' # King
            case _:
                return value
    else:
        if value == 0:
            return 11
        elif value == 11 or value == 12:
            return 10
        return value
    

def hand_total(cards):
    return sum([card['value_num'] for card in cards])


@bp.route('/game/hit')
@chips_required
def hit():
    session['hands']['cards_player'] += deal_card(1)
    session['hands']['totals']['player'] = hand_total(session['hands']['cards_player'])
    return redirect(url_for('index'))


def dealer_pull():
    # dealer stands on 17 and above
    if session['hands']['totals']['dealer'] >= 17:
        return 
    # dealer hits till at least 16: another hit is determined at random
    elif session['hands']['totals']['dealer'] == 16 and bool(random.getrandbits(1)):
        return
    
    session['hands']['cards_dealer'] += deal_card(1)
    session['hands']['totals']['dealer'] = hand_total(session['hands']['cards_dealer'])
    dealer_pull()


@bp.route('/game/stand')
@chips_required
def stand():
    session['stand'] = True
    return redirect(url_for('index'))


@bp.route('/game/next')
@chips_required
def next():
    if session.get('bet'):
        session.pop('bet')
    session.pop('hands')
    session['stand'] = False
    return redirect(url_for('index'))


def determine_winner(totals):
    if totals['dealer'] > 21 or totals['player'] > totals['dealer']:
        return 'player'
    elif totals['dealer'] == totals['player']:
        return 'tie'
    else: 
        return 'dealer'