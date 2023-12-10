import requests
from bs4 import BeautifulSoup
from pprint import pprint
import time

url = 'https://airdoor.jp/list?si=d-131083&p={}'
target_url = url.format(1)
r = requests.get(target_url)
soup = BeautifulSoup(r.text,"html.parser")

contents = soup.find_all('div', {'class': 'PropertyPanel_propertyPanel__MqCpF'})
content = contents[0]

title = content.find('div', {'class': 'PropertyPanelBuilding_buildingTitle__NbWmb'})

divs = content.find_all('div', {'class': 'PropertyPanelBuilding_buildingInformationSection__AMRsh'})

# is-mt5 を持つ

# これらのdivタグ内のすべてのpタグを取得
buildingInfo = []
for div in divs:
    buildingInfo.extend(div.find_all('p'))

roomItems = content.find_all('a', {'class': 'PropertyPanelRoom_roomItem__3bVhC'})
roomItem = roomItems[0]
rentPrice = roomItem.find('div', {'class': 'PropertyPanelRoom_rentPrice__HO4Jp'})
roomDetail = roomItem.find('span', {'class': 'is-ml5'})
print(roomDetail)