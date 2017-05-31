import pymysql
import rand_pw
import reg_pubkey

if __name__ == "__main__":
    admin_pw = rand_pw.gen_rand_pw(19)
    reg_pubkey.register_info("admin")
    password = open("root.pw","rt").read()

    conn = pymysql.connect(host = '127.0.0.1', user = 'root',
                           passwd = password, db = 'bankDB', port = 4406,
                           cursorclass = pymysql.cursors.DictCursor)
    with conn.cursor() as cursor:
        sql = "INSERT INTO user_table(user_id, user_pw, \
               github_id, email, mobile, balance) \
               VALUES(%s, md5(%s), %s, %s, %s, %s)"
        cursor.execute(sql, ("admin", admin_pw, "admin", "admin@bank.com", 
                            "01012341234", 1000))
    conn.commit()
    conn.close()
