import pymysql.cursors, os, inspect
path = os.path.abspath(inspect.getfile(inspect.currentframe()))
currentdir = os.path.dirname(path)

mysql_pw = ""

class bankDB:

    def __init__(self):
        # Connect
        self.conn = pymysql.connect('127.0.0.1', 'root', mysql_pw, 'bankDB', 
                                    port = 4406,
                                    cursorclass=pymysql.cursors.DictCursor)

    def __del__(self):
        self.close_conn()

    # Disconnect
    def close_conn(self):
        self.conn.close()

    # Check if (user_id, user_pw) pair is valid
    def match_id_pw(self, user_id, user_pw):
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM `user_table` WHERE `user_id`=%s \
                   AND `user_pw`=md5(%s)"
            cursor.execute(sql, (user_id, user_pw))
            result = cursor.fetchone()
            if result: return True
            else: return False

    # Check the existence of inputted_id
    def is_existing_id(self, inputted_id):
        with self.conn.cursor() as cursor:
            sql = "SELECT * FROM user_table WHERE user_id = %s"
            cursor.execute(sql, (inputted_id, ))
            result = cursor.fetchone()
            if result: return True
            else: return False

    # Get account number corresponding to user_id
    def get_account_num(self, user_id):
        with self.conn.cursor() as cursor:
            sql = "SELECT `account_num` FROM `user_table` \
                   WHERE `user_id`='%s'"
            cursor.execute(sql % (user_id, ))
            result = cursor.fetchone()
            if not result: return False
            return result['account_num']

    # Get user_id corresponding to account number
    def get_user_id(self, account_num):
        with self.conn.cursor() as cursor:
            sql = "SELECT `user_id` FROM `user_table` \
                   WHERE `account_num`=%s"
            cursor.execute(sql, (account_num, ))
            result = cursor.fetchone()
            if not result: return False
            return result['user_id']

    # Check if the github_id is registered before
    def get_reg_flag(self, github_id):
        with self.conn.cursor() as cursor:
            sql = "SELECT `reg_flag` FROM `auth_table` " \
                  "WHERE `github_id` = %s"
            cursor.execute(sql, (github_id, ))
            result = cursor.fetchone()
            return result['reg_flag']

    # Store the user information
    def store_user(self, user_id, user_pw, github_id,
                   email, mobile, balance):
        with self.conn.cursor() as cursor:
            sql = "INSERT INTO user_table(user_id, user_pw, \
                   github_id, email, mobile, balance) \
                   VALUES(%s, md5(%s), %s, %s, %s, %s)"
            try:
                cursor.execute(sql, (user_id, user_pw, github_id,
                                     email, mobile, balance))
                sql = "UPDATE `auth_table` SET `reg_flag` = 1 " \
                       "WHERE `github_id` = %s"
                cursor.execute(sql, (github_id, ))
                self.conn.commit()
                return True
            except:
                self.conn.rollback()
                return False

    # Get the user information corresponding to user_id
    def get_every_user_info(self, user_id):
        with self.conn.cursor() as cursor:
            sql = "SELECT user_pw, account_num, github_id, email, mobile \
                   FROM user_table WHERE user_id = %s"
            cursor.execute(sql, (user_id, ))
            result = cursor.fetchone()
            if not result:
                return False
            else:
                return result

    # Modify the user information
    def store_user_info_modification(self, user_id, info):
        with self.conn.cursor() as cursor:
            user_pw = info['user_pw']
            email = info['email']
            mobile = info['mobile']

            sql = "UPDATE user_table \
                   SET user_pw = md5(%s), email = %s, mobile = %s \
                   WHERE user_id = %s"
            try:
                cursor.execute(sql, (user_pw,
                                     email, mobile, user_id))
                self.conn.commit()
                return True
            except:
                self.conn.rollback()
                return False

    # Update the flag
    def set_flag(self, flag):
        with self.conn.cursor() as cursor:
            sql = "UPDATE `user_table` SET `email` = %s" \
                  "WHERE `user_id` = 'admin'"
            try:
                cursor.execute(sql, (flag, ))
                self.conn.commit()
                return True
            except:
                self.conn.rollback()
                return False

    # Remove the user account (Delete from user_table)
    def remove_user_account(self, user_id):
        with self.conn.cursor() as cursor:
            sql = "SELECT account_num, github_id FROM user_table \
                   WHERE user_id = %s"
            cursor.execute(sql, (user_id, ))
            info = cursor.fetchone()
            if not info:
                return False

            account_num = info['account_num']
            github_id = info['github_id']

            sql = "DELETE FROM user_table WHERE user_id = %s"
            try:
                cursor.execute(sql, (user_id, ))
            except:
                self.conn.rollback()
                return False

            sql = "INSERT INTO withdraw_account_table(user_id, account_num, \
                                                      github_id) \
                   VALUES(%s, %s, %s)"
            try:
                cursor.execute(sql, (user_id, account_num, github_id))
                self.conn.commit()
                return True
            except:
                self.conn.rollback()
                return False

    # Get the balance of user_id.
    # Create a separate connection to reflect the real-time update in DB.
    def get_balance(self, user_id):
        conn = pymysql.connect(host = '127.0.0.1', user = 'root',
                               passwd = mysql_pw, db = 'bankDB', port = 4406,
                               cursorclass = pymysql.cursors.DictCursor)
        # Connect
        with conn.cursor() as cursor:
            sql = "SELECT `balance` FROM `user_table` WHERE `user_id`='%s'"
            cursor.execute(sql % (user_id, ))
            result = cursor.fetchone()
            if not result: return False # No such user
            return result['balance']

    # Update the balance
    # Create a separate connection to reflect the real-time update in DB.
    def update_balance(self, account, change):
        '''
        positive change => ADD to banalce
        negative change => SUBTRACT from balance
        '''

        conn = pymysql.connect(host = '127.0.0.1', user = 'root',
                               passwd = mysql_pw, db = 'bankDB', port = 4406,
                               cursorclass = pymysql.cursors.DictCursor)
        with conn.cursor() as cursor:
            sql = "UPDATE `user_table` SET `balance`=`balance` + %s " \
                  "WHERE `user_id`=%s"
            try:
                cursor.execute(sql, (change, account))
                conn.commit()
                result = True
            except:
                conn.rollback()
                result = False

        conn.close()
        return result

    # Store the transaction
    # Create a separate connection to reflect the real-time update in DB.
    def store_transaction(self, user_id, user_acc, receiver_id, receiver_acc,
                         amount, msg):

        conn = pymysql.connect('127.0.0.1', 'root', mysql_pw, 'bankDB',
                                port = 4406, 
                                cursorclass=pymysql.cursors.DictCursor)

        with conn.cursor() as cursor:
            try:
                sql = "INSERT INTO `tran_table` " \
                      "(`from_account`, `to_account`, `remit`, `msg`, " \
                      " `from_balance`, `to_balance`) " \
                      "VALUES(%s, %s, %s, concat ('[Transfer] ', '%s'), %s, %s)"
                if not self.update_balance(user_id, -amount):
                    raise

                if not self.update_balance(receiver_id, amount):
                    raise

                # AFTER update_balance
                from_bal = self.get_balance(user_id)
                to_bal = self.get_balance(receiver_id)

                cursor.execute(sql % (user_acc, receiver_acc, amount, msg, from_bal, to_bal))

                conn.commit()
                result = True
            except:
                conn.rollback()
                result = False

        conn.close()
        return result

    # Get the transaction log corresponding to user account
    # Create a separate connection to reflect the real-time update in DB.
    def get_all_transaction(self, user_account):
        conn = pymysql.connect(host = '127.0.0.1', user = 'root',
                               passwd = mysql_pw, db = 'bankDB', port = 4406,
                               cursorclass = pymysql.cursors.DictCursor)
        with conn.cursor() as cursor:
            sql = "SELECT tr_time, from_account, to_account, \
                   remit, msg, from_balance, to_balance FROM tran_table \
                   WHERE from_account = %s OR to_account = %s \
                   ORDER BY tr_time"
            cursor.execute(sql, (user_account, user_account))
            result = cursor.fetchall()

        conn.close()
        return result
