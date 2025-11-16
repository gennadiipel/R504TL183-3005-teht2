# main.py
# etusivun route

from flask import Flask, render_template, request, redirect, url_for
import contextlib, sqlite3

app = Flask(__name__)


@app.route('/')
def index():
    # tämä rivi saa palvelimen generoimaan index.html-sivun ja lähettämään sen vastauksena selaimelle
    return render_template('index.html')

@contextlib.contextmanager
def connect():
    conn = None
    try:
        conn = sqlite3.connect('users.sqlite')
        yield conn
    finally:
        if conn is not None:
            conn.close()

# _get_users

# erillinen funktio käyttäjien noutamiselle tietokannasta,
# koska tarvitaan useammassa paikassa
def _get_users(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT users.id, users.name, users.email, departments.name FROM users INNER JOIN departments ON departments.id = users.department_id")
    _users = cur.fetchall()
    users_list = []
    for u in _users:
        users_list.append({'id': u[0], 'name': u[1], 'email': u[2], 'department': u[3]})
    return users_list

# GET-metodilla haetaan käyttäjät tietokannasta ja palautetaan selaimelle valmis sivu
# jossa käyttäjät listattuna
@app.route('/users', methods=['GET'])
def get_users():
    with connect() as con:
        _users = _get_users(con)

        return render_template('users/index.html', users=_users, error=None)
    
# tähän tullaan, kun formiseta painetaan, Delete-nappia
@app.route('/users', methods=['POST'])
def delete_user():
    # request.form-sisältää tiedot, jotka formilla lähetetään palvelimelle
    _body = request.form
    with connect() as connection:
        try:
            # haetaan userid form datasta
            # userid on formin hidden-inputin name-attribuutin arvo
            userid = _body.get('userid')
            if userid is None:
                raise Exception('missing userid')

            # jos tämä epäonnistuu, tulee ValueError
            userid = int(userid)
            cursor = connection.cursor()
            # jos kaikki onnistuu,
            # poistetaan valittu käyttäjä tietokannasta
            # ja ladataan sivu kokonaan uudelleen
            cursor.execute('DELETE FROM users WHERE id = ?', (userid,))
            connection.commit()
            cursor.close()
            return redirect(url_for('get_users'))

        # valueError-exception tulee silloin
        # jos userid-kenttä ei sisällä numeerista arvoa
        # (ei voida muuttaa kentän arvoa integeriksi)
        except ValueError as e:

            connection.rollback()
            # haetaan käyttäjät ja ladataan sivu uudelleen
            _users = _get_users(connection)
            return render_template('users/index.html', error=str(e), users=_users)

        except Exception as e:
            # haetaan käyttäjät ja ladataan sivu uudelleen
            _users = _get_users(connection)
            connection.rollback()
            return render_template('users/index.html', error=str(e), users=_users)

# GET-metodilla ladataan uuden käyttäjän listäystä varten tehty sivu

def _get_departments(conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM departments')
    _departments = cur.fetchall()
    departments_list = []
    for d in _departments:
        departments_list.append({'id': d[0], 'name': d[1]})
    cur.close()
    return departments_list


@app.route('/users/new', methods=['GET'])
def new_user():
    with connect() as con:
        _departments = _get_departments(con)
        return render_template('users/new.html', departments=_departments, error=None)

# POST-metodilla lisätään käyttäjän tiedot lomakkeelta tietokantaan

@app.route('/users/new', methods=['POST'])
def add_user():
    _body = request.form
    with connect() as con:

        try:
            cur = con.cursor()
            cur.execute('INSERT INTO users (name, email, department_id) VALUES (?, ?, ?)',
                        (_body.get('name'), _body.get('email'), _body.get('department_id')))
            con.commit()
            # kun käyttäjä on lisätty tietokantaan, ohjataan selain takaisin käyttäjälistauksen sivulle
            return redirect(url_for('get_users'))
        except Exception as e:
            con.rollback()
            # jos tulee virhe, haetaan departmentit uudelleen ja näytetään lisäksi virhe käyttäjälle
            _departments = _get_departments(con)
            return render_template('users/new.html', error=str(e), departments=_departments)


# departments koodi


# osastojen listaus (7p)
def _get_departments(conn):
    cur = conn.cursor()
    cur.execute("SELECT d.id, d.name, COUNT(u.id) as users_count FROM departments d LEFT JOIN users u ON d.id = u.department_id GROUP BY d.id, d.name")
    _departments = cur.fetchall()
    departments_list = []
    for d in _departments:
        departments_list.append({'id': d[0], 'name': d[1], 'users_count': d[2]})
    return departments_list

@app.route('/departments', methods=['GET'])
def get_departments():
    with connect() as con:
        _departments = _get_departments(con)
        return render_template('departments/index.html', departments=_departments, error=None)
    
# uuden osaston lisäys (7p)
@app.route('/departments/new', methods=['GET'])
def new_department():
    with connect() as con:
        return render_template('departments/new.html', error=None)

@app.route('/departments/new', methods=['POST'])
def add_department():
    _body = request.form
    with connect() as con:

        try:
            cur = con.cursor()
            cur.execute('INSERT INTO departments (name) VALUES (?)', (_body.get('name'), ))
            con.commit()
            return redirect(url_for('get_departments'))
        
        except Exception as e:
            con.rollback()
            return render_template('departments/new.html', error=str(e))



if __name__ == '__main__':
    app.run(port=5001, debug=True)
