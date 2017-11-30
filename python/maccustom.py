#!/usr/local/bin/python3
# Written By Peter Yang
# Copyright 2017 

import subprocess
import os
import sys
import time

import requests
import base64
import xml.dom.minidom

from subprocess import Popen

#below define the global variables for the program
total_software_count=100#total number of software
base_directory=""#put the absolute root path of your code
UsernameVar=""#put the user name of your JAMF JSS user
PasswordVar=""#put the password of your JAMF JSS user
JamfUrl=""#put your jamf url

def main():
    
    #generate the software options list for startup.html
    generate_list_startup()
    
    #show customize screen
    cmd_str = '../Trigger/Trigger.app/Contents/MacOS/Trigger -f '+base_directory+'/startup.html wait --fullscreen'
    cmd = cmd_str.split()    
    output = subprocess.check_output(cmd);
    output_1 = str(output,'utf-8')
    
    #split each line of output to an array
    output_2 = output_1.split('\n')
    
    is_attr_valid=False
    
    while is_attr_valid==False:
        #iterate through each line
        for output_item in output_2:
            #split the attribute name and value
            output_item_1 = output_item.split('=')
            if(len(output_item_1)==2):
                #print(output_item_1)
                if(output_item_1[0]=='computer_name'):
                    computer_name = output_item_1[1]
                    #print('compute name:'+output_item_1[1])
                elif(output_item_1[0]=='computer_code'):
                    computer_code = output_item_1[1]
                    #print('computer code:'+output_item_1[1])
                elif(output_item_1[0]=='software_option'):
                     #print('software option:'+output_item_1[1])
                     software_option=output_item_1[1]
                     software_option=software_option.replace("%20", " ")
        if computer_name!='' and computer_code!='' and software_option!='':
            is_attr_valid=True
        else:
            #Show invalid attributes screen
            invalid_cmd_str = '../Trigger/Trigger.app/Contents/MacOS/Trigger -f '+base_directory+'/invalidattributes.html wait --fullscreen'
            invalid_cmd = invalid_cmd_str.split()    
            invalid_output = subprocess.check_output(invalid_cmd)
            
            invalid_cmd_str = '../Trigger/Trigger.app/Contents/MacOS/Trigger -f '+base_directory+'/startup.html wait --fullscreen'
            invalid_cmd = invalid_cmd_str.split()    
            invalid_output = subprocess.check_output(invalid_cmd)
            invalid_output_1 = str(invalid_output,'utf-8')
            output_2 = invalid_output_1.split('\n')
            
    #show installation screen
    generate_install_apps("There are "+str(total_software_count)+" software to install")
    time.sleep(2)
    cmd = ['../Trigger/Trigger.app/Contents/MacOS/Trigger', '-f', base_directory+'/setup_mac.html', 'wait','--fullscreen']   
    p = Popen(cmd)
   
   
    #trigger software installation policies
    #get policy id
    policy_id=""
    tmp_policy_list=get_policy_list()
    for tmp_policy in tmp_policy_list:
        tmp_policy_name = str(tmp_policy['name'])
        tmp_policy_name=tmp_policy_name.replace("@", "")
                
        if software_option==tmp_policy_name:
            policy_id=str(tmp_policy['id'])
            break;
    
    if policy_id!="":
        cmd = ['jamf', 'policy', '-id', policy_id]   
        p_policy = Popen(cmd,stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    
    
        #count down number
        i=0
        while True:
            if(i<total_software_count):
                i=i+1
            line = p_policy.stdout.readline()
            
            if not line:
                break
            #print(line)
            time.sleep(5)
            p.terminate()
            generate_install_apps("There are "+str(total_software_count-i)+" software to install ...")
            cmd = ['../Trigger/Trigger.app/Contents/MacOS/Trigger', '-f', base_directory+'/setup_mac.html', 'wait','--fullscreen']   
            p = Popen(cmd)
            #p.terminate()
    p.terminate()
    
    #show complete screen
    cmd = ['../Trigger/Trigger.app/Contents/MacOS/Trigger', '-f', base_directory+'/finish_mac.html', 'wait','--fullscreen']   
    p = Popen(cmd)
    
    

def generate_install_apps(install_log):
    #replace software option list with real values
    print(install_log)
    out_file = open("../setup_mac_tmp.html", "w")
    cmd_replace=['sed', "s/h_install_log/" + install_log+ "/g",base_directory+"/setup_mac_template.html" ]
    subprocess.call(cmd_replace, stdout=out_file);
    
    #copy the temp file to startup.html
    cmd_copy_str="cp -f "+base_directory+"/setup_mac_tmp.html "+base_directory+"/setup_mac.html"
    cmd_copy = cmd_copy_str.split()
    subprocess.check_output(cmd_copy);
    
def generate_list_startup():
    select_list="<option><\/option>"
    policy_list=get_policy_list()
    for policy in policy_list:
        policy_name = str(policy['name'])
        policy_name=policy_name.replace("@", "")
        select_list = select_list + "<option>"+policy_name+"<\/option>"    
    
    #cmd_replace_str="sed \'s/h_select_list/" + select_list+ "/g\' ../startup_template.html>../startup_tmp.html"
    #cmd_replace = cmd_replace_str.split()
    
    #replace software option list with real values
    out_file = open(base_directory+"/startup_tmp.html", "w")
    cmd_replace=['sed', "s/h_select_list/" + select_list+ "/g",base_directory+"/startup_template.html" ]
    subprocess.call(cmd_replace, stdout=out_file);
    
    #copy the temp file to startup.html
    cmd_copy_str="cp -f "+base_directory+"/startup_tmp.html "+base_directory+"/startup.html"
    cmd_copy = cmd_copy_str.split()
    subprocess.check_output(cmd_copy);
    #output = subprocess.check_output(cmd);
    #print(select_list)
    #print(policy_list)


def get_policy_list():
    
    policy_list=[]
    
    r=requests.get(JamfUrl+'/JSSResource/policies',auth=(UsernameVar, PasswordVar),verify=False)
    xmldoc = xml.dom.minidom.parseString(r.text) # or xml.dom.minidom.parseString(xml_string)
    #print(r.text)
    
    policies=xmldoc.getElementsByTagName("policy")
    policy_list=[]
    
    
    for policy in policies:
        policy_name=policy.getElementsByTagName('name')[0].firstChild.nodeValue
        #print(policy_name)
        if "@"  in policy_name:
           policy_id=policy.getElementsByTagName('id')[0].firstChild.nodeValue       
           #print(policy_id)
           policy_list.append({'name':policy_name,'id':policy_id})
    return policy_list

         
if __name__ == "__main__": main()