from flask import Flask, request, session, redirect, url_for, render_template
import sqlite3

from db_logic import DbManager
import common_code
import symbols as sym

app = Flask(__name__)
app.config['SECRET_KEY'] = '<didac|ribot>'

# ----- REMINDERS -----
# SESSION['user_info'] = {
#     'uid': uid,
#     'user_type': user_type,
#     'auth_token': session_token
# }


def get_db_connection():
    conn = sqlite3.connect('data.sqlite')
    return conn


db_man = DbManager(connection_provider=get_db_connection)


@app.before_request
def before_each_req():
    if request.endpoint in ['handle_user_dashboard', 'handle_admin_dashboard', 'handle_super_admin']:
        auth_token = session.get('user_info', {}).get('auth_token')
        if auth_token:
            session_check_response = db_man.get_logged_in_account(auth_token=auth_token)
            if session_check_response.get('status'):
                session['user_info'] = session_check_response['data']
                return

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
        phone = request.form.get('phone')
        address = request.form.get('address')
        interested_in_volunteering = 1 if request.form.get('interested_in_volunteering') else 0

        if task == 'login':
            login_result = db_man.put_login_session(email=user_email, pwd=user_password)
            if login_result.get('status'):
                session['user_info'] = login_result['data']
            else:
                # todo: the failed login message can be captured and the detailed response can be sent to the user
                return render_template('login.html', refresh_message="Login failed!")

        elif task == 'signup':
            signup_result = db_man.add_login_info(
                email=user_email, pwd=user_password, name=user_name, is_vol=is_volunteer, phone=phone, address=address,
                interested_in_volunteering=interested_in_volunteering
            )
            if signup_result.get('status'):
                refresh_message = "Signup successful! Login to your account"
            else:
                refresh_message = signup_result.get('error')

            return render_template('login.html', refresh_message=refresh_message)

    if session.get('user_info', {}).get('user_type') == sym.UserType.NORMAL_USER:
        return redirect(url_for('handle_user_dashboard'))
    elif session.get('user_info', {}).get('user_type') == sym.UserType.VOLUNTEER:
        return redirect(url_for('handle_volunteer_dashboard'))
    elif session.get('user_info', {}).get('user_type') == sym.UserType.SUPER_ADMIN:
        return redirect(url_for('handle_super_admin'))

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def handle_user_dashboard():
    """Homepage of users"""
    if request.method == 'POST':

        if request.form.get('task') == 'create-request':
            required_form_keys = [
                'is_donate_req', 'req_qty_in_person', 'contact_details_same_as_user', 'contact_phone',
                'location_as_address', 'is_veg'
            ]
            payload = {key: request.form.get(key) for key in required_form_keys}
            payload['contact_details_same_as_user'] = 1 if payload['contact_details_same_as_user'] else 0
            payload['fk_creator_uid'] = session['user_info']['uid']
            payload['created_ts'] = common_code.get_ist()
            payload['request_status'] = 'created'

            db_man.create_donor_request(payload=payload)
            return redirect(url_for('handle_user_dashboard'))

        print('getting inbound json')
        if request.is_json:
            inbound_data = request.get_json()
        else:
            inbound_data = {}
        print(inbound_data)

        if inbound_data.get('task') == 'mark-confirmed-tickets-delivered':
            print('handle_user_dashboard: form data dump of task "mark-delivered"> ' + str(inbound_data))

            if db_man.check_user_authority_and_ticket_state(session['user_info']['uid'], inbound_data.get('payload')):
                db_man.mark_confirmed_tickets_delivered(inbound_data.get('payload'))
                return {'success': True}

            return {'success': False, 'err': "Check for user access or condition for ticket state failed!"}

        elif request.form.get('task') == 'submit-feedback':
            print('handle_user_dashboard: form data dump of task "submit-feedback"> ' + str(dict(request.form)))
            db_man.user_put_review(
                request.form.get('req_id'),
                request.form.get('rating_value'),
                request.form.get('review')
            )
            return 'Review added<br><a href="/">Back to page</a>'

    uid = session['user_info']['uid']
    return render_template(
        'user_dashboard.html',
        payload=db_man.get_users_requests(uid=uid),
        user_type=session['user_info']['user_type']
    )


@app.route('/donors_summary', methods=['GET', 'POST'])
def handle_donor_summary():
    """Page for donors summary"""

    user_type = session['user_info']['user_type']
    if user_type not in ['super_admin', 'volunteer']:
        return 'You dont have permission to view this page!<br><a href="/">Back Home</a>'

    return render_template(
        'donors_summary.html',
        user_type=session['user_info']['user_type'],
        donors=db_man.get_donor_review_avg()
    )


@app.route('/donor_details/<donor_uid>', methods=['GET', 'POST'])
def handle_donor_details(donor_uid):
    """Page for donor details"""

    user_type = session['user_info']['user_type']
    if user_type not in ['super_admin', 'volunteer']:
        return 'You dont have permission to view this page!<br><a href="/">Back Home</a>'

    return render_template(
        'donor_details.html',
        user_type=session['user_info']['user_type'],
        payload=db_man.get_donor_specific_review_details(donor_uid)
    )


@app.route('/volunteer_dashboard', methods=['GET', 'POST'])
def handle_volunteer_dashboard():
    """Homepage for volunteers"""

    user_type = session['user_info']['user_type']
    if user_type not in ['super_admin', 'volunteer']:
        return 'You dont have permission to view this page!<br><a href="/">Back Home</a>'

    if request.method == 'POST':
        print('handle_volunteer_dashboard: connect open request > form data dump >')
        inbound_data = dict(request.get_json())
        print(inbound_data)

        if inbound_data.get('task') == 'connect-open-requests':
            return db_man.connect_user_requests(session['user_info']['uid'], inbound_data.get('payload'))

        elif inbound_data.get('task') == 'mark-confirmed-tickets-delivered':
            db_man.mark_confirmed_tickets_delivered(inbound_data.get('payload'))
            return {'success': True}

    return render_template(
        'volunteer_dashboard.html',
        payload=db_man.get_users_requests(),
        user_type=session['user_info']['user_type']
    )


@app.route('/super_admin', methods=['GET', 'POST'])
def handle_super_admin():
    """Homepage for super admins"""

    user_type = session['user_info']['user_type']
    if user_type != 'super_admin':
        return 'You dont have permission to view this page!<br><a href="/">Back Home</a>'

    if request.method == 'POST':
        task = request.form.get('task')
        target_user_list = request.form.getlist('pk_uid')

        print('handle_super_admin: form data dump >')
        payload = dict(request.form)
        print(payload)
        print('user_list: ' + str(target_user_list))

        if task in ['add-to-volunteers', 'remove-from-volunteers']:
            as_volunteer = task == 'add-to-volunteers'
            db_man.super_admin__edit_type_volunteers(
                user_list=target_user_list,
                as_volunteer=as_volunteer
            )
        else:
            return

    return render_template(
        'super_admin.html',
        payload={'users': db_man.super_admin__get_users()},
        user_type=session['user_info']['user_type']
    )


@app.route('/logout')
def handle_logout():
    token = session.get('user_info', {}).get('auth_token')
    if token:
        db_man.del_login_session(token=token)
    session.clear()
    return redirect(url_for('handle_login'))


if __name__ == '__main__':
    app.run(debug=True)
