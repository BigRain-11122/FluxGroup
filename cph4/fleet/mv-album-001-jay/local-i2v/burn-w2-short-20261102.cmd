@echo off
rem W2 i2v 短镜批 v2（2026-11-02 07:4x 决策）。
rem 依据：连续三晚同一条 345 帧（14.1s）镜把 ComfyUI 压到假死，隔夜 0 产出。
rem 决策：先烧 <=10s 的 33 单（LJ 17 待烧 + JD 15），长镜（26 单）等主控裁定拆分或降档。
rem 产物仍是 768p int8，与既有 clips-local-768 同规格，不混档。
cd /d K:\Fluxgroup\FluxGroup
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
if not exist media\mv-album-001-jay\logs mkdir media\mv-album-001-jay\logs
echo [%DATE% %TIME%] W2-i2v short batch start >> media\mv-album-001-jay\logs\w2-i2v-short.log
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup --lane bmc --manifest cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-w2-lj.json --only LJ_T02,LJ_T04,LJ_T05,LJ_T06,LJ_T07,LJ_T08,LJ_T10,LJ_T11,LJ_T12,LJ_T13,LJ_T14,LJ_T15,LJ_T16,LJ_T17,LJ_T18,LJ_T19,LJ_T21,LJ_T25 >> media\mv-album-001-jay\logs\w2-i2v-short.log 2>&1
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup --lane bmc --manifest cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-w2-jd.json --only JD_T03,JD_T04,JD_T11,JD_T12,JD_T13,JD_T14,JD_T21,JD_T22,JD_T23,JD_T24,JD_T25,JD_T26,JD_T28,JD_T29,JD_T30 >> media\mv-album-001-jay\logs\w2-i2v-short.log 2>&1
echo [%DATE% %TIME%] W2-i2v short batch end rc=%ERRORLEVEL% >> media\mv-album-001-jay\logs\w2-i2v-short.log
exit /b %ERRORLEVEL%