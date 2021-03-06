import requests
import re  # regex module
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from func_timeout import func_timeout, FunctionTimedOut


class EmailScraper:

    def __init__(self, query):
        self.query = query

    def search(self):
        temp_query = self.query + " email"
        temp_query = "+".join(temp_query.split())
        starttime = time.time()

        start = 0
        num = 30
        all_email = []
        email_number = 0
        session = requests_retry_session()
        while True:
            params = "&start={}&num={}".format(start, num)
            url = "https://www.google.com/search?q={0}".format(temp_query) + params

            try:
                # sending an http get request with specific url and get a response

                response = session.get(url)
                if response is None:
                    return
            except requests.exceptions.ConnectionError:
                print("Connection Error " + url)
                return "Connection Error"
            except requests.exceptions.Timeout:
                print("Request timed out" + url)
                return "Request timed out"
            except requests.exceptions.TooManyRedirects:
                print("Too many redirects " + url)
                return
            except requests.exceptions.HTTPError:
                print("Bad Request." + url)
                return
            except requests.exceptions.InvalidURL:
                print("Invalid URL. " + url)
                return
            except requests.exceptions.InvalidSchema:
                print("Invalid Schema." + url)
                return
            except requests.exceptions.MissingSchema:
                print("Missing Schema URL. " + url)
                return
            except requests.exceptions.RetryError:
                print("Retry Error " + url)
                return

            soup = BeautifulSoup(response.text, 'lxml')


            for tag in soup.find_all('a'):
                if '/url?q=' in tag['href']:
                    url = tag['href'].split('/url?q=')[1]
                    emails = []
                    try:
                        emails = func_timeout(15, self.get_emails, args=(url, session))
                    except FunctionTimedOut:
                        print("doit('arg1', 'arg2') could not complete within 5 seconds and was terminated.\n")
                    except Exception as e:
                    # Handle any exceptions that doit might raise here
                        print('err')
                    # emails = self.get_emails(url, session)
                    if emails is None or len(emails) == 0:
                        continue
                    all_email.extend((emails, url))
                    email_number = email_number + len(emails)
                    print(email_number, emails)
                    if email_number > 100:
                        break

            endtime = time.time()
            if email_number > 100:
                break
            start = start + num
            delta_time = endtime - starttime
            if delta_time > 120:
                break
        return all_email, delta_time

    def get_emails(self, url, session):

        try:
            # sending an http get request with specific url and get a response
            print(url)
            response = session.get(url)

        except requests.exceptions.ConnectionError:
            print("Connection Error " + url)
            return
        except requests.exceptions.HTTPError:
            print("Bad Request. " + url)
            return
        except requests.exceptions.Timeout:
            print("Request timed out" + url)
            return
        except requests.exceptions.TooManyRedirects:
            print("Too many redirects " + url)
            return
        except requests.exceptions.InvalidURL:
            print("Invalid URL. " + url)
            return
        except requests.exceptions.InvalidSchema:
            print("Invalid Schema." + url)
            response = session.get("http://" + url)
        except requests.exceptions.MissingSchema:
            print("Missing Schema URL. " + url)
            response = session.get("http://" + url)
        except requests.exceptions.RetryError:
            print("Retry Error " + url)
            return

        if response is None:
            return
        # email pattern to match with - name@domain.com
        email_pattern = "[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+" # 1st pattern
        # making the regex workable - compile it with ignore case
        email_regex = re.compile(email_pattern, re.IGNORECASE)
        # match all the email in html response with regex pattern and get a set of emails
        # response.text returns html as string
        email_list = email_regex.findall(response.text)

        # email pattern to match with - name @ domain.com
        email_pattern = "[a-zA-Z0-9._-]+\s@\s[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+" # 2nd pattern
        # making the regex workable - compile it with ignore case
        email_regex = re.compile(email_pattern, re.IGNORECASE)
        # match all the email in html response with regex pattern and get a set of emails
        # response.text returns html as string
        email_list.extend(email_regex.findall(response.text))

        # email pattern to match with - name at domain.com
        email_pattern = "[a-zA-Z0-9._-]+\sat\s[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+" # 3rd pattern
        # making the regex workable - compile it with ignore case
        email_regex = re.compile(email_pattern, re.IGNORECASE)
        # match all the email in html response with regex pattern and get a set of emails
        # response.text returns html as string
        email_list.extend(email_regex.findall(response.text))

        return set(self.strip(email_list))

    def strip(self, all_email):
        first = [item.replace(" at ", "@") for item in all_email]
        second = [item.replace(" AT ", "@") for item in first]
        third = [item.replace(" @ ", "@") for item in second]

        return third


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    session.max_redirects = 60
    # session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
    #                                 '(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


if __name__ == "__main__":

    keywords = input("Search Email: ")
    emailScraper = EmailScraper(keywords)

    email_list = emailScraper.search()

    print(str(len(email_list)) + " emails")

    for email in email_list:
        print(email)
