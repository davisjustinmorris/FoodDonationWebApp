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
            conn.close()
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
            
        return {'status': False}

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

    def add_login_info(self, email, pwd, name, is_vol, phone, address):
        """Signup"""
        query_insert = "INSERT INTO user_table (email, password, name, is_volunteer, phone, address) " \
                       "VALUES (?,?,?,?,?,?)"
        query_check_email = "SELECT pk_uid, name FROM user_table WHERE email=?"

        conn = self.connection_provider()
        email_exists = conn.execute(query_check_email, (email,)).fetchone()
        if not email_exists:
            conn.execute(query_insert, (email, pwd, name, is_vol, phone, address))
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
        query_insert = "INSERT INTO request_table " \
                       "(fk_creator_uid, created_ts, last_updated_ts, request_status, " \
                       "review_rating, review_feedback, fk_handled_vol_id, is_donate_req, req_qty_in_person, " \
                       "contact_details_same_as_user, contact_phone, location_as_address) " \
                       "VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
        conn = self.connection_provider()
        conn.execute(query_insert, (
            payload.get('fk_creator_uid'),
            payload.get('created_ts'),
            payload.get('last_updated_ts'),
            payload.get('request_status'),
            payload.get('review_rating'),
            payload.get('review_feedback'),
            payload.get('fk_handled_vol_id'),
            payload.get('is_donate_req'),
            payload.get('req_qty_in_person'),
            payload.get('contact_details_same_as_user'),
            payload.get('contact_phone'),
            payload.get('location_as_address')
        ))
        conn.commit()
        conn.close()

    def get_users_requests(self, uid=None, limit=20, active=True, state='created'):
        get_query = "SELECT pk_rid, fk_creator_uid, created_ts, last_updated_ts, request_status, " \
                    "review_rating, review_feedback, fk_handled_vol_id, is_donate_req, req_qty_in_person, " \
                    "contact_details_same_as_user, contact_phone, location_as_address, ut.phone, ut.address " \
                    "FROM request_table " \
                    "LEFT JOIN user_table ut ON ut.pk_uid = request_table.fk_creator_uid "
        query_args = list()
        if uid:
            get_query += "WHERE fk_creator_uid=? "
            query_args.append(uid)
        if limit:
            get_query += "LIMIT ? "
            query_args.append(limit)

        conn = self.connection_provider()
        get_result = conn.execute(get_query, tuple(query_args)).fetchall()
        conn.close()

        result_obj_list = [
            {
                'pk_rid': item[0],
                'fk_creator_uid': item[1],
                'created_ts': item[2],
                'last_updated_ts': item[3],
                'request_status': item[4],
                'review_rating': item[5],
                'review_feedback': item[6],
                'fk_handled_vol_id': item[7],
                'is_donate_req': item[8],
                'req_qty_in_person': item[9],
                'contact_details_same_as_user': item[10],
                'contact_phone': item[11],
                'location_as_address': item[12],
                'ut_contact_phone': item[13],
                'ut_address': item[14]
            }
            for item in get_result
        ]
        # evaluate phone and address based on <contact_details_same_as_user> value
        for item in result_obj_list:
            item['this_contact_phone'] = item['ut_contact_phone'] if item['contact_details_same_as_user'] else item['contact_phone']
            item['this_contact_address'] = item['ut_address'] if item['contact_details_same_as_user'] else item['location_as_address']

        result_obj = {
            'created': [],
            'confirmed': [],
            'delivered': [],
            'reviewed': []
        }
        for item in result_obj_list:
            status = item.get('request_status')
            result_obj[status].append(item)

        return result_obj

    def connect_user_requests(self, volunteer_uid, donor_req_id, receive_req_id):
        assert volunteer_uid and donor_req_id and receive_req_id, "insufficient data to process request"

        query_connect_reqs = "INSERT INTO matched_request_map (fk_rid_donate, fk_rid_receive) VALUES (?, ?)"
        query_mark_req_confirm = "UPDATE request_table " \
                                 "SET last_updated_ts=?, request_status=?, fk_handled_vol_id=? " \
                                 "WHERE pk_rid=? "

        conn = self.connection_provider()

        conn.execute(query_connect_reqs, (donor_req_id, receive_req_id))

        common_args = (common_code.get_ist(), 'confirmed', volunteer_uid)
        conn.executemany(query_mark_req_confirm, [common_args+(pk_rid,) for pk_rid in [donor_req_id, receive_req_id]])

        conn.commit()
        conn.close()

    def user_mark_delivered(self, receive_req_id):
        query_get_donor_req_id = "SELECT fk_rid_donate FROM matched_request_map WHERE fk_rid_receive=?"
        query_mark_delivered = "UPDATE request_table SET request_status=? WHERE pk_rid=?"

        conn = self.connection_provider()
        query_res_donor_req_id = conn.execute(query_get_donor_req_id, (receive_req_id,)).fetchone()
        assert query_res_donor_req_id

        donate_req_id = query_res_donor_req_id[0]
        conn.executemany(query_mark_delivered, [('delivered', donate_req_id), ('delivered', receive_req_id)])
        conn.commit()
        conn.close()
