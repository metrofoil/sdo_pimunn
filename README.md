# sdo_pimunn
A client of PIMU SDO


# Example
```python
sdo = SDO('1234', '123456')
test_id = '4558'
sesskey, attempt_id = sdo.start_attempt(test_id)
```

## QA (question & answers):
```python
page = sdo.get_page(0, test_id, attempt_id)
b = bs4.BeautifulSoup(page.text)
sdo.end_attempt(test_id, sesskey, attempt_id)
```
## QRA (question & right answers):
```python
test = sdo.end_attempt(test_id, sesskey, attempt_id)
b = bs4.BeautifulSoup(test.text)
```
