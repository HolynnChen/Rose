import xml.etree.ElementTree as ET
import os

xml_path='test.xml'
filezilla_path=''
class ftp_xml_helper:
    _DefaultUserXml_=""
    _DefaultPageLen_=20
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
    def get_users_page(self,index=0):
        if index*self._DefaultPageLen_+1>len(self._Users):return []
        page_num=self._DefaultPageLen_
        if (index+1)*self._DefaultPageLen_>len(self._Users):page_num=len(self._Users)-index*self._DefaultPageLen_
        return [self._Users.find(f'User[{index*self._DefaultPageLen_+i}]').get('Name') for i in range(page_num)]
    def get_groups_page(self,index=0):
        if index*self._DefaultPageLen_+1>len(self._Groups):return []
        page_num=self._DefaultPageLen_
        if (index+1)*self._DefaultPageLen_>len(self._Groups):page_num=len(self._Groups)-index*self._DefaultPageLen_
        return [self._Users.find(f'User[{index*self._DefaultPageLen_+i}]').get('Name') for i in range(page_num)]
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
        os.system(f'"{self._filezilla_path}" /reload-config')






