@echo off
rem ============================================================
rem  라쿤봇 설치 도우미
rem
rem  하는 일 : 파이썬을 찾아 roboid 모듈을 설치하고,
rem            BLE 동글이 COM 포트로 잡히는지까지 확인한다.
rem
rem  쓰는 법 : 더블클릭
rem            라쿤봇_설치_도우미.bat /auto   질문 없이 roboid 만
rem            라쿤봇_설치_도우미.bat /full   질문 없이 전체 패키지
rem
rem  저장 규칙 : 인코딩 CP949, 줄바꿈 CRLF. UTF-8 로 저장하면 한글이 깨진다.
rem  고칠 때   : 괄호 블록 안의 echo 에는 따옴표 밖 괄호를 쓰지 않는다.
rem              설치는 항상 %PY% -m pip 형태로 쓴다.
rem ============================================================

rem --- 준비 : 폴더 위치 저장, 코드 페이지 고정 ---
set "HERE=%~dp0"
for /f "tokens=2 delims=:." %%a in ('chcp') do set "OLDCP=%%a"
chcp 949 >nul
title 라쿤봇 설치 도우미

set "AUTO="
set "FULL="
if /i "%~1"=="/auto" set "AUTO=1"
if /i "%~1"=="/full" set "AUTO=1" & set "FULL=1"

echo.
echo ============================================================
echo    라쿤봇 설치 도우미
echo    roboid 모듈 설치 + 동글 연결 확인
echo ============================================================
echo.

rem ============================================================
rem  [1/5] 파이썬 찾기
rem ============================================================
echo [1/5] 파이썬을 찾습니다...
set "PY="

rem (1) py 실행기 - 파이썬을 설치하면 함께 깔리므로 PATH 와 무관하게 동작한다
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=py -3"

rem (2) PATH 의 python - 마이크로소프트 스토어 가짜 python 은 여기서 걸러진다
if not defined PY (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)

rem (3) 설치 폴더 직접 검색
if not defined PY (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
)
if not defined PY (
    for /d %%D in ("%ProgramFiles%\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
)
if not defined PY (
    for /d %%D in ("C:\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
)

if not defined PY goto NO_PYTHON

rem 실제 설치 폴더를 파이썬에게 직접 물어본다
rem 경로에 공백이 섞여도 안전하도록 임시 파일을 거친다
%PY% -c "import sys, os; print(os.path.dirname(sys.executable))" > "%TEMP%\racoonbot_pydir.txt" 2>nul
set /p PYDIR=<"%TEMP%\racoonbot_pydir.txt"
del "%TEMP%\racoonbot_pydir.txt" >nul 2>&1

echo      찾았습니다 - %PYDIR%
%PY% -c "import sys; print('     버전 -', sys.version.split()[0])"
echo.
echo      참고 - 이 교육 과정은 파이썬 3.13 에서 전체 동작을 확인했습니다.
echo.

rem ============================================================
rem  [2/5] pip 확인
rem ============================================================
echo [2/5] pip 를 확인합니다...
%PY% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo      pip 가 없어 설치합니다...
    %PY% -m ensurepip --upgrade >nul 2>&1
)
%PY% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo      [실패] pip 를 설치할 수 없습니다. 파이썬을 다시 설치해 주세요.
    goto END_FAIL
)
echo      준비됨
echo.

rem 설치파일 폴더가 옆에 있으면 인터넷을 쓰지 않는다
rem 교사 PC 에서 미리 받는 명령 : python -m pip download roboid -d 설치파일
set "PIPOPT="
if exist "%HERE%설치파일\" (
    echo      설치파일 폴더를 찾았습니다 - 인터넷을 쓰지 않습니다
    set PIPOPT=--no-index --find-links "%HERE%설치파일"
    echo.
)

rem ============================================================
rem  [3/5] roboid 설치
rem ============================================================
echo [3/5] roboid 모듈을 설치합니다...
%PY% -c "import roboid" >nul 2>&1
if errorlevel 1 (
    %PY% -m pip install %PIPOPT% roboid
) else (
    echo      이미 설치되어 있습니다
)
echo.

rem ============================================================
rem  [4/5] 설치 확인
rem ============================================================
echo [4/5] 설치를 확인합니다...
%PY% -c "import roboid, serial; print('     roboid', roboid.__version__, '/ pyserial', serial.__version__)"
if errorlevel 1 (
    echo      [실패] roboid 를 불러올 수 없습니다.
    echo      인터넷 연결을 확인하고 다시 실행해 주세요.
    goto END_FAIL
)
echo.

rem ============================================================
rem  [5/5] 동글 확인
rem ============================================================
echo [5/5] 연결된 COM 포트를 확인합니다...
echo.
%PY% -c "import serial.tools.list_ports as p; L=list(p.comports()); [print('       ', x.device, '|', x.description) for x in L] or print('        (없음)')"
echo.
echo      위 목록에 동글이 보이면 그 번호를 등록카드에 적으세요.
echo      목록이 비어 있으면 - USB 동글이 꽂혀 있는지 먼저 보세요.
echo      노트북 내장 블루투스로는 연결되지 않습니다. 동글이 필요합니다.
echo.

rem ============================================================
rem  (질문) 주제 6 이후 패키지
rem ============================================================
if defined FULL goto EXTRAS
if defined AUTO goto ASK_PATH
echo ------------------------------------------------------------
echo  주제 6 이후에 쓰는 패키지도 지금 설치할까요?
echo  카메라, 손동작, 음성 인식용입니다. 용량이 큽니다.
echo  주제 1 에는 필요하지 않습니다.
echo ------------------------------------------------------------
set "ANS=N"
set /p ANS="  설치할까요? (Y/N) : "
if /i not "%ANS%"=="Y" goto ASK_PATH

:EXTRAS
echo.
echo      추가 패키지를 설치합니다. 시간이 걸립니다...
if exist "%HERE%requirements.txt" (
    %PY% -m pip install %PIPOPT% -r "%HERE%requirements.txt"
) else (
    %PY% -m pip install %PIPOPT% opencv-python numpy matplotlib pillow mediapipe vosk sounddevice
)
echo.
echo      확인합니다...
%PY% -c "import cv2, numpy, matplotlib, PIL; print('     opencv', cv2.__version__, '/ numpy', numpy.__version__)"
%PY% -c "import mediapipe, vosk, sounddevice; print('     mediapipe', mediapipe.__version__, '/ vosk, sounddevice 준비됨')"
echo.
echo      참고 - 음성 인식 모델과 손동작 모델 파일은 따로 받아야 합니다.
echo.

rem ============================================================
rem  (질문) PATH 등록
rem ============================================================
:ASK_PATH
if defined AUTO goto DONE
echo ------------------------------------------------------------
echo  터미널에서 python 과 pip 명령을 바로 쓰고 싶으면
echo  PATH 에 파이썬 폴더를 등록할 수 있습니다.
echo  관리자 권한은 필요하지 않고, 새로 연 창부터 적용됩니다.
echo ------------------------------------------------------------
set "ANS=N"
set /p ANS="  등록할까요? (Y/N) : "
if /i not "%ANS%"=="Y" goto DONE

powershell -NoProfile -Command "$d='%PYDIR%'; $s=Join-Path $d 'Scripts'; $old=[Environment]::GetEnvironmentVariable('Path','User'); $keep=@(); if($old){$keep=$old -split ';' | Where-Object { $_ -and $_ -ne $d -and $_ -ne $s }}; $new=(@($d,$s)+$keep) -join ';'; [Environment]::SetEnvironmentVariable('Path',$new,'User'); Write-Host '      등록했습니다. 새 창부터 적용됩니다.'"
echo.

rem ============================================================
rem  마무리
rem ============================================================
:DONE
echo ============================================================
echo    준비 완료
echo.
echo    다음 할 일
echo      1. 위에서 본 COM 번호를 등록카드에 적는다
echo      2. 실행 전 팔 주변 30cm 를 비운다
echo      3. examples/01_connect_test.py 를 실행한다
echo.
echo    주의 - Raccoon 객체를 만들면 로봇이 곧바로 움직입니다.
echo ============================================================
echo.
goto END

rem ============================================================
rem  파이썬을 못 찾았을 때
rem ============================================================
:NO_PYTHON
echo.
echo      [실패] 파이썬을 찾을 수 없습니다.
echo.
echo      python.org 에서 파이썬을 설치한 뒤 다시 실행해 주세요.
echo      설치 화면 맨 아래의 Add python.exe to PATH 를 꼭 체크하세요.
echo.
if not defined AUTO start "" "https://www.python.org/downloads/"
goto END_FAIL

:END
if not defined AUTO pause
chcp %OLDCP% >nul
exit /b 0

:END_FAIL
if not defined AUTO pause
chcp %OLDCP% >nul
exit /b 1
