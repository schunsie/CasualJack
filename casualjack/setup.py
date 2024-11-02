import functools
from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)

from random import shuffle

bp = Blueprint('setup', __name__, url_prefix='/setup')

@bp.route('/start', methods=['GET', 'POST'])
def set_chips():
    if request.method == 'POST':
        chips = request.form['chips']
        error = None

        try:
            chips = int(chips)
        except ValueError:
            error = 'Chips does not represent a valid integer'
        except TypeError:
            error = 'Chips can not be empty'
        else: 
            if chips <= 0 or chips > 9999:
                error = 'Chips outside allowed range'
            

        if error is None:
            session.clear()
            session['chips'] = chips
            session['deck'] = shuffle_deck()
            
            # remembers the index of the next card out of session['deck'] that is to be played
            session['pnt_card'] = 0
            return redirect(url_for('index'))

        flash(error)

    return render_template('setup/start.html')


@bp.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('setup.set_chips'))


def chips_required(view):
    '''
    Returns wrapped function or function, depending on conditions met. 

    Used as a decorator function to only allow access to the underlying function
    when the user has a valid entry of 'chips' within their session data.  
    '''
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('chips') is None or session.get('chips') < 0:
            return redirect(url_for('setup.set_chips'))
        
        return view(**kwargs)
    
    return wrapped_view


def shuffle_deck():
    '''
    Returns a list

    Creates a deck of 53 succeeding integers [0, 52] and shuffles the sequence before returning it.
    Equivalent to shuffling a deck of playing cards. 
    '''
    deck = list(range(0, 52))
    shuffle(deck)
    return deck