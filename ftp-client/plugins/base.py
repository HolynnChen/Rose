import gb
import subprocess
import connect_mysql
class command:
    def test(self):
        print('yooo')
        return {'command':'response','for_what':'test','data':'success'}
    def run_command(self,cmd):
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        m=res.stdout.read().decode('gbk')
        return m
    def set_admin(self,name,password):
        with open(f'/etc/vsftpd/vsftpd_user_conf/{name}','w+') as file:
            file.write(f'write_enable=YES\ndownload_enable=YES\nlocal_root=/home/ftpuser/{name}\n')
            self.run_command('systemctl restart vsftpd')
            self.run_command(f'mkdir -p /home/ftpuser/{name}')
            self.run_command(f'chmod 777 /home/ftpuser/{name}')
            connect_mysql.add_user(name,password)
        return {'command':'response','for_what':'set_admin','data':'success'}
    def set_user(self,name,password):
        with open(f'/etc/vsftpd/vsftpd_user_conf/{name}','w+') as file:
            file.write(f'write_enable=NO\ndownload_enable=YES\nlocal_root=/home/ftpuser/{name}\n')
            self.run_command('systemctl restart vsftpd')
            self.run_command(f'mkdir -p /home/ftpuser/{name}')
            self.run_command(f'chmod 777 /home/ftpuser/{name}')
            connect_mysql.add_user(name,password)
        return {'command':'response','for_what':'set_user','data':'success'}
    def show_all_user(self):
        return {'command':'response','for_what':'show_all_user','data':connect_mysql.show_all_user()}
    def show_all_project(self):
        return {'command':'response','for_what':'show_all_project','data':self.run_command('xfs_quota -x -c report /home/ftpuser')}
    def add_project(self,name,id):
        message=self.run_command(f"xfs_quota -x -c 'project -s -p /home/ftpuser/{name} {id}'")
        return {'command':'response','for_what':'add_project','data':message}
    def change_limit(self,size,id):
        message=self.run_command(f"xfs_quota -x -c 'limit -p bhard={size}m {id}' /home/ftpuser")
        return {'command':'response','for_what':'change_limit','data':message}
gb.add(command())