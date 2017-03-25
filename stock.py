import tushare as ts
import pandas as pd
from datetime import datetime
import sendMail

class stock():
    def __init__(self):
        self.getThingsEveryday()
        self.__yearRange = 5        #5年 从2012到2016
        self.__yearBegin = datetime.now().year-self.__yearRange
        #print(yearbegin)
        self.__pdYearReport = [pd.read_excel('D:/zzz/joinquant/data4stock/' + \
                    str(self.__yearBegin+i) + 'y.xls','Report',na_values=['NA']) \
                         for i in range(self.__yearRange)]
        self.__pdYearProfit = [pd.read_excel('D:/zzz/joinquant/data4stock/' + \
                    str(self.__yearBegin+i) + 'Profit.xls', sheet_name='Profit',na_values=['NA'])\
                               for i in range(self.__yearRange)]

        self.__stocksL = set(self.__pdYearReport[3].code.values)
        self.__stocksNow = set(self.__pdYearReport[4].code.values)      # 出了年报的股票
        self.__stocksNotNow = set(self.__stocksL - self.__stocksNow)
        #self.__stockNotNew = self.__stockBasics[(self.__stockBasics.timeToMarket < 20160101) &
        #                    (self.__stockBasics.timeToMarket != 0)].index.values.astype(int)
        #self.__stockNotNew
        #print(self.__stockNotNew.index.values.astype(int))    #每天更新一次
        pdYPL = self.__pdYearProfit[3]
        pdYRL = self.__pdYearReport[3]
        self.__pdYearReportNear = self.__pdYearReport[4].append(pdYRL[pdYRL.code.isin(self.__stocksNotNow)])
        self.__pdYearProfitNear = self.__pdYearProfit[4].append(pdYPL[pdYPL.code.isin(self.__stocksNotNow)])
        self.__minute_update = -1
        self.__forecastLastYear = ts.forecast_data(datetime.now().year-1, 4)
        self.__forecastLastYear['code'] = self.__forecastLastYear['code'].astype(int)
        #print(self.__pdYearReportNear[self.__pdYearReportNear.code==600522])
        #print(self.__pdYearReportNear[self.__pdYearReportNear.code == 600067])
        #pdtest.to_excel('D:/zzz/joinquant/data4stock/' + str('test') + 'Profit.xls', sheet_name='Profit')

    def stockNotNow(self):
        return self.__stocksNotNow

    def getThingsEveryday(self):
        yearEnd = datetime.now().year-1
        pdProfitLastYear = ts.get_profit_data(yearEnd, 4)
        pdProfitLastYear.to_excel('D:/zzz/joinquant/data4stock/' + \
                    str(yearEnd) + 'Profit.xls', sheet_name='Profit')
        pdReportLastYear = ts.get_report_data(yearEnd, 4)
        pdReportLastYear.to_excel('D:/zzz/joinquant/data4stock/' + \
                    str(yearEnd) + 'y.xls', sheet_name='Report')
        self.__stockBasics = ts.get_stock_basics()  #获得昨天pe
        self.__stockBasics['code']=self.__stockBasics.index.astype(int)
        self.__stockBasics.sort_index(inplace=True)
        self.__stockTodayAll = ts.get_today_all()   #获得昨收
        self.__stockTodayAll['code'] = self.__stockTodayAll['code'].astype(int)
        self.__pdForwardEps = pd.merge(self.__stockBasics, self.__stockTodayAll, on='code')
        self.__pdForwardEps['feps'] = self.__pdForwardEps['settlement']/self.__pdForwardEps['pe']
        print('\n')
        #print(self.__pdForwardEps[self.__pdForwardEps.code == 600522])

    def peg_stock(self):
        self.per = 10
        for i in range(self.__yearRange):
            self.__pdYearReport[i].rename(columns={'profits_yoy': 'yoy'+str(i)}, inplace = True)
        self.pdYear4Report = self.__pdYearReport[0].copy()
        for i in range(1, self.__yearRange-1):
            self.pdYear4Report = self.pdYear4Report.merge(self.__pdYearReport[i],on='code')

        YP4 = self.pdYear4Report
        czg = YP4[(YP4.yoy0 > self.per) & (YP4.yoy1 > self.per)
                & (YP4.yoy2 > self.per) & (YP4.yoy3 > self.per)]

        stockHaveReportLastYear = set(self.__pdYearReport[4].code.values)

        stockSet = set(czg['code'].values)
        for stock in stockSet:
            pe = self.peNow(stock)
            if stock not in self.__stocksNow:
                inc = YP4[YP4.code == stock].yoy3.values[0]
            else:   #去年年报已出
                inc = self.__pdYearReport[4][self.__pdYearReport[4].code == stock].yoy4.values[0]
            peg = pe/inc
            if pe < 30 and peg > 0 and peg < 0.46:
                    print('%06d %s pe %.2f, inc %.2f%%,peg %.2f' %(stock, YP4[YP4.code == stock].name_x.values[0][0], pe, inc, peg))

        forecastSet = set(self.__forecastLastYear['code'].values)
        #print('002841')
        #print(YP4[YP4.code == 2841])
        print(forecastSet & stockSet)
        print('forecast')
        for stock in stockSet:
            if stock in forecastSet:
                #print('%06d, range %.2f' % (stock, self.__forecastLastYear[self.__forecastLastYear.code == stock]['range'].values[0]))
                pe = self.peNow(stock)
                inc = self.__forecastLastYear[self.__forecastLastYear.code == stock]['range'].values[0]
                peg = pe/inc
                if pe < 50 and peg > 0 and peg < 0.46:
                    print('%06d %s pe %.2f, inc %.2f%%,peg %.2f' %(stock, YP4[YP4.code == stock].name_x.values[0][0], pe, inc, peg))
        #pd.merge()
        #print(self.__pdYearReport)

    def __getProfitOnline(self):
        yearbegin = datetime.now().year-self.__yearRange
        pdYearProfit = [ts.get_profit_data(yearbegin+i,4) \
                        for i in range(self.__yearRange)]
        for i in range(self.__yearRange):
            pdYearProfit[0].to_excel('D:/zzz/joinquant/data4stock/' + \
                    str(yearbegin+i) + 'Profit.xls', sheet_name='Profit')

    def pickHHCG(self):
        #gross_profit_rate 毛利率
        pdHHCG1 = self.__pdYearProfitNear[(self.__pdYearProfitNear.gross_profit_rate > 50) & \
                                          (self.__pdYearProfitNear.roe > 10) &
                                           (self.__pdYearProfitNear.code.isin(self.__stockNotNew))]
        setStageOne = set(pdHHCG1.code)
        pdYRN = self.__pdYearReportNear
        pdHHCG2 = pdYRN[(pdYRN.code.isin(setStageOne)) &
                        (pdYRN.net_profits/pdYRN.eps < 10000) ]
        self.__stockHHCG = set(pdHHCG2.code.values)
        #print(self.__stockBasic[self.__stockBasic.code == 600522])
        #print(self.__stockBasics[self.__stockBasics.code.isin(self.__stockHHCG)])
        return self.__stockHHCG

    def get_today_all(self):
        minuteNow = datetime.now().minute
        if self.__minute_update != minuteNow:
            self.__minute_update = minuteNow
            self.__today_all = ts.get_today_all()
            print('\n')
        return self.__today_all

    def peNow(self, stock):
        # 周一到周五
        if datetime.now().weekday() < 5:
            stockPdNow = self.get_today_all()
            stockPdNow['code'] = stockPdNow['code'].astype(int)
            #print(stockPdNow[stockPdNow.code == stock])
            priceNow = stockPdNow[stockPdNow.code == stock]['trade'].values[0]
            if priceNow == 0:
                return self.__stockBasics[self.__stockBasics.code == stock]['pe'].values[0]
            forwardEps = self.__pdForwardEps[self.__pdForwardEps.code == stock]['feps'].values[0]
            return round(priceNow/forwardEps,2)
        else:
            return self.__stockBasics[self.__stockBasics.code == stock]['pe'].values[0]

        def ai_gzscx(self):         #分配预案的次新股
            df = ts.profit_data(top=1000, year=datetime.now().year-1)
            #df = df[df.shares >= 1]
            df.sort_values(by='shares', ascending=False)
            df['code'] = df['code'].astype(int)
            dfCX = set(df['code'].values)
            pd = ts.get_industry_classified()
            pd['code'] = pd['code'].astype(int)
            # print(pd[pd.c_name == '次新股'])
            # print(set(pd['c_name'].values))
            setCX = set(pd[pd.c_name == '次新股']['code'].values)
            print('\n')
            print(df[df.code.isin(setCX)])

#pd2014y = ts.get_report_data(2014,4)
#pd2014y.to_excel('D:/zzz/joinquant/data4stock/2014y.xls', sheet_name='Report')
#pd2014y = pd.read_excel('D:/zzz/joinquant/data4stock/2014y.xls','Report',na_values=['NA'])
#print(pd2014y)
#os.path.exists('D:/zzz/joinquant/data4stock/2014y.xls')
#pd2016y = pd.read_excel('D:/zzz/joinquant/data4stock/2016y.xls','Report',na_values=['NA'])
#print(pd2016y.code.values)
'''
s = stock()
s.peg_stock()
'''
#pdF = ts.forecast_data(2016, 4)
#stockList = set(pdF['code'].values.astype(int))
'''
nullSet = stockNotNow - stockList
print('\n stockList')
print(stockList)
print('\n stockNotNow')
print(stockNotNow)
print('\n nullSet')
print(nullSet)
pdF = pdF[pdF.range > 1000]
#print(pdF)
'''
'''
s = stock()
print(s.peNow(600522))
s = stock()
stockHHCG = s.pickHHCG()
# [300496, 300427, 300470, 300394, 300491, 2718, 300488, 600593]
#print(stockHHCG)
#print(ts.get_today_all())
stockNow = ts.get_today_all()
stockNow['code'] = stockNow['code'].astype(int)
#print(stockNow)
#stockNow.drop(labels=['volume', 'turnoverratio', 'amount', 'open', 'high', 'low', 'settlement'], inplace=True)
#stockNow.drop(labels=['volume', 'turnoverratio', 'amount', 'open', 'high', 'low', 'settlement'], axis=1, inplace=True)
#stockNow.drop([stockNow.columns[[2, 4, 5, 6, 7, 8]]], axis=1, inplace=True)
del stockNow['volume']
del stockNow['turnoverratio']
del stockNow['amount']
del stockNow['changepercent']
stockNow.sort_values(["code"], inplace=True)
#print(stockNow.columns[[2, 4, 5, 6, 7, 8]])
print(stockNow[stockNow.code.isin(stockHHCG)])

'''