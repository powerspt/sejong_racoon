@echo off
rem ============================================================
rem  라쿤봇 손동작 설치 도우미 (주제 8)
rem
rem  하는 일 : 파이썬을 찾아 mediapipe 와 opencv 를 설치하고,
rem            손 인식 모델(.task)을 vision\models 에 받아 둔다.
rem
rem  쓰는 법 : 더블클릭
rem            손동작_설치_도우미.bat /auto   물어보지 않고 설치만
rem
rem  인코딩 규칙 : 인코딩 CP949, 줄바꿈 CRLF. UTF-8 로 저장하면 한글이 깨진다.
rem  고칠 때   : 괄호 블록 안의 echo 에는 따옴표 와 괄호를 쓰지 않는다.
rem              설치는 항상 %PY% -m pip 형태로 쓴다 (pip 명령이 PATH 에 없을 수 있다).
rem ============================================================

set "HERE=%~dp0"
set "VISION=%HERE%..\vision"
for /f "tokens=2 delims=:." %%a in ('chcp') do set "OLDCP=%%a"
chcp 949 >nul
title 라쿤봇 손동작 설치 도우미

set "AUTO="
if /i "%~1"=="/auto" set "AUTO=1"

echo.
echo ============================================================
echo    라쿤봇 손동작 설치 도우미  (주제 8)
echo    mediapipe + opencv + 손 인식 모델
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

rem (2) PATH 의 python - 마이크로소프트 스토어 가짜가 여기서 걸러진다
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

%PY% -c "import sys; print('     ', sys.version.split()[0], '-', sys.executable)"
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
rem 교사 PC 에서 미리 받는 명령 :
rem   python -m pip download mediapipe opencv-python numpy pillow -d 설치파일
set "PIPOPT="
if exist "%HERE%설치파일\" (
    echo      설치파일 폴더를 찾았습니다 - 인터넷을 쓰지 않습니다
    set PIPOPT=--no-index --find-links "%HERE%설치파일"
    echo.
)

rem ============================================================
rem  [3/5] mediapipe 설치
rem ============================================================
echo [3/5] mediapipe 와 opencv 를 설치합니다. 용량이 커서 몇 분 걸립니다...
%PY% -c "import mediapipe" >nul 2>&1
if errorlevel 1 (
    %PY% -m pip install %PIPOPT% mediapipe opencv-python numpy pillow
) else (
    echo      이미 설치되어 있습니다
)
echo.

rem ============================================================
rem  [4/5] 설치 확인
rem ============================================================
echo [4/5] 설치를 확인합니다...
%PY% -c "import mediapipe, cv2; print('     mediapipe', mediapipe.__version__, '/ opencv', cv2.__version__)"
if errorlevel 1 (
    echo      [실패] mediapipe 를 불러올 수 없습니다.
    echo      인터넷 연결을 확인하고 다시 실행해 주세요.
    echo      학교망이 막혀 있으면 교사용 설치파일 폴더를 옆에 두고 다시 실행하세요.
    goto END_FAIL
)
%PY% -c "import mediapipe as mp; print('     Tasks API', 'OK' if hasattr(mp,'tasks') else '없음')"
echo.
echo      참고 - mediapipe 1.0 부터 mp.solutions 가 없습니다.
echo             인터넷 예제 대부분이 그대로는 동작하지 않습니다 (Tasks API 를 씁니다).
echo.

rem ============================================================
rem  [5/5] 손 인식 모델 받기
rem ============================================================
echo [5/5] 손 인식 모델을 확인합니다 (약 8MB, 처음 한 번만)...
if exist "%HERE%설치파일\gesture_recognizer.task" (
    if not exist "%VISION%\models\" mkdir "%VISION%\models"
    copy /y "%HERE%설치파일\gesture_recognizer.task" "%VISION%\models\" >nul
    echo      설치파일 폴더에서 복사했습니다
) else (
    %PY% -c "import sys; sys.path.insert(0, r'%VISION%'); import hand_tracker; print('     ', hand_tracker.ensure_model())"
)
if errorlevel 1 (
    echo      [실패] 모델을 받지 못했습니다.
    echo      다른 PC 에서 아래 주소의 파일을 받아
    echo      %VISION%\models\gesture_recognizer.task 로 복사해 주세요.
    echo      https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
    goto END_FAIL
)
echo.

rem ============================================================
rem  (질문) 카메라 확인
rem ============================================================
if defined AUTO goto DONE
echo ------------------------------------------------------------
echo  연결된 카메라 목록을 확인할까요?
echo  카메라를 잠깐 켜서 번호만 읽고 바로 끕니다. 저장하지 않습니다.
echo ------------------------------------------------------------
set "ANS=N"
set /p ANS="  확인할까요? (Y/N) : "
if /i not "%ANS%"=="Y" goto DONE
echo.
%PY% -c "import sys; sys.path.insert(0, r'%VISION%'); import camera_test as c; L=c.list_cameras(); [print('        ', i, '->', w, 'x', h) for i, w, h in L] or print('        (없음)')"
echo.
echo      손을 비출 카메라 번호를 기억해 두세요.
echo      노트북 내장 웹캠은 보통 0 번입니다.
echo.

rem ============================================================
rem  마무리
rem ============================================================
:DONE
echo ============================================================
echo    준비 완료
echo.
echo    바로 해 보기
echo      python vision\hand_ar.py        AR 손놀이 (로봇 없이)
echo      python vision\hand_test.py      손에 점 21개 붙이기
echo.
echo    로봇까지 연결하려면
echo      python vision\gesture_control.py --dry-run    가상 로봇으로 먼저
echo      python vision\gesture_control.py              실기
echo.
echo    주의 - 실기에서는 로봇이 사람 손 쪽으로 움직입니다.
echo           팔 주변 30cm 를 비우고, 손바닥을 들면 즉시 정지합니다.
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

:END_FAIL
echo.
echo      해결되지 않으면 선생님께 이 화면을 그대로 보여 주세요.
echo.

:END
chcp %OLDCP% >nul
if not defined AUTO pause
