import requests
from bs4 import BeautifulSoup
import pandas as pd

#GENERATE URLS TO SCRAPE
CSV_PATH = "" #INSERT THE PATH TO YOUR CSV FILE HERE TO SAVE PAST DEALS
BASE_URL = "https://forums.redflagdeals.com/hot-deals-f9/trending/"
SCRAPE_URLS = [BASE_URL + str(page_num) for page_num in range(1,5)]

#GENERATE EMPTY DICTIONARY
deal_dict = {}

#LOOP THROUGH EACH URL IN SCRAPE_URLS
for url in SCRAPE_URLS:
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, "html.parser")

    #SCRAPE EACH URL FOR THE ITEM CONTENTS
    for item in soup.find_all(class_ = "thread_info"):
        try:
            item_title = item.find(class_ = "topic_title_link").get_text().strip()
            item_score = item.find(class_ = "total_count_selector").get_text().strip()

            #FORMATTING AND ERROR HANDLING
            if item_score == "":
                item_score = "0"
            
            if item_score != "0":
                item_score = item_score.replace("+", "")
                item_score = item_score.replace("-", "")

            deal_dict[item_title] = int(item_score)
        except AttributeError:
            item_title = "Error Catch"
            item_score = 0
            deal_dict[item_title] = item_score

#READ IN CSV FILE OF DEALS THAT HAVE ALREADY BEEN SENT
past_deals = pd.read_csv(CSV_PATH)

#DELETE ELEMENTS IN THE DEAL DICTIONARY IF THEY HAVE ALREADY BEEN SENT IN THE PAST
for item in list(deal_dict):
    if item in past_deals["Deal_Name"].values:
        del deal_dict[item]

#CREATE DATAFRAME OF REMAINING DEALS TO BE SENT, WHERE SCORE IS >= 20
df = pd.DataFrame()

df["Deal_Name"] = deal_dict.keys()
df["Deal_Score"] = deal_dict.values()

df.drop(df[df["Deal_Score"] <= 20].index, inplace = True)

df.sort_values("Deal_Score", ascending = False, inplace = True)

message = """Subject: RFD Deals for Today\n\n"""

if df.shape[0] >= 1:
    for i, row in df.iterrows():
        message += f"[{row['Deal_Score']}] - {row['Deal_Name']}\n"

    #GENERATING SMTPLIB DETAILS
    import smtplib, ssl
    message = message.encode('ascii', 'ignore')
    SMTP_SERVER = "smtp.gmail.com" #Using gmail to send the email
    PORT = 587
    SENDER_EMAIL = "" #Insert your 'sending' email here (e.g. the account you're sending the email from)
    SENDER_PASSWORD = "" #Password of 'sending' account
    RECEIVER_EMAIL = ["",] #List of people you'd like to send the deals to

    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP(SMTP_SERVER, PORT)
        server.starttls(context=context)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message)

    except Exception as e:
        print(e)

    finally:
        server.quit()

    df.rename(columns = {"Deal_Score" : "DealScore"}, inplace = True)
    
    past_deals = pd.concat([past_deals, df])

    past_deals.to_csv(CSV_PATH, index = False)

else:
    print("No Email Sent")