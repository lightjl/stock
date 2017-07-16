import tushare as ts
import pandas as pd
from datetime import datetime
import sendMail

class stock():
    def __init__(self):
        self.__yearRange = 5        #5年 从2012到2016
        self.__yearBegin = datetime.now().year-self.__yearRange
        #self.__getYearReportOnline()
        self.__flagUpdateReport = False
        flag = input('Update report now(Y/N):')
        if flag == 'Y' or flag == 'y':
            self.__flagUpdateReport = True

        self.getThingsEveryday()
        #print(yearbegin)
        self.__pdYearReport = [pd.read_excel('./' + \
                    str(self.__yearBegin+i) + 'y.xls','Report',na_values=['NA']) \
                         for i in range(self.__yearRange)]
        self.__pdYearProfit = [pd.read_excel('./' + \
                    str(self.__yearBegin+i) + 'Profit.xls', sheet_name='Profit',na_values=['NA'])\
                               for i in range(self.__yearRange)]
        self.__pdYearGrowth = [pd.read_excel('./' + \
                    str(self.__yearBegin+i) + 'Growth.xls','Growth',na_values=['NA']) \
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
        print('\n')

    def stockNotNow(self):
        return self.__stocksNotNow

    def getThingsEveryday(self):
        yearEnd = datetime.now().year-1

        if self.__flagUpdateReport:
            pdGrowthLastYear = ts.get_growth_data(yearEnd, 4)
            pdGrowthLastYear.to_excel('./' + \
                        str(yearEnd) + 'Growth.xls', sheet_name='Growth')
            pdProfitLastYear = ts.get_profit_data(yearEnd, 4)
            pdProfitLastYear.to_excel('./' + \
                        str(yearEnd) + 'Profit.xls', sheet_name='Profit')
            pdReportLastYear = ts.get_report_data(yearEnd, 4)
            pdReportLastYear.to_excel('./' + \
                        str(yearEnd) + 'y.xls', sheet_name='Report')


        self.__stockBasics = ts.get_stock_basics()  #获得昨天pe
        self.__stockBasics['code']=self.__stockBasics.index.astype(int)
        self.__stockBasics.sort_index(inplace=True)
        self.__stockTodayAll = ts.get_today_all()   #获得昨收
        self.__stockTodayAll['code'] = self.__stockTodayAll['code'].astype(int)
        self.__pdForwardEps = pd.merge(self.__stockBasics, self.__stockTodayAll, on='code')
        self.__pdForwardEps['feps'] = self.__pdForwardEps['settlement']/self.__pdForwardEps['pe']
        print('\n')
        #print(self.__pdForwardEps[self.__pdForwardEps.code == 601200])

    def peg_stock(self):
        self.per = 20
        for i in range(self.__yearRange):
            self.__pdYearReport[i].rename(columns={'profits_yoy': 'yoy'+str(i)}, inplace = True)
        self.pdYear4Report = self.__pdYearReport[0].copy()
        for i in range(1, self.__yearRange-1):
            self.pdYear4Report = self.pdYear4Report.merge(self.__pdYearReport[i],on='code')

        YP4 = self.pdYear4Report
        ''' 成长能力
        for i in range(self.__yearRange):   #5年 从2012到2016 1-4
            self.__pdYearGrowth[i].rename(columns={'nprg': 'yoy'+str(i)}, inplace = True)
        self.pdYear4Growth = self.__pdYearGrowth[0].copy()
        for i in range(1, self.__yearRange-1):
            self.pdYear4Growth = self.pdYear4Report.merge(self.__pdYearGrowth[i],on='code')

        YP4 = self.pdYear4Growth
        '''
        czg = YP4[              (YP4.yoy1 > self.per) &    #todo 3年增长
                (YP4.yoy2 > self.per) & (YP4.yoy3 > self.per)]

        #stockHaveReportLastYear = set(self.__pdYearGrowth[4].code.values)

        stockSet = set(czg['code'].values)
        stocksCZG = []
        stocksGD = []
        dy = ts.get_area_classified()
        for stock in stockSet:
            if self.__pdForwardEps[self.__pdForwardEps.code == stock].empty:
                continue
            pe = self.peNow(stock)
            if stock not in self.__stocksNow:
                inc = YP4[YP4.code == stock].yoy3.values[0]
                peg = pe/inc
                if dy[dy.code == ('%06d' % stock)]['area'].values[0] == '广东':
                    if pe < 50 and peg > 0 and peg < 2:
                        stocksGD.append(['%06d' % stock, YP4[YP4.code == stock].name_x.values[0][0], \
                                         round(pe, 2), round(inc, 2), round(peg, 2),
                                         dy[dy.code == ('%06d' % stock)]['area'].values[0]])
            else:   #去年年报已出
                inc = self.__pdYearReport[4][self.__pdYearReport[4].code == stock].yoy4.values[0]
            peg = pe/inc
            if pe < 30 and peg > 0 and peg < 0.8:
                #print('%06d %s pe %.2f, inc %.2f%%,peg %.2f' %(stock, YP4[YP4.code == stock].name_x.values[0][0], pe, inc, peg))
                stocksCZG.append(['%06d' % stock, YP4[YP4.code == stock].name_x.values[0][0], \
                                      round(pe, 2), round(inc, 2), round(peg, 2), dy[dy.code == ('%06d' % stock)]['area'].values[0] ])
        #print(stocksCZG)
        columns = ['code', 'name', 'pe', 'inc', 'peg', 'area']
        pdCZG = pd.DataFrame(data = stocksCZG, columns=columns)
        pdCZG.sort_values(by=['peg'], inplace=True)
        print(pdCZG)
        forecastSet = set(self.__forecastLastYear['code'].values)
        #print('002841')
        #print(YP4[YP4.code == 2841])
        #print(forecastSet & stockSet)
        stocksFCZG = []
        #print(dy[dy.code.isin(fpegStock)])
        for stock in stockSet:
            if self.__pdForwardEps[self.__pdForwardEps.code == stock].empty:
                continue

            if stock in forecastSet:
                if not isinstance(self.__forecastLastYear[self.__forecastLastYear.code == stock]['range'].values[0], float):
                    continue    #todo is not float
                #print('%06d, range %.2f' % (stock, self.__forecastLastYear[self.__forecastLastYear.code == stock]['range'].values[0]))
                pe = self.peNow(stock)
                inc = float(self.__forecastLastYear[self.__forecastLastYear.code == stock]['range'].values[0])

                peg = pe / inc
                if pe < 50 and peg > 0 and peg < 0.8:
                    #print('%06d %s pe %.2f, inc %.2f%%,peg %.2f' %(stock, YP4[YP4.code == stock].name_x.values[0][0], pe, inc, peg))
                    stocksFCZG.append(['%06d' % stock, YP4[YP4.code == stock].name_x.values[0][0], \
                                      round(pe, 2), round(inc, 2), round(peg, 2), dy[dy.code == ('%06d' % stock)]['area'].values[0] ])
                if dy[dy.code == ('%06d' % stock)]['area'].values[0] == '广东':
                    stocksGD.append(['%06d' % stock, YP4[YP4.code == stock].name_x.values[0][0], \
                                      round(pe, 2), round(inc, 2), round(peg, 2), dy[dy.code == ('%06d' % stock)]['area'].values[0] ])

        #print(stocksFCZG)
        pdFCZG = pd.DataFrame(data=stocksFCZG, columns=columns)
        pdFCZG.sort_values(by=['peg'], inplace=True)
        pdGD = pd.DataFrame(data=stocksGD, columns=columns)
        pdFCZG.sort_values(by=['peg'], inplace=True)
        print(pdFCZG)
        print('GD')
        print(pdGD)
        #pd.merge()
        #print(self.__pdYearReport)
        print(pdCZG['code'].values)
        print(pdFCZG['code'].values)

    def __getYearReportOnline(self):
        yearbegin = datetime.now().year-self.__yearRange
        pdYearProfit = [ts.get_profit_data(yearbegin+i,4) \
                        for i in range(self.__yearRange)]
        for i in range(self.__yearRange):
            pdYearProfit[i].to_excel('./' + \
                    str(yearbegin+i) + 'Profit.xls', sheet_name='Profit')

        pdReportLastYear = [ts.get_report_data(yearbegin+i,4) \
                        for i in range(self.__yearRange)]
        for i in range(self.__yearRange):
            pdReportLastYear[i].to_excel('./' + \
                    str(yearbegin+i) + 'y.xls', sheet_name='Report')


        pdYearGrowth = [ts.get_growth_data(yearbegin+i,4) \
                        for i in range(self.__yearRange)]
        for i in range(self.__yearRange):
            pdYearGrowth[i].to_excel('./' + \
                    str(yearbegin+i) + 'Growth.xls', sheet_name='Growth')

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
            #print(stockPdNow)
            #print(stockPdNow[stockPdNow.code == stock])
            if stockPdNow[stockPdNow.code == stock].empty:
                return self.__stockBasics[self.__stockBasics.code == stock]['pe'].values[0]
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


s = stock()
s.peg_stock()


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