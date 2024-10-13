from pyqtgraph.Qt import QtCore
import os, sys, codecs
import time
#import threading
import numpy as np
import pyvisa


from PyQt6 import uic, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QFileDialog, QDialog, QApplication,
    QPushButton, QMainWindow, QMessageBox
    )

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("Conductance_gui.ui", self)
        self.initUI()

    def initUI(self):
        self.gpib=False
#        self.gpib=True
        self.outputFileFullPath='/Users/okada/Documents/LNG/PyQt/CVMeas/tmp/'
#        self.resize(800,800)
        self.setWindowTitle("Conductance Measurement Program")
        self.mainTitle = "Conductance measurement Program Ver 2.0.0 (2024)"
        self.label_mainTitle.setText(self.mainTitle)
        self.show()

        # Redefinition of ids for RadioButton groups
        # Redefinition of id: Equivllent circuit model
        self.tupleEquiv=("", "Cp//G" , "C and D" , "Cs+Rs")
        self.tupleEquivset=("", "CPG" , "CSD" , "CSRS")
        self.buttonGroup_Equiv.setId(self.radioButton_Equiv_CpG, 1) # CpG = 1
        self.buttonGroup_Equiv.setId(self.radioButton_Equiv_CandD, 2) # C and D = 2
        self.buttonGroup_Equiv.setId(self.radioButton_Equiv_CsRs, 3) # Cs+Rs = 3

        # Redefinition of id: Start and End Frequency
#        self.tupleFrequency=("", "MHZ" , "KHZ" , "HZ")
        self.buttonGroup_StartFreq.setId(self.radioButton_StartFreq_100kHz, 5) #  100kHz = 10^5
        self.buttonGroup_StartFreq.setId(self.radioButton_StartFreq_10kHz, 4) #  10kHz= 10^4
        self.buttonGroup_StartFreq.setId(self.radioButton_StartFreq_1kHz, 3) #  1kHz= 10^3
        self.buttonGroup_StartFreq.setId(self.radioButton_StartFreq_100Hz, 2) #  100Hz= 10^2
        self.buttonGroup_EndFreq.setId(self.radioButton_EndFreq_1MHz, 6) #  1 MHz = 10^6
        self.buttonGroup_EndFreq.setId(self.radioButton_EndFreq_100kHz, 5) #  100 kHz = 5
        self.buttonGroup_EndFreq.setId(self.radioButton_EndFreq_10kHz, 4) #  10 kHz= 4

        # Redefinition of id: Sequence
#        self.tapleSequence=("","i->1->2->i", "i->1->i", "i->1")
#        self.buttonGroup_Sequence.setId(self.radioButton_Sequence_i12i, 1) # i->1->2->i = 1
#        self.buttonGroup_Sequence.setId(self.radioButton_Sequence_i1i, 2) # i->1->2->i = 1
#        self.buttonGroup_Sequence.setId(self.radioButton_Sequence_i1, 3) # i->1->2->i = 1

        # Redefinition of id: Integ. Time
        self.tupleInteg=("", "SHORT", "MEDIUM", "LONG")
        self.buttonGroup_IntegTime.setId(self.radioButton_Integ_Short, 1) # short = 1
        self.buttonGroup_IntegTime.setId(self.radioButton_Integ_Medium, 2) # medium = 2
        self.buttonGroup_IntegTime.setId(self.radioButton_Integ_Long, 3) # long = 3
        self.status_text=self.textBrowser_status.toPlainText()

#        self.pushButton_chooseOutputFile.clicked.connect(self.outputFileDialog)
        self.pushButton_chooseOutputDirectory.clicked.connect(self.outputFileDialog)
        # self.pushButton_execute.setEnabled(False)
        self.pushButton_execute.setEnabled(True)
        self.pushButton_execute.clicked.connect(self.execute_measurement)

        # timer
        # self.threading=threading.Timer(1, self.timer)
        #  self.threading.start()
        #self.timer.threadigt.connect(self.recurring_timer)
        #self.timer.start()

        self.fhandleFlag=False

        # initialize array for pyqtgraph curves
        self.datac1=np.empty(0) # data column 1 bias
        self.datac2=np.empty(0) # data column 2 Cp, Cs, C
        self.datac3=np.empty(0) # data column 3 Rp, Rs, D
        self.datac4f=np.empty(0) # data column 4 frequency for all biases
        self.datac4gw=np.empty(0) # data column 4 G/w for all biases

        # plot area settings
        self.p1=self.graphicsView1
        self.p1.setEnabled(True) # Activate Right clicking
        self.p1.setBackground("white")
        styles={'color':'b'}
        self.p1.setTitle("Cm vs freq. graph", color="black")
        self.p1.setLabel("bottom", "Frequency (Hz)", **styles)
        self.p1.setLabel("left", "Cm (F)", **styles)
#        self.p1.setRange(None, [1e3, 1e6], None, None, True, False)
#        self.p1.setRange(xRange=(1000, 1000000))
        self.p1.setLogMode(x=True, y=None)

        self.curve1=self.p1.plot(self.datac1, self.datac2, pen='b')
        self.p1.getAxis('left').setTextPen('k')
        self.p1.getAxis('left').setPen('k')
        self.p1.getAxis('bottom').setTextPen('k')
        self.p1.getAxis('bottom').setPen('k')

#        self.p1.setXRange(10.0**(float(self.buttonGroup_StartFreq.checkedId())), \
#                          10.0**(float(self.buttonGroup_EndFreq.checkedId())))
        
        self.p2=self.graphicsView2
        self.p2.setEnabled(True) # Activate Right clicking
        self.p2.setBackground("white")
        styles={'color':'b'}
        self.p2.setTitle("Gm vs freq.", color="black")
        self.p2.setLabel("bottom", "Frequency (Hz)", **styles)
        self.p2.setLabel("left", "Gm (S)", **styles)
        self.curve2=self.p2.plot(self.datac1, self.datac2, pen='brown')
        self.p2.getAxis('left').setTextPen('k')
        self.p2.getAxis('left').setPen('k')
        self.p2.getAxis('bottom').setTextPen('k')
        self.p2.getAxis('bottom').setPen('k')
        self.p2.setLogMode(x=True, y=None)

        self.p3=self.graphicsView3
        self.p3.setEnabled(True) # Activate Right clicking
        self.p3.setBackground("white")
        styles={'color':'b'}
        self.p3.setTitle("G/omega vs freq.", color="black")
        self.p3.setLabel("bottom", "Frequency (Hz)", **styles)
        self.p3.setLabel("left", "Reactance (S/(rad/s))", **styles)
        self.curve3=self.p3.plot(self.datac4f, self.datac4gw, pen=None, symbol="o", symbolSize=4)
        self.p3.getAxis('left').setTextPen('k')
        self.p3.getAxis('left').setPen('k')
        self.p3.getAxis('bottom').setTextPen('k')
        self.p3.getAxis('bottom').setPen('k')
        self.p3.setLogMode(x=True, y=None)

#        self.timer=QtCore.QTimer()
#        self.timer.setInterval(int(self.doubleSpinBox_stepwait.value()*1000))
#        self.textBrowser_status.append("Wait:"+str(int(self.doubleSpinBox_stepwait.value()*1000))+" msec")
#        self.timer.timeout.connect(self.recurring_timer)
        
        self.measuringFlag=False

        # File setting area
        self.outputFileName="test.dat"
        self.lineEdit_outputFileName.setText(self.outputFileName)
        self.outputFileFullPathName=os.path.join(self.outputFileFullPath, self.outputFileName) # join
        self.textEdit_outputFileFullPathName.setText(self.outputFileFullPathName) # 
        self.lineEdit_outputFileName.textChanged.connect(self.outputFilePath)

        ######## initialize GP-IB ########### 4284A LCR Meter
        if (self.gpib == True):
            rm=pyvisa.ResourceManager()
            self.textBrowser_status.append("GPIB0::"+str(self.spinBox_GPIB.value())+"::INSTR")
            self.meter=rm.open_resource("GPIB0::"+str(self.spinBox_GPIB.value())+"::INSTR")
            self.meter.write("*RST;*CLS")
            self.meter.write("FORM ASCII")
            self.meter.write("TRIG:SOUR BUS") # trigger by GP-IB command
            self.meter.write("DISP:PAGE MEAS")
            self.meter.write("ABORT") # ABORT measn reset trigger
            self.meter.write("INIT:CONT ON") # continuous mode
            self.meter.timeout=20000 # timeout in msec

        ######## end of initUI() ############

    def outputFileDialog(self):
#        fname = QFileDialog.getOpenFileName(self, 'Open file', '/Users/okada/Document/LNG/PyQt/CVMeas/tmp/')
        self.outputFileFullPath = QFileDialog.getExistingDirectory(self, 'Open file', self.outputFileFullPath)
        self.outputFileFullPathName=os.path.join(self.outputFileFullPath, self.outputFileName) # join
        self.textEdit_outputFileFullPathName.setText(self.outputFileFullPathName) # 

    def outputFilePath(self):
        self.outputFileName = self.lineEdit_outputFileName.text()
        self.outputFileFullPathName=os.path.join(self.outputFileFullPath, self.outputFileName)
        self.textEdit_outputFileFullPathName.setText(self.outputFileFullPathName)
        
    def warnNoFile(self):
        dlg=QMessageBox(self)
        dlg.setWindowTitle("Error !")
        dlg.setText("No Output File Specified")

        button = dlg.exec()
        button = QMessageBox.StandardButton(button)
        if button == QMessageBox.StandardButton.Ok:
            return

    def warnFileAlreadyExists(self):
        dlg=QMessageBox(self)
        dlg.setWindowTitle("Warning!")
        dlg.setText("Output File already exisis. Overwrite?")

        dlg.setStandardButtons(QMessageBox.StandardButton.Yes
                               | QMessageBox.StandardButton.No)
        dlg.setIcon(QMessageBox.Icon.Question)
        button = dlg.exec()
                
        if button == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False
        
    def execute_measurement(self):
        if self.measuringFlag == True : # Now measuring? Then return!
            return
        noffreq=0
        noffreq=(int(self.buttonGroup_EndFreq.checkedId()))-(int(self.buttonGroup_StartFreq.checkedId()))
        noffreq=noffreq*(self.spinBox_step_per_decade.value())
        self.textBrowser_status.append("N of freq:"+str(noffreq))

        # number of bias point for loop count
        nofbias=abs(self.doubleSpinBox_initialBias.value()-self.doubleSpinBox_bias1.value())/abs(self.doubleSpinBox_biasStep.value())
        nofbias=int(nofbias)+1
        self.textBrowser_status.append("N of bias:"+str(nofbias))

        # set step wait time
        self.timer=QtCore.QTimer()
        self.timer.setInterval(int(self.doubleSpinBox_stepwait.value()*1000))
        self.textBrowser_status.append("Wait:"+str(int(self.doubleSpinBox_stepwait.value()*1000))+" msec")
        self.timer.timeout.connect(self.recurring_timer)

        if os.path.exists(self.outputFileFullPath) == False or len(self.outputFileName) == 0:
            return
#        if self.measuringFlag == True or self.fhandleFlag == False :

        if os.path.exists(self.outputFileFullPathName) == True :
            if self.warnFileAlreadyExists() == False :
                return
        
        self.fhandle=codecs.open(self.outputFileFullPathName, 'w', 'utf-8')
        self.fhandleFlag=True

        self.status_text="Start Measurement"+"\n" + self.status_text
        self.measuringFlag=True
        self.pushButton_execute.setEnabled(False)


        # Frequency setting 4284A
#        self.freq=self.doubleSpinBox_startFreq.value()
        self.freq=10**(int(self.buttonGroup_StartFreq.checkedId()))
#        freqset=str(self.doubleSpinBox_freq.value())
        freqset=str(self.freq)
#        freqset="FREQ "+freqset+self.tupleFrequency[self.buttonGroup_StartFreq.checkedId()]
        freqset="FREQ "+freqset+"HZ"
        self.textBrowser_status.append(freqset)
        self.textBrowser_status.append("FUNC:IMP:RANG:AUTO ON")
        if (self.gpib==True):
            self.meter.write(freqset)
            self.meter.write("FUNC:IMP:RANG:AUTO ON") # auto range
            
        # Equivallent Circuit Model setting 4284A
        modelset="FUNC:IMP "+self.tupleEquivset[self.buttonGroup_Equiv.checkedId()]
#        modelset="FUNC:IMP CPG"
        self.textBrowser_status.append(modelset)
        if (self.gpib==True):
            self.meter.write(modelset)

        # Aperture time 4284A
        apertset="APER "+self.tupleInteg[self.buttonGroup_IntegTime.checkedId()]
        self.textBrowser_status.append(apertset)
        if (self.gpib==True):
            self.meter.write(apertset)
    
        # AC Amplitude setting 4284A
        ampset="VOLT "+str(self.spinBox_AClevel.value())+"MV"
        self.textBrowser_status.append(ampset)
        if (self.gpib==True):
            self.meter.write(ampset)

        # insulator capacitance, Cox, and series resistance, Rs
        self.Cox=self.doubleSpinBox_Cox.value()*1e-12 # (F)
        self.Rs=self.doubleSpinBox_Rs.value() # (Ohm)
        
        # Bias setting 4284A
        biasset="BIAS:STAT 1" # DC Bias ON
        self.textBrowser_status.append(biasset)
        if (self.gpib==True):
            self.meter.write(biasset)
        
        ## Sequence
        self.biasList=[0,0,0,0,0]
#        if self.buttonGroup_Sequence.checkedId()==1: # i -> 1 -> 2 -> i
#            self.biasList[0]=self.doubleSpinBox_initialBias.value()
#            self.biasList[1]=self.doubleSpinBox_bias1.value()
#            self.biasList[2]=self.doubleSpinBox_bias2.value()
#            self.biasList[3]=self.doubleSpinBox_initialBias.value()
#            self.biasList[4]=0
#        if self.buttonGroup_Sequence.checkedId()==2: # i -> 1 -> i
#            self.biasList[0]=self.doubleSpinBox_initialBias.value()
#            self.biasList[1]=self.doubleSpinBox_bias1.value()
#            self.biasList[2]=self.doubleSpinBox_initialBias.value()
#            self.biasList[3]=0
#            self.biasList[4]=0
#        if self.buttonGroup_Sequence.checkedId()==3: # i -> 1
        self.biasList[0]=self.doubleSpinBox_initialBias.value()
        self.biasList[1]=self.doubleSpinBox_bias1.value()
        self.biasList[2]=0
        self.biasList[3]=0
        self.biasList[4]=0
        self.vstep=abs(self.doubleSpinBox_biasStep.value())

        # measurementStart
        #
        self.startTime=time.time()
        #
        # Output File Header
        self.fhandle.write("# "+self.mainTitle+"\n")
        #   Header: Frequency
        if (self.gpib == True):
            self.meter.write("FREQ?")
            freqquery=self.meter.read()
        else:
            freqquery=str(self.freq)
        self.fhandle.write("# Freq.: "+freqquery.replace("\n","")+" Hz"+"\n")
        self.textBrowser_status.append("# "+freqquery.replace("\n","")+" Hz")
        #   Header: Equivalent model
#        self.fhandle.write("# Equiv. Model: "+self.tupleEquiv[self.buttonGroup_Equiv.checkedId()]+"\n")
        self.fhandle.write("# Equiv. Model: Cp-G"+"\n")
        #   Header: Initial wait
        #   Header: Step wait
        self.fhandle.write("# Step wait (s): "+str(self.doubleSpinBox_stepwait.value())+"\n")
        #   Header: Integration
        self.fhandle.write("# Integration: "+self.tupleInteg[self.buttonGroup_IntegTime.checkedId()]+"\n")
        #   Header: Format
        tupleHeaderFormat1=("", "Bias Cp Rp time",    "Bias C D time",     "Bias Cs Rs time")
        tupleHeaderFormat2=("", "(V) (F) (Ohm) (sec)","(V) (F) (1) (sec)", "(V) (F) (Ohm) (sec)")
        #self.fhandle.write("#"+tupleHeaderFormat1[self.buttonGroup_Equiv.checkedId()]+"\n")
        #self.fhandle.write("#"+tupleHeaderFormat2[self.buttonGroup_Equiv.checkedId()]+"\n")
        self.fhandle.write("# Freq Bias Cp G time\n")
        self.fhandle.write("# (Hz) (V) (F) (S) (sec)\n")
        
        #
#        self.sequenceNumber=4-self.buttonGroup_Sequence.checkedId()
        self.sequenceNumber=1
        self.bias=0
        self.sequenceStep=0 # #### should be considered
        self.stepNumber=0
        self.stepSubNumber=0
        # initial bias setting
        self.v1=self.biasList[self.sequenceStep]
        self.v2=self.biasList[self.sequenceStep+1]
        # print("v1, v2:", self.v1, self.v2)
        self.vstep0=self.vstep*(np.sign(self.v2-self.v1)) # vstep0 involves step direction in sign
        self.bias=self.v1

        self.timer.start() # Timer start
#        self.recurring_timer()
# end of definition of execute_measurement(self):

    def recurring_timer(self):
#        statusinfo=""
#        self.meter.write("STAT?")
#        statusinfo=self.meter.read()
#        print(statusinfo)
#        print(str(self.meter.read_stb()))
        # Measurement
        #
        # set bias 4284A
        self.textBrowser_status.append("---\n")
#        self.textBrowser_status.append("RB: "+str(self.checkBox_reverseBias.checkState()))
        if self.checkBox_reverseBias.isChecked():
            biasset="BIAS:VOLT "+str(-1.0*self.bias)
        else:
            biasset="BIAS:VOLT "+str(self.bias)
        self.textBrowser_status.append(biasset)
        if (self.gpib==True):
            self.meter.write(biasset)
        # display and store data
        self.lcdNumber_bias.display(self.bias)

        # trigger out for measurement 4284A
        if (self.gpib==True):
##            self.meter.write("TRIG:IMM")
##            self.meter.write("ABORT;:INIT")
#            self.meter.write("*TRG")
            self.meter.write("TRIG:IMM")
            self.presentTime=time.time()
            self.meter.write("FETC?")
        else:
            self.presentTime=time.time()

        # read data from 4284A
        rawdata=""
        if (self.gpib==True):
            rawdata=self.meter.read() # Format: DataA, DataB, Status
            currentBias=float(self.meter.query("BIAS:VOLT?"))
            if self.checkBox_reverseBias.isChecked():
                currentBias=-1.0*currentBias
            self.textBrowser_status.append(str(currentBias)+"V "+rawdata.replace("\n",""))
            currentFreq=float(self.meter.query("FREQ?"))
            self.textBrowser_status.append(str(currentFreq)+"Hz "+rawdata.replace("\n",""))
        else:
            if self.checkBox_reverseBias.isChecked():
                currentBias=self.bias
            self.textBrowser_status.append(str(currentBias)+"V "+rawdata.replace("\n",""))
            self.currentFreq=self.freq

        self.datac1=np.append(self.datac1, self.freq)
        if (self.gpib==True):
            splitdata=rawdata.split(',') # read parallel cm and gm
            cm=float(splitdata[0])
            gm=float(splitdata[1])
        else:
            cm=40e+3 + np.random.rand()*1.0e+3 + self.bias*1e+2
            gm=100e3+np.random.rand()*1e3
        self.datac2=np.append(self.datac2, cm)
        self.datac3=np.append(self.datac3, gm)

        self.datac4f=np.append(self.datac4f, currentFreq)

        omega=currentFreq*2.0*np.pi
#        Cox=42e-12
        gpdomega=omega*gm*self.Cox*self.Cox/(gm*gm + omega*omega*(self.Cox-cm)*(self.Cox-cm)) # gpdomgea: Gp/omega
        self.datac4gw=np.append(self.datac4gw, gpdomega)
        
        self.lcdNumber_cp.display(cm)
        self.lcdNumber_rp.display(gm)
        self.lcdNumber_freq.display(self.freq)
        
        self.textBrowser_status.append("stepNumber: "+str(self.stepNumber))
        self.textBrowser_status.append("bias: "+str(currentBias))
        #self.textBrowser_status.setText(self.status_text)
        self.curve1.setData(self.datac1, self.datac2)
        self.curve2.setData(self.datac1, self.datac3)
        self.curve3.setData(self.datac4f, self.datac4gw)

        # output data to the file
        self.fhandle.write(str(currentFreq)+ " " + str(currentBias) + " " + str(cm) + " " + str(gm) + " " \
                           + str(self.presentTime - self.startTime) + "\n")
        self.fhandle.flush() # Force to write data to the file

        # freq for next measurement
        self.stepNumber+=1
        self.freq=10.0**(int(self.buttonGroup_StartFreq.checkedId())+self.stepNumber / (self.spinBox_step_per_decade.value())/ \
                  ((int(self.buttonGroup_EndFreq.checkedId())) - (int(self.buttonGroup_StartFreq.checkedId()))))

        if self.freq < 10.0**(int(self.buttonGroup_EndFreq.checkedId())):
            self.textBrowser_status.append("freq: "+str(self.freq)) # setting frequency for next measurement
            freqset=str(self.freq)
            freqset="FREQ "+freqset+"HZ"
            self.textBrowser_status.append(freqset)
            self.textBrowser_status.append("FUNC:IMP:RANG:AUTO ON")
            if (self.gpib==True):
                self.meter.write(freqset)
            return

        # frequency scan is completed, thus change bias
        self.stepNumber=0

        self.datac1=np.empty(0) # data column 1 bias
        self.datac2=np.empty(0) # data column 2 Cp, Cs, C
        self.datac3=np.empty(0) # data column 3 Rp, Rs, D

        self.freq=10.0**(self.buttonGroup_StartFreq.checkedId()) # set start frequency for new bias
        self.textBrowser_status.append("freq: "+str(self.freq))
        freqset=str(self.freq)
        freqset="FREQ "+freqset+"HZ"
        self.textBrowser_status.append(freqset)
        self.textBrowser_status.append("FUNC:IMP:RANG:AUTO ON")
        if (self.gpib==True):
            self.meter.write(freqset)
            
        # bias for next measurement
        self.stepSubNumber+=1

#        if ((self.bias + self.vstep0)*np.sign(self.vstep0) > self.v2*np.sign(self.vstep0)) :
        if ((self.v1 + self.vstep0*self.stepSubNumber)*np.sign(self.vstep0) > self.v2*np.sign(self.vstep0)) :
            self.textBrowser_status.append("V2 edge")
            self.bias = self.v2 # critical edge due to finite vstep
        else:
            self.bias = self.v1+self.vstep0*self.stepSubNumber # normal step

        # Is bias within the range of current sequence step?
#        if ((self.bias)*np.sign(self.vstep0) >= (self.v2+self.vstep0*0)*np.sign(self.vstep0)):
        if ((self.v1 + self.vstep0*self.stepSubNumber)*np.sign(self.vstep0) > self.v2*np.sign(self.vstep0)) :
            # next bias is out of current step sequence
            self.textBrowser_status.append("out of current step")
            self.sequenceStep+=1 # Increment sequence
            self.stepSubNumber=0

            if self.sequenceStep+1 > self.sequenceNumber :
                self.timer.stop()
                self.textBrowser_status.append("END of Measurement")
                self.measuringFlag=False
                self.fhandle.close()
                self.pushButton_execute.setEnabled(True)
                
            else :
                self.v1=self.biasList[self.sequenceStep]
                self.v2=self.biasList[self.sequenceStep+1]
                self.vstep0=self.vstep*(np.sign(self.v2-self.v1)) # vstep0 involves step direction in sign

#    def measurementLoop(self):

        
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
