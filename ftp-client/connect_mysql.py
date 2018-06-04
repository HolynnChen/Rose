import pymysql
import configloader as co
db=None
def init():
    global db
    db=pymysql.connect(co.config['mysql_address'],co.config['mysql_user'],co.config['mysql_password'],co.config['mysql_used_db'])
def add_user(name,password):
    try:
        sql=f'insert into user(name,passwd) values("{name}",password("{password}"))'
        cu=db.cursor()
        cu.execute(sql)
        db.commit()
    except:
        db.rollback()

def show_all_user():
    try:
        sql='select * from user'
        cu=db.cursor()
        cu.execute(sql)
        return cu.fetchall()
    except:
        return 'ERROR'