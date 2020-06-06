from bs4 import BeautifulSoup
import requests
import urllib3
urllib3.disable_warnings()


class SDO:
  '''
  '''
  def __init__(self, username, password, moodle_id=None):
    self.headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Origin': 'https://sdo.pimunn.net',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.136 YaBrowser/20.2.4.143 Yowser/2.5 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'x-compress': 'null',
        'Referer': 'https://sdo.pimunn.net',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ru,en;q=0.9'}
    
    if moodle_id:
      try:
        self.log_cookie = {'MoodleSession': moodle_id}
        r = requests.get('https://sdo.pimunn.net/login/index.php', 
                         headers=self.headers, cookies=self.log_cookie, verify=False)
        b = BeautifulSoup(r.text, 'html.parser')
        logininfo = b.find('div', attrs={'class': 'logininfo'}).find('a').text
        print('Вы зашли под именем: ' + logininfo)
      except:
        self.log_cookie = self.login_sdo(username, password)
    else:
      self.log_cookie = self.login_sdo(username, password)


  def login_sdo(self, username, password):
    '''
    this method sign in sdo.pimunn.net and 
    returns cookie (r2_cookies) that 
    identify you there
    '''
    # firstly we get main sdo page to get temp cookies and logintoken (params for sign in)
    r1 = requests.get('https://sdo.pimunn.net/login/index.php', headers=self.headers, verify=False)
    r1_cookies = {'MoodleSession': r1.cookies['MoodleSession']}
    logintoken = BeautifulSoup(r1.text, 'html.parser').find(attrs={'name': 'logintoken'})['value']
    r1_data = {'logintoken': logintoken,
               'username': username,
               'password': password}
    # then we log in with that params and get main log cookies
    r2 = requests.post('https://sdo.pimunn.net/login/index.php', 
                       headers=self.headers, cookies=r1_cookies, 
                       data=r1_data, allow_redirects=False, verify=False)
    r2_cookies = {'MoodleSession': r2.cookies['MoodleSession']}
    # i don't know why, but we should go on this location with main log cookies ("registration")
    requests.get(r2.headers['location'], headers=self.headers, 
                 cookies=r2_cookies, allow_redirects=False, verify=False)
    return r2_cookies


  def start_attempt(self, test_id):
    '''
    test_id can be find on sdo by user

    this method starts attempt and
    returns params that identify it
    '''
    test_id = str(test_id)
    # here we only get main page of test looking for sesskey of attempt
    r1 = requests.get('https://sdo.pimunn.net/mod/quiz/view.php?id=' + test_id, 
                        headers=self.headers, cookies=self.log_cookie, verify=False)
    sesskey = BeautifulSoup(r1.text, 'html.parser').find(attrs={'name': 'sesskey'})['value']
    attempt_params = (('cmid', test_id),
                      ('sesskey', sesskey),
                      ('_qf__mod_quiz_preflight_check_form', '1'))
    # here we start an attempt by sesskey and get an attempt_id
    r2 = requests.post('https://sdo.pimunn.net/mod/quiz/startattempt.php', 
                         headers=self.headers, params=attempt_params, 
                         cookies=self.log_cookie, verify=False)
    attempt_id = BeautifulSoup(r2.text, 'html.parser').find(attrs={'name': 'attempt'})['value']
    return sesskey, attempt_id


  def get_page(self, page, test_id, attempt_id):
    '''
    num of pages can be diffirent
    in various test

    we can find num of pages of
    current test in this 
    r.text (html)

    this method gets a page with 
    question and variants of 
    answers (not maked) and 
    returns response with html
    '''
    page = str(page)
    if page == '0':
      params = (('attempt', attempt_id),
                ('cmid', test_id))
    else:
      params = (('attempt', attempt_id),
                  ('cmid', test_id),
                  ('page', str(page)))
    r = requests.get('https://sdo.pimunn.net/mod/quiz/attempt.php', 
                      headers=self.headers, cookies=self.log_cookie, 
                      params=params, verify=False)
    return r


  def save_img(self, img_url, img_path):
    '''
    '''
    response = requests.get(img_url, headers=self.headers, 
                            cookies=self.log_cookie, verify=False)
    with open(img_path, 'wb') as out_file:
      out_file.write(response.content)


  def end_attempt(self, test_id, sesskey, attempt_id):
    '''
    this method gets a page with 
    question and correct answers 
    and returns response with html

    also this method ends an attempt
    '''
    end_params = (
        ('cmid', test_id),
         ('sesskey', sesskey),
         ('finishattempt', '1'),
         ('attempt', attempt_id)
       )
    r = requests.post('https://sdo.pimunn.net/mod/quiz/processattempt.php', 
                        headers=self.headers, params=end_params, 
                        cookies=self.log_cookie, verify=False)
    return r
