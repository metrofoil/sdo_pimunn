from sdo_client import SDO
from bs4 import BeautifulSoup
from urllib.parse import unquote
import os
import time


class TestMaker:
  '''
  '''
  def __init__(self):
    if not os.path.exists('sdo_testmaker'):
      os.mkdir('sdo_testmaker')
    self.path = 'sdo_testmaker/'

    try:
      with open('sdo_testmaker/login.info', 'r') as f:
        logininfo = f.read().splitlines()
      if len(logininfo) > 1:
        moodle_id = logininfo[1].strip()
      else:
        moodle_id = None
      u_p = [word.strip() for word in logininfo[0].split()]
      username, password = u_p[0], u_p[1]
      self.sdo = SDO(username, password, moodle_id)
    except:
      inp = input('Введите через пробел логин и пароль от СДО:')
      inp = [word.strip() for word in inp.split()]
      username, password = inp[0], inp[1]
      self.sdo = SDO(username, password)

    with open('sdo_testmaker/login.info', 'w') as f:
      f.write(username + ' ' + password + '\n' + self.sdo.log_cookie['MoodleSession'])


  def _proccess_qa(self, tag):
    '''
    '''
    q = tag.find(attrs={'class': 'qtext'})
    #
    img = q.find('img')
    if img: 
      img_url = img.get('src')
      img_name = unquote(img_url.split('/')[-1])
      self.sdo.save_img(img_url, self.path + img_name)
    else:
      img_name = 'None'

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
      answers.append('Правильно: ' + ra)
    except:
      pass
    return (q.text, '\n'.join(a for a in answers), img_name)


  def _process_test(self, test_text):
    '''
    '''
    b = BeautifulSoup(test_text, 'html.parser')
    questions = b.find(attrs={'role': 'main'}).find_all(attrs={'class': 'content'})
    questions = [self._proccess_qa(q) for q in questions]
    return questions


  def _get_qa(self, test_id):
    '''
    '''
    data = []
    sesskey, attempt_id = self.sdo.start_attempt(test_id)

    r = self.sdo.get_page(0, test_id, attempt_id)
    data.extend(self._process_test(r.text))
    num_q = BeautifulSoup(r.text, 'html.parser').find_all(attrs={'data-quiz-page': True})
    for page in range(1, len(num_q) - 1):  # "-1" потому что первый выше получен
      r = self.sdo.get_page(page, test_id, attempt_id)
      data.extend(self._process_test(r.text))
    self.sdo.end_attempt(test_id, sesskey, attempt_id)
    return data


  def _get_qra(self, test_id):
    '''
    '''
    sesskey, attempt_id = self.sdo.start_attempt(test_id)
    r = self.sdo.end_attempt(test_id, sesskey, attempt_id)
    return self._process_test(r.text)


  def make_test(self, test_id, maker_type='qra'):
    '''
    '''
    #
    test = []
    count_new = 1
    max_iter = 50
    wait = 0
    while count_new and max_iter:
      try:
        max_iter -= 1
        if maker_type == 'qra':
          maked_test = self._get_qra(test_id)
        else:  # maker_type = qa
          maked_test = self._get_qa(test_id)
        #
        count_new = 0
        for qa in maked_test:
          if qa not in test:
            count_new += 1
            test.append(qa)
        #
        if count_new > 0:
          print(str(test_id) + '| Всего вопросов ' + str(len(test)))
        text = '\n\n'.join(q[0] + '\n' + q[2] + '\n' + q[1] 
                           for q in test).replace('None\n', '') 

        with open(self.path + str(test_id) + '.txt', 'w') as f:
          f.write(text)

      except:
        wait += 60
        print(str(test_id) + '| Похоже, для этого теста нужно ждать ' + str(wait) + ' секунд')

      if count_new > 0:
          time.sleep(wait)
      else:
        print(str(test_id) + '| Больше вопросов нет. Завершаем')


print('SDO TESTMAKER 0.1')
print('------------------------------')
t = TestMaker()
print('------------------------------')
print('Чтобы поменять режим работы, введите:\n "qra" (с правильными ответами)\n "qa" (просто ответы)')
print('------------------------------')
maker_type = 'qra'
while True:
  inp = input(maker_type + '>> ').strip()
  if inp == 'qra' or inp == 'qa':
    maker_type = inp
  else:
    try:
      if '-' in inp:
        inp = inp.split('-')
        nums = range(int(inp[0]), int(inp[1]) + 1)
      elif ',' in inp:
        nums = [num.strip() for num in inp.split(',')]
      else:
        nums = inp.split()
      for num in nums:
        t.make_test(num, maker_type)
    except:
      print('неправильный ввод')
