from tkinter import *
from tkinter import scrolledtext
import time
from threading import Thread
import requests
from bs4 import BeautifulSoup


headers = {
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


def login_sdo(username, password):
  global headers
  r1 = requests.get('https://sdo.pimunn.net/login/index.php', headers=headers, verify=False)
  r1_cookies = {
      'MoodleSession': r1.cookies['MoodleSession'],
  }

  r1_data = {
    'logintoken': BeautifulSoup(r1.text).find(attrs={'name': 'logintoken'})['value'],
    'username': username,
    'password': password
  }
  r2 = requests.post('https://sdo.pimunn.net/login/index.php', headers=headers, cookies=r1_cookies, data=r1_data, allow_redirects=False, verify=False)
  r2_cookies = {
      'MoodleSession': r2.cookies['MoodleSession'],
  }
  requests.get(r2.headers['location'], headers=headers, cookies=r2_cookies, allow_redirects=False, verify=False)
  return r2_cookies


def make_test(test_id, cookies):
  global headers
  test_id = str(test_id)
  r4 = requests.get('https://sdo.pimunn.net/mod/quiz/view.php?id=' + test_id, headers=headers, cookies=cookies, verify=False)
  sesskey = BeautifulSoup(r4.text).find(attrs={'name': 'sesskey'})['value']
  params = (
    ('cmid', test_id),
    ('sesskey', sesskey),
    ('_qf__mod_quiz_preflight_check_form', '1')
  )
  r5 = requests.post('https://sdo.pimunn.net/mod/quiz/startattempt.php', headers=headers, params=params, cookies=cookies, verify=False)
  params = (
    ('cmid', test_id),
    ('sesskey', sesskey),
    ('finishattempt', '1'),
    ('attempt', BeautifulSoup(r5.text).find(attrs={'name': 'attempt'})['value'])
  )

  r6 = requests.post('https://sdo.pimunn.net/mod/quiz/processattempt.php', headers=headers, params=params, cookies=cookies, verify=False)
  return r6.text


def proccess_questions(q):
  q_t = q.find(attrs={'class': 'qtext'}).text
  try:
    answers = sorted([q.text.split('. ')[1] for q in q.find_all('label')])
    r_answers = q.find(attrs={'class': 'rightanswer'}).text.split(': ')[1]

    for i, a in enumerate(answers):
      if a in r_answers:
        answers[i] = '+  ' + answers[i]
      else:
        answers[i] = '   ' + answers[i]
    answers.append(r_answers)
  except:
    answers = sorted(q.find(attrs={'class': 'rightanswer'}).text.split(': ')[1].split(', '))
  return (q_t, '\n'.join(a for a in answers))


def process_test(test_text):
  b = BeautifulSoup(test_text)
  questions = b.find(attrs={'role': 'main'}).find_all(attrs={'class': 'content'})
  questions = [proccess_questions(q) for q in questions]
  return questions


def str2list(t):
  t = t.replace(' ', '').replace('\n', '').split(',')
  temp_t = []
  for num in t:
    if '-' in num:
      num = num.split('-')
      temp_t.extend(list(range(int(num[0]), int(num[1])+1)))
    else:
      temp_t.append(int(num))
  return temp_t


login = login_sdo('5313', '20111999')


def clicked_temp():
    global login
    test_ids = str2list(txt.get('1.0', 'end'))

    for test_id in test_ids:
        data = []
        count_new = 1
        count_try = 1  # сколько раз повторять, если не нашел ничего
        wait = 0
        while count_new:
            try:
                test = make_test(test_id, login)
                processed_test = process_test(test)
                count_new = 0
                for q in processed_test:
                    if q not in data:
                        count_new += 1
                        data.append(q)
                if count_new:
                    outxt.insert('1.0', str(test_id) + ' - ' + 'Добавлено: ' + str(count_new) + ' - Всего: ' + str(len(data)) + ' - Ожидаем ' + str(wait) + ' секунд\n')
                    time.sleep(wait + 1)
                else:
                    if count_try > 0:
                      count_new = 1
                      outxt.insert('1.0', str(test_id) + ' - ' + 'Ничего не нашли, но попробуем еще ' + str(count_try) + ' раз\n')
                      count_try -= 1
                      time.sleep(wait + 1)
                    else:
                      outxt.insert('1.0', str(test_id) + ' - ' + 'Завершено\n')

                with open(str(test_id) + '.txt', 'w', encoding='utf-8') as file:
                    output = '\n\n'.join('\n'.join(line for line in q) for q in data)
                    file.write(output)

            except TypeError:
                count_new = 1
                wait += 60
                outxt.insert('1.0', str(test_id) + ' - ' + 'Ожидаем дополнительно 60 секунд - Общее время ожидания: ' + str(wait) + ' секунд\n')
                time.sleep(61)


window = Tk()
window.title("SDO - test maker")
txt = Text(window, height=1)
outxt = scrolledtext.ScrolledText(window)
btn = Button(window, text="Запустить", command=lambda: Thread(target=clicked_temp).start())


txt.grid(column=0, row=0)
btn.grid(column=1, row=0)
outxt.grid(column=0, row=1)

window.mainloop()
