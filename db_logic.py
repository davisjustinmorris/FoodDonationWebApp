import common_code


class DbManager:
    def __init__(self, connection_provider):
        self.connection_provider = connection_provider

    def get_logged_in_account(self, auth_token=None, uid=None):
        query_from_token = "SELECT pk_uid, is_volunteer, is_super_admin " \
                           "FROM user_table WHERE session_token=?"
        if auth_token:
            conn = self.connection_provider()
            account_info_res = conn.execute(query_from_token, (auth_token,)).fetchone()
            if account_info_res:
                user_id, is_volunteer, is_super_admin = account_info_res

                if is_super_admin:
                    user_type = "super_admin"
                elif is_volunteer:
                    user_type = "volunteer"
                else:
                    user_type = "normal_user"

                return {
                    'status': True,
                    'data': {
                        'uid': user_id,
                        'user_type': user_type,
                        'auth_token': auth_token
                    }
                }

    def put_login_session(self, email, pwd):
        """Login (& update token)"""
        query_check_email = "SELECT pk_uid, password, is_volunteer, is_super_admin FROM user_table WHERE email=?"
        query_insert = "UPDATE user_table SET session_token = ? WHERE email=?"

        conn = self.connection_provider()
        account_info_result = conn.execute(query_check_email, (email,)).fetchone()
        if account_info_result:
            uid, saved_password, is_volunteer, is_super_admin = account_info_result
            if saved_password == pwd:
                session_token = common_code.get_random()            # todo: ensure toke does not already exist in table
                conn.execute(query_insert, (session_token, email))
                conn.commit()
                conn.close()

                if is_super_admin:
                    user_type = "super_admin"
                elif is_volunteer:
                    user_type = "volunteer"
                else:
                    user_type = "normal_user"

                return {
                    'status': True,
                    'data': {
                        'uid': uid,
                        'user_type': user_type,
                        'auth_token': session_token
                    }
                }

        conn.close()
        return {'status': False}

    def del_login_session(self, uid=None, token=None):
        """Logout"""
        query_del_token_by_token = "UPDATE user_table SET session_token=null WHERE session_token=?"
        query_del_token_by_uid__ = "UPDATE user_table SET session_token=null WHERE pk_uid=?"

        query = query_del_token_by_token if token else query_del_token_by_uid__
        param = (token if token else uid)
        conn = self.connection_provider()
        conn.execute(query, (param,))
        conn.commit()
        conn.close()

    def add_login_info(self, email, pwd, name, is_vol):
        """Signup"""
        query_insert = "INSERT INTO user_table (email, password, name, is_volunteer) " \
                       "VALUES (?,?,?,?) "
        query_check_email = "SELECT pk_uid, name FROM user_table WHERE email = ?"

        conn = self.connection_provider()
        email_exists = conn.execute(query_check_email, (email,)).fetchone()
        if not email_exists:
            conn.execute(query_insert, (email, pwd, name, is_vol))
            conn.commit()
            conn.close()
            return {'status': True}
        else:
            conn.close()
            print(f'Account already exists for email: {email} with uid: {email_exists[0]} and name: {email_exists[1]}')
            return {'status': False, 'error': 'Account already exists for that email'}

    def edit_login_info(self, email, pwd):
        """Reset password"""
        return

    def create_donor_request(self, payload):
        return
