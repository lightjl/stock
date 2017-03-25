import stock
import tushare as ts
import time
import WorkInTime as wk
import sendMail as sm
from datetime import datetime

#print(s.peNow(600522))
class iw:
    def __init__(self, wl):
        '''
        :param wl: [[code, '字段', '目标方向', '目标', '有效性'],
                    [2078, 'price', '低'，7， True]]
        监控字段包括：价格、pe
        '''
        self.__stock = stock.stock()
        self.__watchList = wl

    def getNewdayThings(self):
        self.__stock.getThingsEveryday()

    def run(self):
        stockNow = ts.get_today_all()
        stockNow['code'] = stockNow['code'].astype(int)
        for row in self.__watchList[:]:
            if row[4] == False:
                #目标达成后
                continue
            printFlag = False
            name = stockNow[stockNow.code == row[0]]['name'].values[0]
            if row[1] == 'pe':
                if row[2] == '低':
                    if self.__stock.peNow(row[0]) <= row[3]:
                        printFlag = True
                        row[4] = False
                elif row[2] == '高':
                    if self.__stock.peNow(row[0]) >= row[3]:
                        printFlag = True
                        row[4] = False
            elif row[1] == 'price':
                price = stockNow[stockNow.code == row[0]]['trade'].values[0]
                if row[2] == '低':
                    if price <= row[3]:
                        printFlag = True
                        row[4] = False
                elif row[2] == '高':
                    if price >= row[3]:
                        printFlag = True
                        row[4] = False
            if printFlag:
                noticeText = "股票：%06d %s的%5s%s于%.2f"%(row[0], name, row[1],row[2],row[3])
                print(noticeText)
                sm.sendMail(noticeText, noticeText)
        pass

watchlist = [
            [600522, 'price', '低', 11.25, True, "中天科技"],
            [600522, 'pe', '低', 22.95, True],
            #[2078, 'price', '低', 7.1, True, "太阳纸业"],
            [2078, 'price', '高', 7.9, True, "太阳纸业"],
            [600816, 'pe', '低', 15, True, "安信信托"],
            [600816, 'price', '低', 11.11, True]
            ]#600816

timeTrade = [['9:25', '11:30'], ['13:00', '15:00']]
workTime = wk.WorkInTime(timeTrade)

for text in watchlist:
    print(text)
ic = iw(watchlist)
while True:
    # 周一到周五
    if datetime.now().weekday() < 5:
        workTime.relax()
        if workTime.isNewDay():
            ic.getNewdayThings()
        ic.run()
        time.sleep(5)