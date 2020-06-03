class SDO(object):
  """docstring for SDO"""
  def __init__(self, username, password):
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
      'Accept-Language': 'ru,en;q=0.9',
    }
    self.log_cookie = self._login_sdo(username, password)


  def _login_sdo(self, username, password):
    '''
    this method sign in sdo.pimunn and returns cookie (r2_cookies) that identify you there
    '''
    r1 = requests.get('https://sdo.pimunn.net/login/index.php', headers=self.headers, verify=False)
    r1_cookies = {'MoodleSession': r1.cookies['MoodleSession']}

    r1_data = {
      'logintoken': BeautifulSoup(r1.text).find(attrs={'name': 'logintoken'})['value'],
      'username': username,
      'password': password
    }

    r2 = requests.post('https://sdo.pimunn.net/login/index.php', 
                       headers=self.headers, cookies=r1_cookies, data=r1_data, 
                       allow_redirects=False, verify=False)
    r2_cookies = {'MoodleSession': r2.cookies['MoodleSession']}
    requests.get(r2.headers['location'], headers=headers, 
                 cookies=r2_cookies, allow_redirects=False, verify=False)
    return r2_cookies
    

    def _start_attempt(self, test_id):

      test_id = str(test_id)
      r1 = requests.get('https://sdo.pimunn.net/mod/quiz/view.php?id=' + test_id, 
                        headers=self.headers, cookies=self.log_cookie, verify=False)
      sesskey = BeautifulSoup(r1.text).find(attrs={'name': 'sesskey'})['value']

      test_params = (
        ('cmid', test_id),
        ('sesskey', self.sesskey),
        ('_qf__mod_quiz_preflight_check_form', '1')
      ) 
      r2 = requests.post('https://sdo.pimunn.net/mod/quiz/startattempt.php', 
                         headers=self.headers, params=test_params, 
                         cookies=self.log_cookie, verify=False)
      attempt_id = BeautifulSoup(r2.text).find(attrs={'name': 'attempt'})['value']
      return sesskey, attempt_id


    def _proccess_qa(self, tag):
      q = tag.find(attrs={'class': 'qtext'})

      img = q.find('img')
      if img: 
        img_url = img.get('src')
      else:
        img_url = None

      try:
        answers = sorted([l.text.split('. ')[1] for l in tag.find_all('label')])
      except:
        answers = ['сорян', 'ответы', 'не удалось', 'получить']

      try:
        ra = tag.find(attrs={'class': 'rightanswer'}).text.split(': ')[1]

        for i, a in enumerate(answers):
          if a in ra:
            answers[i] = '+  ' + answers[i]
          else:
            answers[i] = '   ' + answers[i]
        answers.append(ra)
      except:
        pass
      return (q_t.text, '\n'.join(a for a in answers), img_url)


    def _process_test(test_text):
      b = BeautifulSoup(test_text)
      questions = b.find(attrs={'role': 'main'}).find_all(attrs={'class': 'content'})
      questions = [self.proccess_qa(q) for q in questions]
      return questions


    def get_qa(self, test_id, num_q=50):
      # проверить сколько там вопросов, чтобы не вводить сюда
      sesskey, attempt_id = self._start_attempt(test_id)
      data = []
      for page in range(num_q):
        if page == 0:
          params = (
            ('attempt', attempt_id),
            ('cmid', test_id)
          )
        else:
          params = (
            ('attempt', attempt_id),
            ('cmid', test_id),
            ('page', str(page))
          )
        r = requests.get('https://sdo.pimunn.net/mod/quiz/attempt.php', 
                          headers=self.headers, cookies=self.log_cookie, 
                          params=params, verify=False)
        data.extend(self._process_test(r.text))
      self.end_attempt(test_id, sesskey, attempt_id)
      return data


    def get_qra(self, test_id):
      sesskey, attempt_id = self._start_attempt(test_id)
      r = self.end_attempt(test_id, sesskey, attempt_id)
      return self._process_test(r.text)


    def end_attempt(self, test_id, sesskey, attempt_id):
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
