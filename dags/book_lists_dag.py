from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
import requests
from requests.auth import HTTPBasicAuth
import os 
import smtplib,ssl

from random import randint
from datetime import datetime

# set the api key to the os environment, could comment out or delete later for security
os.environ['new_york_times_api_key'] = 'ebUcZtSrmuDa3WrKdFmZw2bvhHYCow9I'
os.environ['sender_gmail'] = "futony264@gmail.com"
os.environ["sender_password"] = "pyuhjlfuebewwrjr"


class Mail:

    def __init__(self):
        self.port = 465
        self.smtp_server_domain_name = "smtp.gmail.com"
        self.sender_mail = os.getenv('sender_gmail')
        self.password = os.getenv('sender_password')

    def send(self, emails, subject, content):
        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)
        
        for email in emails:
            result = service.sendmail(self.sender_mail, email, f"Subject: {subject}\n{content}")

        service.quit()


class Crawer:


    def __init__(self,target_lists = ['Combined Print and E-Book Nonfiction']) -> None:
        self.apikey = os.getenv('new_york_times_api_key')
        self.get_book_url = "https://api.nytimes.com/svc/books/v3/lists.json"
        self.target_lists = target_lists
        self.log_path = 'book_list_history.txt'
        file = open(self.log_path,'a+')

    def fetch_list(self,list_name):
        """
        Pass in the list name and return the dict format 
        Ref: 1. https://blog.networktocode.com/post/using-python-requests-with-rest-apis/
            2. https://developer.nytimes.com/docs/books-product/1/routes/lists.json/get
        
        """
       
        query = {'list':list_name,'api-key':self.apikey}
        
        try:
            response = requests.get(self.get_book_url, params=query)
            response.raise_for_status()
            list_result = response.json()['results']
            #self.add_record(list_result)
        
        # Exception Handling
        except requests.exceptions.HTTPError as errh:
            print(errh)
        except requests.exceptions.ConnectionError as errc:
            print(errc)
        except requests.exceptions.Timeout as errt:
            print(errt)
        except requests.exceptions.RequestException as err:
            print(err)
            
        
        return list_result 
    
    def create_book_detail(self,book_info):
        """
        Helper function: Pass in the dic format of book into and generate the string 
        """
        rank = book_info['rank'] 
        title = book_info['book_details'][0]['title']
        contributor = book_info['book_details'][0]['contributor']
        return f"{rank}:{title},{contributor} \n"
    
    def create_all_book_info(self,res_dict):
        """
        Helper function: Pass in the response from the response and generate all the book information 
        """
        # get basic info for the list 
        list_name = res_dict[0]['list_name']
        best_seller_date = res_dict[0]['bestsellers_date']
        published_date = res_dict[0]['published_date']

        res = f"For list name: {list_name}, best_seller_date:{best_seller_date}, publish date:{published_date}, the rank goes as follows: \n"
        for book in res_dict:
            res += self.create_book_detail(book) 
        return res 

    def get_list_info(self):
        """
        Main function to fetch the data and generate string for all lists.
        If the list has already been pulled for this week, then return False,
        else return True 
        """
        # check if pulled before 
        if self.is_pulled_before():
            return ""

        res_str = ""
        for list_name in self.target_lists:
            cur_list_res = self.fetch_list(list_name)
            # add the record to the log to avoid duplication 
            self.add_record(cur_list_res)
            res_str += self.create_all_book_info(cur_list_res)
            res_str += "\n"
        # return "\n".join(self.create_all_book_info(self.fetch_list(list_name)) for list_name in self.target_lists)
        return res_str
    

    def add_record(self,res_dict):
        with open(self.log_path, 'a') as f:
            list_name = res_dict[0]['list_name']
            best_seller_date = res_dict[0]['bestsellers_date']
            published_date = res_dict[0]['published_date']
            #now = datetime.datetime.now()
            base = "New Entry:"
            f.write(f'{base},{list_name},{best_seller_date},{published_date}\n')

    def get_all_pulled_date(self):
        """
        Read the log and return all the pulled startdate
        """
        records = set() # set of all the startdate 
        with open(self.log_path) as f:
            lines = f.readlines()
        for line in lines:
            infos = line.split(",")
            #print(f"infos:{infos}")
            records.add(infos[2])
        print("records:"+str(records))
        return records 
    
    def is_pulled_before(self):
        """
        Check if the lists date has been pulled before 
        """
        res_dict = self.fetch_list(self.target_lists[0]) 
        publish_date = res_dict[0]['bestsellers_date']
        #print(publish_date)
        if publish_date in self.get_all_pulled_date():
            return True 
        return False 




def send_email(ti):
    book_list_str = ti.xcom_pull(task_ids=[
        'fetch_data',  
    ])
    mail = Mail()
    mail.send(["tf2502@columbia.edu"], "The New York Times Best Sellers Book list update",book_list_str[0])
    
    return book_list_str


def fetch_data():
    cr = Crawer(['Combined Print and E-Book Nonfiction',"Combined Print and E-Book Fiction"])
    res_str = cr.get_list_info()
    return res_str 

def handle_pull_res(ti):
    book_list_str = ti.xcom_pull(task_ids=[
        'fetch_data',  
    ])
    if book_list_str[0] == "":
        return 'duplicate_pull'
    else:
        return 'send_email'

with DAG("book_list_dag", start_date=datetime(2022, 11, 8),
    schedule_interval="@daily", catchup=False) as dag:

        fetch_data = PythonOperator(
            task_id="fetch_data",
            python_callable= fetch_data
        )

        duplicate_pull = BashOperator(
        task_id="duplicate_pull",
        bash_command="echo 'list data already pulled'"
        )

        handle_pull_res = BranchPythonOperator(
            task_id="handle_pull_res",
            python_callable= handle_pull_res
        )

        send_email = PythonOperator(
            task_id="send_email",
            python_callable= send_email
        )

        
        fetch_data >> handle_pull_res  >> [send_email, duplicate_pull] 