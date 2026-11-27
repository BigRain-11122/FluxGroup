@echo off
rem W2 i2v short-shot batch v2 (2026-11-02). ASCII-ONLY on purpose:
rem a UTF-8 Chinese "rem" line was mis-split by cmd under a GBK console,
rem which produced a bogus command ('t8, ...') and a "file not found" every replay.
rem Scope: shots with src <= 10s only; long shots wait for master scheduling.
rem Output: 768p int8, same spec as clips-local-768.
cd /d K:\Fluxgroup\FluxGroup
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
if not exist media\mv-album-001-jay\logs mkdir media\mv-album-001-jay\logs
echo [%DATE% %TIME%] W2-i2v short batch start >> media\mv-album-001-jay\logs\w2-i2v-short.log
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup --lane bmc --manifest cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-w2-lj.json --only LJ_T02,LJ_T04,LJ_T05,LJ_T06,LJ_T07,LJ_T08,LJ_T10,LJ_T11,LJ_T12,LJ_T13,LJ_T14,LJ_T15,LJ_T16,LJ_T17,LJ_T18,LJ_T19,LJ_T21,LJ_T25 >> media\mv-album-001-jay\logs\w2-i2v-short.log 2>&1
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup --lane bmc --manifest cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-w2-jd.json --only JD_T03,JD_T04,JD_T11,JD_T12,JD_T13,JD_T14,JD_T21,JD_T22,JD_T23,JD_T24,JD_T25,JD_T26,JD_T28,JD_T29,JD_T30 >> media\mv-album-001-jay\logs\w2-i2v-short.log 2>&1
echo [%DATE% %TIME%] W2-i2v short batch end rc=%ERRORLEVEL% >> media\mv-album-001-jay\logs\w2-i2v-short.log
exit /b %ERRORLEVEL%
