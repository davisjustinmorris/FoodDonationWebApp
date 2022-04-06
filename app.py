from flask import Flask, request, session, redirect, url_for, render_template
import sqlite3

from db_logic import DbManager
import common_code

app = Flask(__name__)
app.config['SECRET_KEY'] = '<didac|ribot>'


def get_db_connection():
    conn = sqlite3.connect('data.sqlite')
    return conn


db_man = DbManager(connection_provider=get_db_connection)


@app.before_request
def before_each_req():
    if request.endpoint in ['handle_user_dashboard', 'handle_admin_dashboard', 'handle_super_admin']:
        auth_token = session.get('auth_token')
        if auth_token:
            session_check_response = db_man.get_logged_in_account(auth_token=auth_token)
            if session_check_response.get('status'):
                session['user_info'] = session_check_response['data']
            else:
                session.clear()
                return redirect(url_for('handle_login'))


@app.route('/')
def handle_root():
    return redirect(url_for('handle_login'))


@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        task = request.form.get('task')
        user_name = request.form.get('name')
        user_email = request.form.get('email')
        user_password = request.form.get('password')
        is_volunteer = 1 if request.form.get('is_volunteer') else 0

        if task == 'login':
            login_result = db_man.put_login_session(email=user_email, pwd=user_password)
            if login_result.get('status'):
                session['user_info'] = login_result['data']
            else:
                # todo: the failed login message can be captured and the detailed response can be sent to the user
                return render_template('login.html', refresh_message="Login failed!")

        elif task == 'signup':
            signup_result = db_man.add_login_info(email=user_email, pwd=user_password, name=user_name,
                                                  is_vol=is_volunteer)
            if signup_result.get('status'):
                refresh_message = "Signup successful! Login to your account"
            else:
                refresh_message = signup_result.get('error')

            return render_template('login.html', refresh_message=refresh_message)

    if session.get('user_info', {}).get('user_type') == 'normal_user':
        return redirect(url_for('handle_user_dashboard'))
    elif session.get('user_info', {}).get('user_type') == 'volunteer':
        return redirect(url_for('handle_volunteer_dashboard'))
    elif session.get('user_info', {}).get('user_type') == 'super_admin':
        return redirect(url_for('handle_super_admin'))

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def handle_user_dashboard():
    """Homepage of users"""
    if request.method == 'POST':
        # fk_creator_uid                    - check
        # created_ts                        - check
        # last_updated_ts                   - not required
        # request_status                    - check
        # review_rating                     - not required
        # review_feedback                   - not required
        # fk_handled_vol_id                 - not required
        # is_donate_req                     - check
        # req_qty_in_person                 - check
        # contact_details_same_as_user      - check
        # contact_phone                     - check
        # location_as_address               - check
        required_form_keys = [
            'is_donate_req', 'req_qty_in_person', 'contact_details_same_as_user', 'contact_phone', 'location_as_address'
        ]
        payload = {key: request.form.get(key) for key in required_form_keys}
        payload['contact_details_same_as_user'] = 1 if payload['contact_details_same_as_user'] else 0
        payload['fk_creator_uid'] = session['user_info']['uid']
        payload['created_ts'] = common_code.get_ist()
        payload['request_status'] = 'created'

        db_man.create_donor_request(payload=payload)
        return 'req created<br><a href="/">Back to page</a>'

    return render_template('user_dashboard.html')


@app.route('/volunteer_dashboard')
def handle_volunteer_dashboard():
    """Homepage for volunteers"""
    return 'Hello Volunteer!'


@app.route('/super_admin')
def handle_super_admin():
    """Homepage for super admins"""
    return 'Hello Super Man!'


@app.route('/logout')
def handle_logout():
    token = session.get('user_info', {}).get('auth_token')
    if token:
        db_man.del_login_session(token=token)
    session.clear()
    return redirect(url_for('handle_login'))


if __name__ == '__main__':
    app.run(debug=True)
