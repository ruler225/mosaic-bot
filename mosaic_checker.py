import requests
from bs4 import BeautifulSoup
import smtplib
from http.client import RemoteDisconnected
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass
from sys import argv
import traceback
#from discord_webhook import DiscordWebhook

session_requests = requests.session()

max_allowed_attempts = 10

url = "https://csprd.mcmaster.ca/psc/prcsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.GBL"
#webhookUrl = "https://discordapp.com/api/webhooks/701474506891591790/vfnUdqZoVXCcFBHR-OBIXlOu7arrx1UrFaETfHg-vahOlXvUimJNBc_810bEblB2rwN3"


#If you would like to skip certain prompts, just fill these out
#Leaving passwords in plaintext is not secure, and is not advised
macID = ""
passwd = ""
email = ""
emailPass = ""
receivingEmail = ""


payload = {
}

returnToTerms = True    # Set this to true if Mosaic goes straight into the wrong semester's grades

# This is used if returnToForms is True
returnFormData = {
    "ICAction": "DERIVED_SSS_SCT_SSS_TERM_LINK",
}

formData = {
    "ICAction": "DERIVED_SSS_SCT_SSR_PB_GO",
    "SSR_DUMMY_RECV1$sels$1$$0": "1" #This is the index of the selection on the term selection page
}


def send_email(email,password,receivingEmail,subject, msg, htmlText=""):
    part1 = MIMEText(msg, "plain")
    part2 = MIMEText(htmlText, "html")

    if htmlText == "":
        part2 = MIMEText(msg, "plain")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = "Mosaic Grades Checker"
    message["To"] = receivingEmail

    message.attach(part1)
    message.attach(part2)

    #print("Establishing eonnection with smtp.gmail.com")
    email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    #print("Logging in...")
    email_server.login(email, password) #I generated an app specific password for the login. I don't advice leaving your password here in plain text though
    #print("Sending email...")
    email_server.sendmail(email, receivingEmail, message.as_string())
    #print("sent email!")

if "--silent" not in argv:
    print("\nWelcome to the Mosaic Grades Page Checker!\n")

skipMacID = macID != ""
skipPassword = passwd != ""
skipEmail = email != ""
skipEmailPass = emailPass != ""
skipReceivingEmail = receivingEmail != ""
continueToPage = False

if not (skipMacID and skipPassword and skipEmail and skipEmailPass and skipReceivingEmail):
    print("Before we begin, I'm going to need some information.\n")

while True:
    if not skipMacID:
        macID = input("What is your MacID? (what you sign into Mosaic with):\n")
    if not skipPassword:
        passwd = getpass("\nWhat is the MacID password for "+macID+"? For security reasons, it will not appear on the screen as you type it:\n")

    if "--silent" not in argv:
        print("I will now attempt to log in with your MacID.\n")

    payload = {
        "userid" : macID,
        "pwd" : passwd
    }

    result = session_requests.get(url)

    result = session_requests.post(
        url,
        data = payload,
        headers = dict(referer=url)
    )

    #tree = html.fromstring(result.content)
    htmlParser = BeautifulSoup(result.content, features="html.parser")
    error = htmlParser.body.find('span', attrs={'id' : 'login_error'})
    #errors = tree.xpath("//span[@id='login_error']/text()")
    #if errors != []:
    if error != None:
        #print("Failed to log in with the following error:\n" + errors[0] + "\n")
        print("Failed to log in with the following error:\n" + error.text + "\n")
        if skipMacID and skipPassword:
            print("The information entered in the python file is incorrect. Please correct it and try again.")
            quit(1)
        print("Please try logging in again.\n")
    else:
        break

if "--silent" not in argv:
    print("Successfully logged into Mosaic!\n")


if not ((skipEmail and skipEmailPass) or "--display-grades" in argv):
    print("Now I need some information about the email you will be using to alert you of grade changes. (Note that it must be a gmail account)\n")
    sleep(1)
    print("Before I get this information, you will need to do one of the following:")
    print("Go to https://accounts.google.com and go to your Security settings (on the left sidebar)\n")
    print("If you have two-factor authentication enabled, go to 'App Passwords' and generate a new app password. This is the password you will enter here.")
    print("If you do not have two-factor authentication enabled, scroll down until you see 'Less secure app access', and turn on access.\n")

while "--display-grades" not in argv:
    while not skipEmail:
        email = input("Please enter your email address:\n")
        if "@" not in email:
            print("This is not a valid email address!\n")
        else:
            break            
    if not skipEmailPass:
        emailPass = getpass("Please enter your email password (or app-specific password):\n")
    if "--silent" not in argv:
        print("Logging in to your gmail account...")

    email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    try:
        email_server.login(email, emailPass)
        break
    except smtplib.SMTPAuthenticationError as e:
        print("Login failed!")
        print(str(e))
        print("Please make sure you are either using an app-specific password (if you have 2-factor authentication enabled) or you have less secure app access enabled in your gmail account settings.")
        if skipEmail and skipEmailPass:
            quit(0)

if not ("--silent" in argv or "--display-grades" in argv):
    print("Successfully logged into your gmail account!\n")

if not (skipReceivingEmail or "--display-grades" in argv):
    receivingEmail = input("Enter the email address that you would like to send emails to. If you would like to just send them to yourself, you can leave this blank\n")

if receivingEmail == "":
    receivingEmail = email

if "--silent" not in argv:
    print("Getting grades...")

#tree = html.fromstring(result.content)

htmlParser = None
course_names = None

if returnToTerms:
    result = session_requests.post(
        url,
        data = returnFormData,
        headers = dict(referer=url)
    )
else:
    htmlParser = BeautifulSoup(result.content, features="html.parser")
    course_names = htmlParser.find_all('a', attrs={'class' : 'PSHYPERLINK'})[7:-2]
    course_names = [course.text for course in course_names]
    oldMarks = htmlParser.find_all('span', attrs=({'class' : 'PABOLDTEXT'}))[1:]
    oldMarks = [mark.text for mark in oldMarks]
#DEBUG####################################################################################
#course_names = []
#Parse all elements representing course names
#for elem in elems:
#    if 'id' in elem.attrs:
#        if elem['id'].startswith("CLS_LINK"):
#            course_names.append(elem.text)
#for course in course_names:
#    print(course)
#course_names = tree.xpath("//a[@class='PSHYPERLINK']/text()")[:-1]
#oldMarks = tree.xpath("//span[@class='PABOLDTEXT']/text()")[1:]
###########################################################################################

if course_names == [] or returnToTerms:
    continueToPage = True
    result = session_requests.post(
        url,
        data = formData,
        headers = dict(referer=url)
    )
    #tree = html.fromstring(result.content)
    htmlParser = BeautifulSoup(result.content, features="html.parser")
    course_names = htmlParser.find_all('a', attrs={'class' : 'PSHYPERLINK'})[7:-2]
    course_names = [course.text for course in course_names]
    oldMarks = htmlParser.find_all('span', attrs=({'class' : 'PABOLDTEXT'}))[1:]
    oldMarks = [mark.text for mark in oldMarks]
    #course_names = tree.xpath("//a[@class='PSHYPERLINK']/text()")[:-1]
    #oldMarks = tree.xpath("//span[@class='PABOLDTEXT']/text()")[1:]

print("I found these grades:\n")
for index, name in enumerate(course_names):
    grade = oldMarks[index]
    grade = "Nothing yet" if grade == '\xa0' else grade
    print(name + ": " + grade)

if "--display-grades" in argv:
    quit(0)


print("\nI will now check for any changes to these grades every 30 seconds and email you if anything changes.\n")
sleep(1)
print("You can stop this script at any time by pressing control-c\n")

failCount = 0

#this loop checks for changes to the above webpages from when they were fetched at the beginning of the script
while True:
    try:
        if failCount >= max_allowed_attempts:
            raise ConnectionError("Too many failures to connect!")
        
        
        result = session_requests.get(url, headers = dict(referer = url))
        
        if returnToTerms:
            result = session_requests.post(url, data = returnFormData, headers = dict(referer=url))

        if continueToPage:
            result = session_requests.post(url, data = formData, headers = dict(referer = url))
        
        htmlParser = BeautifulSoup(result.content, features="html.parser")
        marks = htmlParser.find_all('span', attrs=({'class' : 'PABOLDTEXT'}))[1:]
        marks = [mark.text for mark in marks]

        if marks == []:
            failCount += 1
            marks = oldMarks[:]
            if failCount >= max_allowed_attempts:
                send_email(email, emailPass, receivingEmail, "Script failed", "Couldn't find grades in the following webpage", result.text)
                quit(-1)
        elif len(marks) != len(oldMarks):
            send_email(email, emailPass, receivingEmail, "Script failed", "The grades have changed. Only the following grades are available now: " + str(marks))
            quit(-1)
        else:
            failCount = 0

        if marks != oldMarks:
            differentMarks = [index for index, i in enumerate(oldMarks) if i != marks[index]]
            #print("Grades change found! Sending email...")
            #print("For course ", course_names[differentMarks[0]])
            msgString = ""
            for index, mark in enumerate(differentMarks):
                msgString += "Your mark for " + course_names[differentMarks[index]] + " is out. Your mark is: " + marks[differentMarks[index]] + "\n\n"
                #    webhook = DiscordWebhook(url=webhookUrl, content=course_names[differentMarks[index]] + " marks have been released on Mosaic.\n\n*I can’t look, hold me Belle!*")
                #    webhook.execute()
            send_email(email, emailPass, receivingEmail,"Final marks released", msgString)
            oldMarks = marks

        
        
        #print("no grades change found")

        #wait for 30 seconds before checking again
        sleep(30)
    except KeyboardInterrupt:
        quit(0)
    except requests.exceptions.ConnectionError:
        failCount += 1
        sleep(30)
    except requests.exceptions.Timeout:
        failCount += 1
        sleep(30)
    except ConnectionResetError:
        failCount += 1
        sleep(30)
    except RemoteDisconnected:
        failCount += 1
        sleep(30)
    except Exception as e:
        error = traceback.format_exc()
        send_email(email, emailPass, receivingEmail,"Script failed", "An error occured in the script. Details are: " + error)
        #print("Error: ", str(e))
        quit(0)




