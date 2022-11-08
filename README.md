# Fetching data from The New York Times Best Sellers  API and send email 

### Basic Information 
- name: Tianshu Fu 
- email: tf2502@columbia.edu

### How to Run
1. Open the terminal and clone the Repository 
```shell
git clone https://github.com/tianshufu/Code-Assessment---Data-Engineering.git
```
2. Go the cloned directory and start the docker container 
```shell
cd Code-Assessment---Data-Engineering
docker-compose up
```
3. Wait for a file and open the browser and enter: `http://localhost:8080/`, username and password both are: `airflow`

<img width="1181" alt="image" src="https://user-images.githubusercontent.com/43307910/200628618-f306636a-8625-48fc-b029-bed3aff76c4e.png">

4. Go to the `book_list_dag` to click to run, the first run will pull the data and send the email 
<img width="1431" alt="image" src="https://user-images.githubusercontent.com/43307910/200629367-37241197-0122-4b29-b6bd-c06696877a54.png">
And we click run agian, it will not pull the data since the data has already been pulled:
<img width="1429" alt="image" src="https://user-images.githubusercontent.com/43307910/200629700-f61a7e6e-979a-47eb-bcba-50af635fdca1.png">

### File Structure
```
  /dags/
    book_lists_dag.py : Airflow DAG file for this assignment
  /dev/
    fetch_data.py : All the function code such as send email and unit test code, could use this file to do unit testing 
  /logs/ : All the Airflow logs
  .env : environment varaiable during containder run time 
  docker-compose.yaml : Docker configuration file 
```

### Details of Implentation:

> The dag should be designed in a way that it will just pull the list of a given week for no more than once. But the dag should still be scheduled as a daily job.

**My Solution:** I created a `log` file `book_list_history.txt` contians the success pulling history, before pulling, the program will read the log file and check if the specific date has been pulled before. If not pulled before, it will pull the data and wrtie to the log and send the email. If pulled before, if will not pull the data and wake `duplicate_pull` task.


### FAQ:
1. How to adjust email list?


**Ans:** Go the the `book_lists_dag.py` and update the email list:
```python
def send_email(ti):
    book_list_str = ti.xcom_pull(task_ids=[
        'fetch_data',  
    ])
    mail = Mail()
    mail.send(["tf2502@columbia.edu"], "The New York Times Best Sellers Book list update",book_list_str[0])
    
    return book_list_str
```

2.How to adjust the pulling book list?

**Ans:** Go the the `book_lists_dag.py`  Add or remove in the list

```python
def fetch_data():
    cr = Crawer(['Combined Print and E-Book Nonfiction',"Combined Print and E-Book Fiction"])
    res_str = cr.get_list_info()
    return res_str 
```




### Reference: 
- Aifrflow Docker: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- Python send email: https://realpython.com/python-send-email/
- Project Desceription: https://docs.google.com/document/d/1pudzsIRvicQ72PRzJ7O_8isVRH2oxdQRXXjQrAdDKGc/edit



