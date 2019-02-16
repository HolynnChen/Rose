import gb
import subprocess
class command:
    def test(self):
        print('yooo')
        return {'command':'response','for_what':'test','data':'success'}
    def run_command(self,cmd):
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        m=res.stdout.read().decode('gbk')
        return m
gb.add(command())