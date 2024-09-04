DIMENSION RAIN(366),ACOM(20),NI(12),SRAIN(12),NII(12),PWW(12),PWD(12),
4ALPHA(12),BETA(12)
DATA NI/31,59,90,120,151,181,212,243,273,304,334,365/
DATA NII/31,60,91,121,152,182,213,244,274,305,335,366/
C*****************************************************************
C* INPUT # 01 - TITLE *
C* ACOM(I) - LOCATION IDENTIFICATION OR OTHER USER *
C* COMMENTS. 80 CHARACTER MAXIMUM *
C*****************************************************************
READ(2,98) (ACOM(I),I=1,20)
98 FORMAT(20A4)
WRITE(6,99) (ACOM(I),I=1,20)
99 FORMAT('1',20A4)

C*****************************************************************
C* INPUT # 02 - NUMBER OF YEARS, GENERATION CODES *
C* *
C* NYRS - YEARS OF DATA TO BE GENERATED *
C*****************************************************************
READ(2,100) NYRS,KGEN,ALAT,KTCF,KRCF
100 FORMAT(2I5,F5.2,2I5)

C****************************************************************
C* NOTE--INPUTS #03,04,05,06 ARE RAINFALL PARAMETERS *
C****************************************************************
C* INPUT # 03 - PROBABILITY OF WET GIVEN WET *
C* PWW(I) - 12 MONTHLY VALUES OF P(W/W) *
C****************************************************************
READ(2,103) (PWW(I),I=1,12)
103 FORMAT(12F6.0)
C****************************************************************
C* INPUT # 04 - PROBABILITY OF WET GIVEN DRY *
C* PWD(I) - 12 MONTHLY VALUES OF P(W/D) *
C****************************************************************
READ(2,103)(PWD(I),I=1,12)
C****************************************************************
C* INPUT # 05 - GAMMA DISTRIBUTION SHAPE PARAMETER *
C* ALPHA(I) - 12 MONTHLY VALUES OF SHAPE PARAMETER *
C****************************************************************
READ(2,103)(ALPHA(I),I=1,12)
C****************************************************************
C* INPUT # 06 - GAMMA DISTRIBUTION SCALE PARAMETER *
C* BETA(I) - 12 MONTH VALUES OF SCALE PARAMETER *
C****************************************************************
READ(2,103)(BETA(I),I=1,12)
101 FORMAT(9F8.0)


C****************************************************************
C* INPUT # 15 - MONTHLY VALUES OF ACTUAL MEAN RAINFALL *
C* OMIT IF KRCF = 0 *
C* RM(I) = 12 MONTHLY VALUES OF ACTUAL MEAN RAINFALL *
C****************************************************************
READ(2,103)(RM(I),I=1,12)
13 WRITE(6,700)
700 FORMAT(////,10X,'GENERATION PARAMETERS',//,15X,'PRECIPITATION')
WRITE(6,701)(PWW(I),I=1,12)
701 FORMAT(20X,'P(W/W) ',12F7.3)
WRITE(6,702) (PWD(I),I=1,12)
702 FORMAT(20X,'P(W/D) ',12F7.3)
WRITE(6,703) (ALPHA(I),I=1,12)
703 FORMAT(20X,'ALPHA ',12F7.3)
WRITE(6,704) (BETA(I),I=1,12)
704 FORMAT(20X,'BETA ',12F7.3)


IF(KRCF .EQ. 0) GO TO 52
WRITE(6,712)(RM(I),I=1,12)
712 FORMAT(10X,'ACT MEAN RAIN',12F7.2)
WRITE(6,713) (RG(I),I=1,12)
713 FORMAT(10X,'EST MEAN RAIN',12F7.2)
WRITE(6,714)(RCF(I),I=1,12)
714 FORMAT(10X,'RAIN CF ',12F7.3)
52 IF (KTCF .EQ. 0) GO TO 19

C****************************************************************
C****************************************************************
C*** Beginning of Annual DO Loop
C****************************************************************

DO 40 I = 1,NYRS
IYR = I

KK = 0
IJ = 1
C****************************************************************
C* INPUT # 16 - MEASURED RAINFALL FOR NYRS *
C* OMIT IF KGEN = 1 *
C* RAIN(I) - ACTUAL RAINFALL DATA - ONE VALUE PER DAY *
C* FOR NYRS *
C****************************************************************
21 READ(2,102) IYR,MO,IDAY,RAIN(IJ)
102 FORMAT(4X,3I2,20X,F10.0)

IF(KK .EQ. 1) GO TO 24
20 IDAYS = 365
IFLG= MOD(IYR,4)

IF(IFLG .EQ. 0) IDAYS = 366
KK = 1

IF(KGEN .EQ. 1) GO TO 28
24 IJ = IJ + 1

IF(IJ .LE. IDAYS) GO TO 21
28 CONTINUE

CALL WGEN(PWW,PWD,ALPHA,BETA)

DO 23 IM = 1,12
SRAIN(IM) = 0.
NWET(IM) = 0
23 CONTINUE

IM = 1
NYWET = 0
IDA = 0

DO 30 J=1,IDAYS
IDA = IDA + 1
IF(IDAYS .EQ. 366) GO TO 27
IF(J .GT. NI(IM)) GO TO 251
GO TO 29
251 IM = IM + 1
IDA = 1
GO TO 29
27 IF(J .GT. NII(IM)) GO TO 251
29 CONTINUE
C*****THE FOLLOWING STATEMENT WRITES DAILY GENERATED WEATHER ON AN
C*****EXTERNAL FILE (UNIT 8).
WRITE(8,200)IM,IDA,IYR,J,RAIN(J)
800 CONTINUE
C*****THE FOLLOWING STATEMENT PRINTS DAILY GENERATED WEATHER
WRITE(6,200)IM,IDA,IYR,J,RAIN(J)
200 FORMAT(2X,4I5,F7.2,3F7.0)
25 CONTINUE
IF(RAIN(J) .LT. 0.005) GO TO 26
NWET(IM) = NWET(IM) + 1
NYWET = NYWET + 1
26 CONTINUE
SRAIN(IM) = SRAIN(IM) + RAIN(J)
RYR = RYR + RAIN(J)
30 CONTINUE


WRITE(6,201) IYR
201 FORMAT(//,5X,'SUMMARY FOR YEAR',I5,/,2X,'MONTH 1
* 2 3 4 5 6 7 8 9 10
* 11 12 YR',/)
WRITE(6,207)(NWET(IM),IM=1,12),NYWET
207 FORMAT(2X,'WET DAYS ',13I8)
WRITE(6,202)(SRAIN(IM),IM=1,12),RYR
202 FORMAT(2X,'RAINFALL ',13F8.2)
40 CONTINUE

C****************************************************************
C*** End the annual Do loop *
C****************************************************************
C****************************************************************

999 STOP
END

C*****THE FOLLOWING SUBROUTINE GENERATED DAILY WEATHER DATA FOR
C*****ONE YEAR.
SUBROUTINE 	WGEN(PWW,PWD,ALPHA,BETA,RAIN)

DIMENSION RAIN(366),A(3,3),B(3,3),
3XIM1(3),E(3),R(3),X(3),RR(3),PWW(12),PWD(12),ALPHA(12),BETA(12),

DATA A/0.567,0.253,-0.006,0.086,0.504,-0.039,-0.002,-0.050,0.244/
DATA B/0.781,0.328,0.238,0.0,0.637,-0.341,0.0,0.0,0.873/
DATA XIM1/0.,0.,0./
DATA IX/9398039/
DATA IP/0/
IM = 1


C*****DETERMINE WET OR DRY DAY USING MARKOV CHAIN MODEL
CALL RANDN(RN)
IF(IP-0) 7,7,10
7 IF(RN - PWD(IM ))11,11,8
8 IP = 0
RAIN(IDAY) = 0.
GO TO 18
10 IF(RN-PWW(IM ))11,11,8
11 IP = 1

C*****DETERMINE RAINFALL AMOUNT FOR WET DAYS USING GAMMA DISTRIBUTION
AA = 1./ALPHA(IM)
AB = 1./(1.-ALPHA(IM))
TR1 = EXP(-18.42/AA)
TR2 = EXP(-18.42/AB)
SUM = 0.
SUM2 = 0.
12 CALL RANDN(RN1)
CALL RANDN(RN2)
IF(RN1-TR1) 61,61,62
61 S1 = 0.
GO TO 63
62 S1 = RN1**AA
63 IF(RN2-TR2) 64,64,65
64 S2 = 0.
GO TO 66
65 S2 = RN2**AB
66 S12 = S1 + S2
IF(S12-1.) 13,13,12
13 Z = S1/S12
CALL RANDN(RN3)
RAIN(IDAY) = -Z*ALOG(RN3)*BETA(IM)*RCF(IM)



C*****RAIN(IDAY) IS GENERATED RAINFALL FOR IDAY
15 IF(RAIN(IDAY)) 16,16,17
16 IP = 0
GO TO 18
17 IP = 1
18 IF(IP-1) 25,26,26

50 CONTINUE
RETURN
END


C*****THE FOLLOWING SUBROUTINE GENERATES A UNIFORM RANDOM NUMBER ON
C*****THE INTERVAL 0 - 1
SUBROUTINE RANDN(YFL)
DIMENSION K(4)
DATA K/2510,7692,2456,3765/
K(4) = 3*K(4)+K(2)
K(3) = 3*K(3)+K(1)
K(2)=3*K(2)
K(1) = 3*K(1)
I=K(1)/1000
K(1)=K(1)-I*1000
K(2)=K(2) + I
I = K(2)/100
K(2)=K(2)-100*I
K(3) = K(3)+I
I = K(3)/1000
K(3)=K(3)-I*1000
K(4)=K(4)+I
I = K(4)/100
K(4)=K(4)-100*I
YFL=(((FLOAT(K(1))*.001+FLOAT(K(2)))*.01+FLOAT(K(3)))*.001+FLOAT
*(K(4)))*.01
RETURN
END