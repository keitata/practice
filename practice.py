# coding: UTF-8
import struct
import datetime
import time
import operator
#モジュール（serialというフォルダ）
#pipでローカルにコピーさせて、import でモジュールを持ってくる
import serial

class Sps30:
    def __init__(self, device_name):
        self.ser = serial.Serial(port=device_name, baudrate=115200, timeout=1)
        self.listReceiveFrame = []
        
        
    def start(self,seconds):
        """ アイドルモードを測定モードにする
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """        
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x00,0x02,[0x01,0x03])
        self.ser.write(strPacket)
        return self.commonCheck(seconds)

        
    def stop(self,seconds):
        """ アイドルモードにする
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """        
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x01,0x00,None)
        self.ser.write(strPacket)
        return self.commonCheck(seconds)


    def read_values(self,seconds):
        """ 測定値の読み込みをする
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x03,0x00,None)
        self.ser.write(strPacket)
        return self.commonCheck(seconds)
        

    def readCleaning(self,seconds):
        """自動ファンクリーニング間隔を読み取るフレームを作る
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """        
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x80,0x01,[0x00])
        self.ser.write(strPacket)
        return self.commonCheck(seconds)


    def writeCleaning(self,seconds):
        """自動ファンクリーニング間隔を書き込むフレームを作る
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """        
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x80,0x05,[0x00,0x00,0x09,0x3a,0x80])
        self.ser.write(strPacket)
        return self.commonCheck(seconds)


    def startFanCleaning(self,seconds):
        """ファンクリーニングを行う
        引数secondsは受信を待つ（単位：秒）
        戻り値：boolean
        正しく実行→True/それ以外→False
        """        
        self.ser.flushInput()
        strPacket = self.makeMOSI(0x56,0x00,None)
        self.ser.write(strPacket)
        return self.commonCheck(seconds)


    def commonCheck(self,seconds):
        time.sleep(seconds)
        listReceiveFrame= self.makeListOfReceiveFrame()
        self.ser.flushOutput()
        if self.receiveFrameStateCheck(listReceiveFrame):
            if self.receiveFramefiveCheck(listReceiveFrame):
                if self.receiveFrameCorrectCheck(listReceiveFrame):
                    return True
                else:
                    print("receiveFrameCorrectCheckでFalse")
            else:
                print("receiveFramefiveCheckメソッドでFalse")        
        else:
            pass
            # print("receiveFrameStateCheckメソッドでFalse")
            
        return False


    def makeMOSI(self,CMD, length, data):
        """送信フレームを作成
        エスケープ処理
        戻り値：String
        """
        # 開始、ADRを示す　ADRは常に０
        sendPacket = [0x7E,0x00]
        #CMDを追加
        sendPacket.append(CMD)
        #lengthを追加
        sendPacket.append(length)
        #TXdataを追加　（start関数は2つある）
        try:
            for i in data:
                sendPacket.append(i)
        except TypeError:
            pass
        #CHKを作成
        checksum = self.createChecksum(sendPacket)
        #CHKの追加
        sendPacket.append(checksum)

        sendPacket.append(0x7E)

        # エスケープ処理　sendPacket[1:-1]は開始終了を除く
        for index,element in enumerate(sendPacket[1:-1]):
            # スライスで先頭をずらした分indexに加算する
            #sendPacket[1:-1] = [0x00,0x80,0x01,0x00,0x7D]
            #sendPacket = [0x7E, 0x00, 0x80, 0x01, 0x00, 0x7D, 0x01, 0x7E]
            index += 1
            if element == 0x7E:
                sendPacket[index:index+1] = [0x7D,0x5E]
            elif element == 0x7D:
                sendPacket[index:index+1]=[0x7D,0x5D]
            elif element == 0x11:
                sendPacket[index:index+1] =[0x7D,0x31]
            elif element == 0x13:
                sendPacket[index:index+1] =[0x7D,0x33]
        # print('送信フレーム:{}'.format(sendPacket))


        #listを文字列に変換する
        strPacket = ''
        for byte in sendPacket:
            strPacket += chr(byte)
        # print strPacket

            
        return strPacket


    def createChecksum(self,packetWithoutEnd):
        """チェックサムを算出
        戻り値：Int
        """
        # hex で数字を16進数表記の文字列になる　0xを除いた　
        # 16進数は15までは一桁で表す
        # 例 0x6の場合 LSBは6
        # 例 0xf532aの場合 LSBは2a
        # LSBは最下位バイト
        total = 0
        #checksumを算出
        #packetWithoutEnd=[開始,ADR,CMD,Length,TXdata]
        for byte in packetWithoutEnd[1:]: #開始を除くリスト
            total += byte
        #一桁の判別
        # 16進数は15までは一桁で表す

        if total < 16:
            totalOfLSB= hex(total)[-1:] 
        else:
            totalOfLSB = hex(total)[-2:]
        # int で16進表記されている文字列を数字にしている
        # intに16進の文字列と教えている
        # 第二引数を書かないと（10進がデフォルト）
        
        totalOfLSB = int(totalOfLSB,16)
        #totalOfLSB = int(totalOfLSB,10)
        #print(totalOfLSB)
        
        checksum = operator.xor(totalOfLSB, 0xff)
        
        
        return checksum

    
    def receiveFrameStateCheck(self,receiveFrame):
        """受信フレームの状態を表すバイトの確認
        戻り値：boolean
        """
        if receiveFrame[3] == 0x00:
            return True
        else:
            if receiveFrame[3] == 0x01:
                print("Error:0x01 コマンドのデータ長が正しくない")
            elif  receiveFrame[3] == 0x02:
                print("Error:0x02 存在しないコマンド")                
            elif receiveFrame[3] == 0x03:
                print("Error:0x03 コマンドのアクセス権がない")
            elif receiveFrame[3] == 0x04:
                print("Error:0x04 不正なコマンドパラめーあまたは許容範囲外のパラメータ")
            elif receiveFrame[3] == 0x28:
                print("Error:0x28 内部関数の引数が範囲外")
            elif receiveFrame[3] == 0x43:
                print("Error:0x43 現在の状態ではコマンドは許可されてない")
                
            return False


    def receiveFramefiveCheck(self,receiveFrame):
        """5バイト未満の場合が連続5回続けば、プログラム強制終了
        戻り値:Boolean
        """
        # del receiveFrame[:]
        # receiveFrame.append(0x7E)
        # receiveFrame.append(0x01)
        # receiveFrame.append(0x00)
        # receiveFrame.append(0x03)

        
        fiveCheckCount = 0
        # receiveFrame=[開始,ADR,CMD,status,Length,RXdata,CHK,終了]
        # statusは受信フレームのみ存在、通信及びエラーを格納
        # TX,RXdataは0～255バイトが格納できるデータ
        if len(receiveFrame[1:-1]) < 5:
            file = open('new.csv','a')
            dt_now = datetime.datetime.now()
            error_message = "5バイト未満の不正なデータを検知しました"
            file.write(str(dt_now.date()) + ',' + str(dt_now.time()).split('.')[0] + '\n')
            file.write(error_message)
            file.close
            fiveCheckCount += 1
            print(error_message)

            if fiveCheckCount == 5:
                exit()
            else:
                return False
        else:
            fiveCheckCount = 0
            return True

            
    def receiveFrameCorrectCheck(self,receiveFrame):
        """受信フレームが正しいフレームかをチェック
        戻り値：Boolean
        """
        correctCheckCount = 0
        total = 0
        for byte in receiveFrame[1:-2]: #開始、CHK、終了を除くリスト
            total += byte

        # hex で数字を16進数表記の文字列になる　0xを除いた　
        # 16進数は15までは一桁で表す
        # 例 0x6の場合 LSBは6
        # 例 0xf532aの場合 LSBは2a
        # LSBは最下位バイト
        if total < 16:
            #hexは文字列を返す
            totalOfLSB = hex(total)[-1:]
        else:
            totalOfLSB = hex(total)[-2:]
        # int で16進表記されている文字列を数字にしている
        # intに16進の文字列と教えている
        # 第2引数を書かないと（10進がデフォルト）
        totalOfLSB = int(totalOfLSB,16)

        checksum = operator.xor(totalOfLSB,0xff)

        #print(receiveFrame)
        # print checksum
        if checksum == receiveFrame[-2]:
            correctCheckCount = 0
            return True
        else:
            correctCheckCount += 1
            if correctCheckCount == 5:
                exit()
            return False
            
            
    def makeListOfReceiveFrame(self):
        """受信フレーム(バイト列)を逆エスケープ
        戻り値：List<Int>
        """

        escapeDict = {
            0x5e: 0x7e,
            0x5d: 0x7d,
            0x31: 0x11,
            0x33: 0x13
        }
        del self.listReceiveFrame[:]
        flag = False
        while self.ser.readable():
            try:
                #ordの引数は一文字
                intCode = ord(self.ser.read(1)) 
            except TypeError:
                print("受信フレーム取得エラー")
                break
            # intCode = ord(self.ser.read(1)) 
            #センサがつながっていないとエラーになるその処理もいる
            if intCode == 0x7d:
                nextIntCode = ord(self.ser.read(1))
                intCode = escapeDict[nextIntCode]
            else: 
                if flag == False and intCode ==0x7E:
                    flag =True
                elif flag == True and intCode==0x7E:
                    self.listReceiveFrame.append(intCode)
                    break
    
            self.listReceiveFrame.append(intCode)
        # print('受信フレーム:{}').format(listReceiveFrame)
        return self.listReceiveFrame


    def createCSV(self,listReceiveFrame):
        length=listReceiveFrame[4]
        if length == 0:
            pass
        elif length % 4 != 0:
            pass
        else:
            file = open('new.csv','a')
            itemlist =[
                "PM1.0 の重さ",
                "PM2.5 の重さ",
                "PM4.0 の重さ",
                "PM10 の重さ",
                "PM0.5 の数",
                "PM1.0 の数",
                "PM2.5 の数",
                "PM4.0 の数",
                "PM10 の数",
                "代表的な微粒子のサイズ"
            ]         
            #dataは１０進　int型
            #listReceiveFrame=[開始,ADR,CMD,status,Length,RXdata,CHK,終了]
            data = listReceiveFrame[5:-2]
            # print type(data[0]) #int
            dt_now = datetime.datetime.now()
            file.write(str(dt_now.date()) + ',' + str(dt_now.time()).split('.')[0] + '\n')
            # 浮動小数点
            for i in xrange(0,length,4):
                # print(data[i])
                # print(data[i+1])
                # print(data[i+2])
                # print(data[i+3])

                #センサからのデータはマイナスはないのでunsigned char型に直す
                bstr = struct.pack('B', data[i]) + struct.pack('B', data[i+1]) + struct.pack('B', data[i+2]) + struct.pack('B', data[i+3])
                #dataは10進だから2進に変える
                result = struct.unpack('>f', bstr)[0]
                item = itemlist[i / 4]
                print('{}:{}'.format(item, str(result)))
                #print(f'{item}:{str(result)}')
                file.write(item + ',' + str(result) + '\n')
            file.close()
