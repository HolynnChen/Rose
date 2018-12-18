import xml.etree.ElementTree as ET
import os

xml_path='test.xml'
filezilla_path=''
class ftp_xml_helper:
    _DefaultUserXml_=""
    def __init__(self,xml_path,filezilla_path,DefaultUserXml):
        self._xml_path=xml_path
        self._filezilla_path=filezilla_path
        self._xml=ET.parse(xml_path)
        self._Users=self._xml.find('Users')
        self._Groups=self._xml.find('Groups')
    def get_users(self):
        return list(map(lambda x:x.get('Name'),self._Users.findall('User')))
    def get_groups(self):
        return list(map(lambda x:x.get('Name'),self._Groups.findall('Group')))
    def edit_user(self,name,option):
        user=self._Users.find(f'User[@Name="{name}"]')
        if not user:self.add_user(name)
        return
    def add_user(self,name,password=''):
        new_User=ET.fromstring(self._DefaultUserXml_)
        new_User.set('Name',name)
        if password:new_User.find('Option[@Name="Pass"]').text=password
    def apply(self):
        self._xml.write(self._xml_path)
        os.system(f'{self._filezilla_path} /reload-config')






