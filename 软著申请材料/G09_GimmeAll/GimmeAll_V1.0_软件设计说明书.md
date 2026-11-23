# 吸嘟嘟游戏软件 V1.0 软件设计说明书

## 1 概述

吸嘟嘟游戏软件（版本 V1.0）为竖屏休闲游戏客户端，基于团结引擎与 C# 开发。
本说明书说明 448 个 C# 源文件的命名空间划分、类型结构与公开接口，用于描述本软件的设计与实现。

## 2 运行环境

| 项 | 要求 |
|---|---|
| 引擎 | 团结 2022.3 LTS |
| 语言 | C# |
| 目标平台 | Android / Windows |
| 屏幕 | 竖屏 1080×1920 |

## 3 系统架构

| 命名空间 | 文件数 |
|---|---:|
| GimmeAll.Tests | 124 |
| GimmeAll.UI | 74 |
| GimmeAll.Game | 58 |
| GimmeAll.Gameplay | 58 |
| GimmeAll.Core | 42 |
| GimmeAll.Levels | 37 |
| GimmeAll.Replay | 10 |
| GimmeAll.Audio | 8 |
| GimmeAll.Levels.Stations | 8 |
| GimmeAll.Social | 8 |
| GimmeAll.Ads | 7 |
| GimmeAll.Game.Editor | 6 |
| GimmeAll.PlayGate | 3 |
| GimmeAll.Car | 2 |
| GimmeAll.Levels.Editor | 2 |
| GimmeAll.EditorTools | 1 |

## 4 模块说明

### 4.1 mm-committed.cs

- 路径：`.codely-cli/mod/mm-committed.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| SetDuduPose |
| Show |
| Hide |

### 4.2 MOD-12-orig-MetaStore.cs

- 路径：`.codely-cli/mod/MOD-12-orig-MetaStore.cs`
- 命名空间：`GimmeAll.Game`
- 类型：MetaStore

| 公开方法 |
|---|
| StageOf |
| AddSand |
| TrySpendSand |
| ItemCount |
| GrantItem |
| TryConsume |
| ChapterClearedOnce |
| MarkChapterCleared |
| SetDailyDay |
| SetDailyTaskBits |
| LevelClearedOnce |
| MarkLevelCleared |
| LevelClearBits |
| ChestClaimedOnce |
| MarkChestClaimed |
| CodexFullHouseOnce |
| MarkCodexFullHouse |
| CompanionLevel |
| SetCompanionLevel |
| CompanionSeat |
| SetCompanionSeat |
| WipeTestKeysForCurrentPrefix |
| UsePrefsKeyForTests |
| Flush |
| StageOf |
| AddSand |
| TrySpendSand |
| ItemCount |
| GrantItem |
| TryConsume |
| ChapterClearedOnce |
| MarkChapterCleared |
| SetDailyDay |
| SetDailyTaskBits |
| LevelClearedOnce |
| MarkLevelCleared |
| LevelClearBits |
| ChestClaimedOnce |
| MarkChestClaimed |
| CodexFullHouseOnce |

### 4.3 AdConfig.cs

- 路径：`Assets/_Project/Ads/AdConfig.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：AdConfig

| 公开方法 |
|---|
| IsRewardedPlacement |
| IndexOfRewardedPlacement |

### 4.4 AdsSelfTest.cs

- 路径：`Assets/_Project/Ads/AdsSelfTest.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：AdsSelfTest

### 4.5 RewardCatalog.cs

- 路径：`Assets/_Project/Ads/RewardCatalog.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：RewardCatalog

| 公开方法 |
|---|
| GetIntent |

### 4.6 StubAdRunner.cs

- 路径：`Assets/_Project/Ads/StubAdRunner.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：StubAdRunner

| 公开方法 |
|---|
| RunRewarded |
| RunInterstitial |

### 4.7 StubAdService.cs

- 路径：`Assets/_Project/Ads/StubAdService.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：StubAdService

| 公开方法 |
|---|
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |

### 4.8 WeChatAdBootstrap.cs

- 路径：`Assets/_Project/Ads/WeChatAdBootstrap.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：WeChatAdBootstrap

### 4.9 WeChatAdService.cs

- 路径：`Assets/_Project/Ads/WeChatAdService.cs`
- 命名空间：`GimmeAll.Ads`
- 类型：WeChatAdService、AdUnitIds、AdUnitConfig

| 公开方法 |
|---|
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |

### 4.10 AudioSelfTest.cs

- 路径：`Assets/_Project/Audio/AudioSelfTest.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：AudioSelfTest、AudioSelfTestRunner

### 4.11 BgmBus.cs

- 路径：`Assets/_Project/Audio/BgmBus.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：BgmBus、DuckTicker

| 公开方法 |
|---|
| ClipNameForLevelId |
| Bind |
| Init |
| SwitchTo |
| EnsurePlaying |
| Duck |

### 4.12 SfxBus.cs

- 路径：`Assets/_Project/Audio/SfxBus.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：SfxKind、SfxBus

| 公开方法 |
|---|
| Init |
| Play |
| Play |
| StopAll |
| CaptureWindowFor |
| Reset |

### 4.13 SfxFlow.cs

- 路径：`Assets/_Project/Audio/SfxFlow.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：SfxFlow

| 公开方法 |
|---|
| Bind |
| Reset |
| PlayEnterSting |
| PlayWinSting |
| PlayFailSting |
| StingLoadStatus |
| PlayStarRelease |
| PlayCry |

### 4.14 SfxSynth.Base.cs

- 路径：`Assets/_Project/Audio/SfxSynth.Base.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：（无声明）

### 4.15 SfxSynth.cs

- 路径：`Assets/_Project/Audio/SfxSynth.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：（无声明）

### 4.16 SfxSynth.Families.cs

- 路径：`Assets/_Project/Audio/SfxSynth.Families.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：（无声明）

### 4.17 SfxSynth.Signature.cs

- 路径：`Assets/_Project/Audio/SfxSynth.Signature.cs`
- 命名空间：`GimmeAll.Audio`
- 类型：（无声明）

### 4.18 CarCabinBridge.cs

- 路径：`Assets/_Project/Car/CarCabinBridge.cs`
- 命名空间：`GimmeAll.Car`
- 类型：CarCabinBridge、Keeper

| 公开方法 |
|---|
| RegisterOem |
| EnsureInstalled |
| TrySetAmbientLight |
| TryPlayAmbientScene |
| TryVibrateSeat |
| TrySetFragrance |
| TryDistributeToScreen |
| TrySpeak |
| StopSpeaking |
| RestoreCabin |
| Bind |

### 4.19 CarCabinMock.cs

- 路径：`Assets/_Project/Car/CarCabinMock.cs`
- 命名空间：`GimmeAll.Car`
- 类型：CarCabinMock、Drawer

| 公开方法 |
|---|
| SetChargingSoc |
| SetChargingPowerKw |
| TriggerChargingCompleted |
| SetOdometerKm |
| SetSeatbelt |
| SetAllSeatbelts |
| SetParkingGear |
| SetSteeringAngle |
| PressSteeringKey |
| IsChannelSupported |
| IsSeatbeltBuckled |
| SetAmbientLight |
| PlayAmbientScene |
| RestoreAmbientLight |
| VibrateSeat |
| SetFragrance |
| Speak |
| StopSpeaking |
| DistributeToScreen |

### 4.20 AdCopy.cs

- 路径：`Assets/_Project/Core/AdCopy.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdCopy

| 公开方法 |
|---|
| DoubleReward |
| Revive |
| Supply |
| Trial |
| CodexAccel |
| SeatUnlock |
| OfflineDouble |
| Vault |
| ShopSand |

### 4.21 AdFrequencyGate.cs

- 路径：`Assets/_Project/Core/AdFrequencyGate.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdFrequencyGate

| 公开方法 |
|---|
| CanShowInterstitial |
| RegisterInterstitialShown |
| Reset |

### 4.22 AdServiceSeam.cs

- 路径：`Assets/_Project/Core/AdServiceSeam.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdServiceSeam

| 公开方法 |
|---|
| Provide |
| Activate |
| Reset |

### 4.23 AdsPolicy.cs

- 路径：`Assets/_Project/Core/AdsPolicy.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdsPolicy

| 公开方法 |
|---|
| FaceVisibleFor |
| IsFamilyOrCarBuild |

### 4.24 CaptureBeat.cs

- 路径：`Assets/_Project/Core/CaptureBeat.cs`
- 命名空间：`GimmeAll.Core`
- 类型：CaptureBeat

| 公开方法 |
|---|
| PredictAudible |
| IsSignature |
| Reset |

### 4.25 ComboTracker.cs

- 路径：`Assets/_Project/Core/ComboTracker.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ComboTracker

| 公开方法 |
|---|
| NoteCapture |
| Reset |

### 4.26 CompanionDef.cs

- 路径：`Assets/_Project/Core/Companions/CompanionDef.cs`
- 命名空间：`GimmeAll.Core`
- 类型：CompanionDef、CompanionVersion、SkillKind、PointCaptureMode、HaltMode、StardustMode、CompanionRoster

| 公开方法 |
|---|
| ForVersion |
| ById |

### 4.27 CompanionProgress.cs

- 路径：`Assets/_Project/Core/Companions/CompanionProgress.cs`
- 命名空间：`GimmeAll.Core`
- 类型：CompanionProgress

| 公开方法 |
|---|
| UpgradeCost |
| PowerScale |
| ChargeProgress01 |
| UnlockLevelId |
| TrialPending |
| ResolveActiveWithTrial |
| Seat2Unlocked |
| Seat2OfChapter |
| ScaledRadius |
| ScaledDuration |
| ScaledSeconds |
| ScaledCaptureCount |
| ScaledHaltSec |
| ScaledStardustFlat |
| ScaledShieldCount |
| PrimarySeat |
| ResolveSeat |

### 4.28 CompanionRuntime.cs

- 路径：`Assets/_Project/Core/Companions/CompanionRuntime.cs`
- 命名空间：`GimmeAll.Core`
- 类型：CompanionRuntime

| 公开方法 |
|---|
| ResetForLevel |
| OnCapture |
| TryConsume |
| ArmShield |
| TryRechargeFill |
| ConsumeShield |

### 4.29 AdMetrics.cs

- 路径：`Assets/_Project/Core/Events/AdMetrics.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdMetrics

| 公开方法 |
|---|
| InterstitialsFor |
| RewardedsFor |
| Reset |

### 4.30 AdsEvents.cs

- 路径：`Assets/_Project/Core/Events/AdsEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：AdRewarded、InterstitialShown

### 4.31 AudioEvents.cs

- 路径：`Assets/_Project/Core/Events/AudioEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SneezeStormBurst、CodexCryRequested、PostcardComposed、DuduReactionBeat、CodexRallyRequested

### 4.32 LevelEvents.cs

- 路径：`Assets/_Project/Core/Events/LevelEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：LevelStarted、BinInfo、LevelCompleted、LevelFailed、FamilyFreeContinueUsed、FamilySoftTimeout、TimeRunningLow、ObjectCaptured、ObjectEscaped、FieldPressed、FieldReleased、SuctionPowerChanged、CarryMouthChanged、BinSettled、EmotionValueGained、Front3FinaleTriggered、WaveAdvanced、MidEventTriggered、MidEventCatalog、LandmarkPolished、ChapterFinaleStarted、AmbushRevealed、SweepBeatStruck、SystemUnlockChanged、EvolveMomentTriggered、InLevelChoiceCatalog、InLevelChoiceOffered、InLevelChoicePickRequested、InLevelChoiceResolved、ComboChoiceCatalog、ComboChoiceOffered、ComboChoicePickRequested、ComboChoiceResolved、PreLevelChoiceCatalog、PreLevelChoiceOffered、PreLevelChoicePickRequested、PreLevelChoiceResolved、ParentKeyKind、ParentKeyKeys、ParentKeyPullCurve、ParentKeyClockHold、ParentKeyRequested、ParentKeyResolved

| 公开方法 |
|---|
| Envelope01 |
| Falloff01 |
| StrengthAt |

### 4.33 MetaEvents.cs

- 路径：`Assets/_Project/Core/Events/MetaEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：MetaItem、StardustChanged、ItemStockChanged、ItemUsedRequested、OutfitEquipped、CompanionChargeChanged、CompanionSkillRequested、CompanionUpgraded、CompanionSeatChanged、CompanionSeatRequested、CompanionUpgradeRequested、CompanionRosterSnapshotRequested、CompanionRosterSnapshot、CompanionTrialRequested、CompanionTrialArmed、CompanionRechargeRequested、CompanionSeatUnlockRequested、CompanionSeat2Unlocked、CompanionSeat2PurchaseRequested、DailyTaskCatalog、DailyTasksChanged、ItemEffectApplied、DailyTaskClaimRequested、DailyTaskSnapshotRequested、CheckInCatalog、CheckInChanged、CheckInClaimRequested、CheckInSnapshotRequested、ChapterChestCatalog、ChapterChestChanged、ChapterChestClaimRequested、ChapterChestSnapshotRequested、CodexFullHouseChanged、CodexFullHouseSnapshotRequested、CodexHouseCatalog、LevelSupplyCatalog、LevelSupplyChanged、LevelSupplySnapshotRequested、CodexAccelCatalog、CodexAccelChanged、CodexAccelSnapshotRequested、OfflineEarningsCatalog、OfflineEarningsChanged、OfflineEarningsClaimRequested、OfflineEarningsSnapshotRequested、StorePurchaseRequested、StorePurchaseSettled、StorePurchaseRejected、StoreDealCatalog

| 公开方法 |
|---|
| RewardFor |
| ChestItemOf |
| SupplyItemOf |
| AccelItemOf |
| PriceOf |
| ItemOf |

### 4.34 ProfileEvents.cs

- 路径：`Assets/_Project/Core/Events/ProfileEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ProfileSwitched

### 4.35 UIEvents.cs

- 路径：`Assets/_Project/Core/Events/UIEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SneezeChargeChanged、SneezeRequested、DailyFocusResolved、ShareLandingResolved、UiPressed

### 4.36 GameEventBus.cs

- 路径：`Assets/_Project/Core/GameEventBus.cs`
- 命名空间：`GimmeAll.Core`
- 类型：GameEventBus

| 公开方法 |
|---|
| ClearAll |

### 4.37 GameEvents.cs

- 路径：`Assets/_Project/Core/GameEvents.cs`
- 命名空间：`GimmeAll.Core`
- 类型：GameStateChanged

### 4.38 GameStateMachine.cs

- 路径：`Assets/_Project/Core/GameStateMachine.cs`
- 命名空间：`GimmeAll.Core`
- 类型：GameState、GameStateMachine

| 公开方法 |
|---|
| Set |
| ResetToBoot |

### 4.39 IAnalyticsService.cs

- 路径：`Assets/_Project/Core/IAnalyticsService.cs`
- 命名空间：`GimmeAll.Core`
- 类型：IAnalyticsService

### 4.40 ICanvasBoard.cs

- 路径：`Assets/_Project/Core/ICanvasBoard.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ICanvasBoard

### 4.41 ICarCabinSignalSource.cs

- 路径：`Assets/_Project/Core/ICarCabinSignalSource.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ICarCabinSignalSource、CarCabinChannel、CabinLightScene、SeatVibrationLevel、CabinFragrance、SteeringWheelKey、CabinScreen

### 4.42 IMetaService.cs

- 路径：`Assets/_Project/Core/IMetaService.cs`
- 命名空间：`GimmeAll.Core`
- 类型：IMetaService、MetaServices

### 4.43 InterstitialPolicy.cs

- 路径：`Assets/_Project/Core/InterstitialPolicy.cs`
- 命名空间：`GimmeAll.Core`
- 类型：InterstitialPolicy

### 4.44 IRecordable.cs

- 路径：`Assets/_Project/Core/IRecordable.cs`
- 命名空间：`GimmeAll.Core`
- 类型：RecordSnapshot、IRecordable

### 4.45 IServices.cs

- 路径：`Assets/_Project/Core/IServices.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SharePayload、LeaderboardEntry、IAdService、IShareService、ILeaderboardService、IReplayService、ITimeService、PostcardSpec、IPostcardComposer

### 4.46 ISuctionable.cs

- 路径：`Assets/_Project/Core/ISuctionable.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SuctionState、ISuctionable

### 4.47 ISuctionGuide.cs

- 路径：`Assets/_Project/Core/ISuctionGuide.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ISuctionGuideTarget、SuctionGuideField

| 公开方法 |
|---|
| Reset |

### 4.48 LevelData.cs

- 路径：`Assets/_Project/Core/LevelData.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SpawnEntry、LevelData、BinSpec、LevelJson

| 公开方法 |
|---|
| ToJson |
| FromJson |

### 4.49 ObjectPool.cs

- 路径：`Assets/_Project/Core/ObjectPool.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ObjectPool

| 公开方法 |
|---|
| Acquire |
| Release |

### 4.50 ObjectRegistry.cs

- 路径：`Assets/_Project/Core/ObjectRegistry.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ObjectRegistry

| 公开方法 |
|---|
| NextId |
| Register |
| Unregister |
| GetAt |
| CopyActive |
| Clear |

### 4.51 PlaceholderSpriteFactory.cs

- 路径：`Assets/_Project/Core/PlaceholderSpriteFactory.cs`
- 命名空间：`GimmeAll.Core`
- 类型：PlaceholderSpriteFactory

| 公开方法 |
|---|
| Ring |
| Circle |
| Square |

### 4.52 PrefsFlush.cs

- 路径：`Assets/_Project/Core/PrefsFlush.cs`
- 命名空间：`GimmeAll.Core`
- 类型：PrefsFlush、PrefsFlushPump

| 公开方法 |
|---|
| Request |
| FlushNow |

### 4.53 ProfileClaim.cs

- 路径：`Assets/_Project/Core/ProfileClaim.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ClaimOutcome、ProfileClaim

| 公开方法 |
|---|
| ClaimGuest |
| RecoverPending |

### 4.54 ProfileDelete.cs

- 路径：`Assets/_Project/Core/ProfileDelete.cs`
- 命名空间：`GimmeAll.Core`
- 类型：DeleteOutcome、ProfileDelete

| 公开方法 |
|---|
| IsNamedSlot |
| IsOccupied |
| SlotName |
| CountNamed |
| FindEmptySlot |
| DeleteProfile |

### 4.55 ProfileReloadContract.cs

- 路径：`Assets/_Project/Core/ProfileReloadContract.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ProfileReloadContract

| 公开方法 |
|---|
| Reset |

### 4.56 ProfileRosterContract.cs

- 路径：`Assets/_Project/Core/ProfileRosterContract.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ProfileRosterContract

| 公开方法 |
|---|
| IntKeys |
| StringKeys |
| Reset |

### 4.57 ProfileScope.cs

- 路径：`Assets/_Project/Core/ProfileScope.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ProfileScope

| 公开方法 |
|---|
| IsValidSlot |
| Key |
| KeyInSlot |
| Reload |
| UseSlotForTests |

### 4.58 ProfileSwitch.cs

- 路径：`Assets/_Project/Core/ProfileSwitch.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SwitchOutcome、ProfileSwitch

| 公开方法 |
|---|
| SwitchProfile |
| ReloadActive |

### 4.59 ServiceRegistry.cs

- 路径：`Assets/_Project/Core/ServiceRegistry.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ServiceRegistry

| 公开方法 |
|---|
| Clear |

### 4.60 SpawnRegistry.cs

- 路径：`Assets/_Project/Core/SpawnRegistry.cs`
- 命名空间：`GimmeAll.Core`
- 类型：ISpawnFactory、SpawnRegistry

| 公开方法 |
|---|
| Register |
| IsRegistered |
| TryCreate |
| Clear |

### 4.61 SystemUnlockGate.cs

- 路径：`Assets/_Project/Core/SystemUnlockGate.cs`
- 命名空间：`GimmeAll.Core`
- 类型：SystemUnlockGate

| 公开方法 |
|---|
| IsChallengeLevel |
| RebindForProfile |
| IsUnlocked |
| MarkUnlocked |
| UsePrefsKeyForTests |
| WipeForCurrentTestPrefix |

### 4.62 BuildAndroid.cs

- 路径：`Assets/_Project/Editor/BuildAndroid.cs`
- 命名空间：`GimmeAll.EditorTools`
- 类型：BuildAndroid、SpritePpuEnforcer、LockEntry、LockFile

| 公开方法 |
|---|
| Probe |
| BuildWindows |
| Build |

### 4.63 AmbientLoopLayer.cs

- 路径：`Assets/_Project/Game/AmbientLoopLayer.cs`
- 命名空间：`GimmeAll.Game`
- 类型：AmbientLoopLayer、ChapterAmbient

### 4.64 AutoPilotMenuStart.cs

- 路径：`Assets/_Project/Game/AutoPilotMenuStart.cs`
- 命名空间：`GimmeAll.Game`
- 类型：AutoPilotMenuStart

### 4.65 AutoPilotStationAdvance.cs

- 路径：`Assets/_Project/Game/AutoPilotStationAdvance.cs`
- 命名空间：`GimmeAll.Game`
- 类型：AutoPilotStationAdvance

### 4.66 BackdropBoard.cs

- 路径：`Assets/_Project/Game/BackdropBoard.cs`
- 命名空间：`GimmeAll.Game`
- 类型：BackdropBoard

| 公开方法 |
|---|
| Show |
| ShowLarge |

### 4.67 Bootstrap.cs

- 路径：`Assets/_Project/Game/Bootstrap.cs`
- 命名空间：`GimmeAll.Game`
- 类型：Bootstrap

### 4.68 CameraRig.cs

- 路径：`Assets/_Project/Game/CameraRig.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CameraRig

| 公开方法 |
|---|
| AddShake |
| DecayAmp |

### 4.69 CarAppLifecycle.cs

- 路径：`Assets/_Project/Game/CarAppLifecycle.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CarAppLifecycle

### 4.70 ChapterArt.cs

- 路径：`Assets/_Project/Game/ChapterArt.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ChapterArt

| 公开方法 |
|---|
| ChapterOf |
| HasLargeScene |
| Scene |
| For |

### 4.71 ChapterChestFlow.cs

- 路径：`Assets/_Project/Game/ChapterChestFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ChapterChestFlow

| 公开方法 |
|---|
| ChapterOf |
| LevelsDoneOf |
| FocusChapter |
| TryClaimChest |

### 4.72 CheckInFlow.cs

- 路径：`Assets/_Project/Game/CheckInFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CheckInFlow

| 公开方法 |
|---|
| TryCheckIn |
| SetNowUnixForTests |

### 4.73 CodexAccelFlow.cs

- 路径：`Assets/_Project/Game/CodexAccelFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CodexAccelFlow

| 公开方法 |
|---|
| MissingCount |
| PublishSnapshot |

### 4.74 CodexFlow.cs

- 路径：`Assets/_Project/Game/CodexFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CodexFlow

| 公开方法 |
|---|
| FullHouseReached |
| TryClaimFullHouse |

### 4.75 ComboChoiceFlow.cs

- 路径：`Assets/_Project/Game/ComboChoiceFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ComboChoiceFlow

| 公开方法 |
|---|
| HandleLevelStarted |
| HandleObjectCaptured |
| HandleObjectCaptured |
| HandlePickRequested |
| HandleLevelCompleted |
| HandleLevelFailed |
| ResetForTests |

### 4.76 CompanionAdFlow.cs

- 路径：`Assets/_Project/Game/CompanionAdFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CompanionAdFlow

| 公开方法 |
|---|
| TryArmTrial |
| TryUnlockSeat2Timed |

### 4.77 CompanionCoordinator.cs

- 路径：`Assets/_Project/Game/CompanionCoordinator.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CompanionCoordinator

| 公开方法 |
|---|
| TryRecharge |
| TryRechargeById |

### 4.78 CompanionRosterFlow.cs

- 路径：`Assets/_Project/Game/CompanionRosterFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CompanionRosterFlow

### 4.79 CompanionSeatFlow.cs

- 路径：`Assets/_Project/Game/CompanionSeatFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CompanionSeatFlow

| 公开方法 |
|---|
| TrySetSeat |
| TryUnlockSeat2Permanent |

### 4.80 CompanionUpgradeFlow.cs

- 路径：`Assets/_Project/Game/CompanionUpgradeFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：CompanionUpgradeFlow

| 公开方法 |
|---|
| TryUpgrade |

### 4.81 DailyTaskFlow.cs

- 路径：`Assets/_Project/Game/DailyTaskFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：DailyTaskFlow

| 公开方法 |
|---|
| TryClaim |
| SetNowUnixForTests |
| ClearCacheForTests |

### 4.82 DevLevelBoot.cs

- 路径：`Assets/_Project/Game/DevLevelBoot.cs`
- 命名空间：`GimmeAll.Game`
- 类型：DevLevelBoot、Runner

### 4.83 DuelRope.cs

- 路径：`Assets/_Project/Game/DuelRope.cs`
- 命名空间：`GimmeAll.Game`
- 类型：DuelTier、DuelResult、DuelRope、DuelRopeSession、DuelRopeController、DuelRopeView

| 公开方法 |
|---|
| TierAt |
| SeatOf |
| InNeutralBand |
| ModeAvailable |
| SteeringSignalAvailable |
| Step |
| Arm |
| SetWheelSource |
| Disarm |
| RestartRound |
| Attach |
| Begin |
| Refresh |
| ResetForNewRound |
| Teardown |

### 4.84 ArtImportRules.cs

- 路径：`Assets/_Project/Game/Editor/ArtImportRules.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：ArtImportRules

### 4.85 AudioPackageMatrix.cs

- 路径：`Assets/_Project/Game/Editor/AudioPackageMatrix.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：AudioPackageMatrix、Tier

| 公开方法 |
|---|
| TierOf |
| EnsurePackageOverrides |

### 4.86 NewbieRunSetup.cs

- 路径：`Assets/_Project/Game/Editor/NewbieRunSetup.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：NewbieRunSetup

| 公开方法 |
|---|
| Prepare |
| ClearOnly |

### 4.87 O1610BorderBake.cs

- 路径：`Assets/_Project/Game/Editor/O1610BorderBake.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：O1610BorderBake

| 公开方法 |
|---|
| Run |

### 4.88 ProjectBuild.cs

- 路径：`Assets/_Project/Game/Editor/ProjectBuild.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：ProjectBuild

| 公开方法 |
|---|
| BuildWin64 |
| PrepareScene |
| ProbeMiniGame2 |
| ProbeMiniGame3 |
| ProbeMiniGame5 |
| ProbeMiniGame4 |
| ProbeMiniGame6 |
| ProbeMiniGame7 |
| EnsureAudioMonoImported |
| ProbeU330AudioOverride |
| ApplyAudioPackageMatrix |
| BuildWeChatMiniGameProfile |
| ProbeMiniGame |
| BuildWeixinMiniGame |
| ForceReimportBgmLongLoops |

### 4.89 StoreAssetGen.cs

- 路径：`Assets/_Project/Game/Editor/StoreAssetGen.cs`
- 命名空间：`GimmeAll.Game.Editor`
- 类型：StoreAssetGen

| 公开方法 |
|---|
| GenerateStoreIcon |

### 4.90 FeelPulse.cs

- 路径：`Assets/_Project/Game/FeelPulse.cs`
- 命名空间：`GimmeAll.Game`
- 类型：FeelPulse

| 公开方法 |
|---|
| Bind |
| Reset |

### 4.91 FileAnalyticsService.cs

- 路径：`Assets/_Project/Game/FileAnalyticsService.cs`
- 命名空间：`GimmeAll.Game`
- 类型：FileAnalyticsService

| 公开方法 |
|---|
| Report |
| Flush |

### 4.92 HapticPulse.cs

- 路径：`Assets/_Project/Game/HapticPulse.cs`
- 命名空间：`GimmeAll.Game`
- 类型：HapticPulse

### 4.93 HapticsRelay.cs

- 路径：`Assets/_Project/Game/HapticsRelay.cs`
- 命名空间：`GimmeAll.Game`
- 类型：HapticsRelay

### 4.94 HiddenTreasureFlow.cs

- 路径：`Assets/_Project/Game/HiddenTreasureFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：HiddenTreasureFlow

| 公开方法 |
|---|
| ClearForTests |

### 4.95 InLevelChoiceFlow.cs

- 路径：`Assets/_Project/Game/InLevelChoiceFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：InLevelChoiceFlow

| 公开方法 |
|---|
| ShouldOffer |
| HandleLevelStarted |
| HandleObjectCaptured |
| HandleTimeRunningLow |
| HandlePickRequested |
| ApplyExtend |
| HandleLevelCompleted |
| HandleLevelFailed |
| ResetForTests |

### 4.96 LevelSupplyFlow.cs

- 路径：`Assets/_Project/Game/LevelSupplyFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：LevelSupplyFlow

| 公开方法 |
|---|
| PublishSnapshot |

### 4.97 MetaService.Companion.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Companion.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| CompanionLevel |
| SetCompanionLevel |
| CompanionSeat |
| SetCompanionSeat |

### 4.98 MetaService.Daily.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Daily.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| SetDailyDay |
| SetDailyTaskBits |
| LevelClearedOnce |
| MarkLevelCleared |
| LevelClearBits |
| ChestClaimedOnce |
| MarkChestClaimed |
| CodexFullHouseOnce |
| MarkCodexFullHouse |

### 4.99 MetaService.Offline.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Offline.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

### 4.100 MetaService.Profile.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Profile.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| RebindProfileKeys |

### 4.101 MetaService.Sand.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Sand.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| StageOf |
| AddSand |
| TrySpendSand |
| ItemCount |
| GrantItem |
| TryConsume |
| ChapterClearedOnce |
| MarkChapterCleared |

### 4.102 MetaService.Supply.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.Supply.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

### 4.103 MetaService.TestKeys.cs

- 路径：`Assets/_Project/Game/Meta/MetaService.TestKeys.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| WipeTestKeysForCurrentPrefix |
| UsePrefsKeyForTests |

### 4.104 MetaFlow.cs

- 路径：`Assets/_Project/Game/MetaFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：MetaFlow

### 4.105 MetaService.cs

- 路径：`Assets/_Project/Game/MetaService.cs`
- 命名空间：`GimmeAll.Game`
- 类型：（无声明）

| 公开方法 |
|---|
| Install |
| Flush |

### 4.106 MetaStore.cs

- 路径：`Assets/_Project/Game/MetaStore.cs`
- 命名空间：`GimmeAll.Game`
- 类型：MetaStore

| 公开方法 |
|---|
| DeviceKey |
| Flush |
| StageOf |
| AddSand |
| TrySpendSand |
| ItemCount |
| GrantItem |
| TryConsume |
| ChapterClearedOnce |
| MarkChapterCleared |
| SetDailyDay |
| SetDailyTaskBits |
| LevelClearedOnce |
| MarkLevelCleared |
| LevelClearBits |
| ChestClaimedOnce |
| MarkChestClaimed |
| CodexFullHouseOnce |
| MarkCodexFullHouse |
| CompanionLevel |
| SetCompanionLevel |
| CompanionSeat |
| SetCompanionSeat |
| WipeTestKeysForCurrentPrefix |
| UsePrefsKeyForTests |

### 4.107 OfflineEarningsFlow.cs

- 路径：`Assets/_Project/Game/OfflineEarningsFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：OfflineEarningsFlow

| 公开方法 |
|---|
| NowUnix |
| ComputeAtBoot |
| TryClaimBase |

### 4.108 PadLevelSwitch.cs

- 路径：`Assets/_Project/Game/PadLevelSwitch.cs`
- 命名空间：`GimmeAll.Game`
- 类型：PadLevelSwitch

### 4.109 PreLevelChoiceFlow.cs

- 路径：`Assets/_Project/Game/PreLevelChoiceFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：PreLevelChoiceFlow

| 公开方法 |
|---|
| HandleLevelStarted |
| HandlePickRequested |
| HandleLevelCompleted |
| HandleLevelFailed |
| ResetForTests |

### 4.110 ProfileReload.cs

- 路径：`Assets/_Project/Game/ProfileReload.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ProfileReload

| 公开方法 |
|---|
| InstallForTests |
| Rebind |

### 4.111 ProfileRoster.cs

- 路径：`Assets/_Project/Game/ProfileRoster.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ProfileRoster

| 公开方法 |
|---|
| InstallForTests |
| IntKeys |
| StringKeys |

### 4.112 QuitTrace.cs

- 路径：`Assets/_Project/Game/QuitTrace.cs`
- 命名空间：`GimmeAll.Game`
- 类型：QuitTrace、FocusWatch

### 4.113 RevealVeil.cs

- 路径：`Assets/_Project/Game/RevealVeil.cs`
- 命名空间：`GimmeAll.Game`
- 类型：RevealVeil

| 公开方法 |
|---|
| AlphaForLevel |
| Cover |
| Lift |

### 4.114 ScreenshotKey.cs

- 路径：`Assets/_Project/Game/ScreenshotKey.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ScreenshotKey

### 4.115 ShareLandingGate.cs

- 路径：`Assets/_Project/Game/ShareLandingGate.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ShareLandingGate、LandingQuery

| 公开方法 |
|---|
| ResolveFromLaunch |
| TryParseLevelId |

### 4.116 StationArt.cs

- 路径：`Assets/_Project/Game/StationArt.cs`
- 命名空间：`GimmeAll.Game`
- 类型：StationArt

| 公开方法 |
|---|
| IsStationLevel |
| Scene |

### 4.117 StoreAdFlow.cs

- 路径：`Assets/_Project/Game/StoreAdFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：StoreAdFlow

### 4.118 StoreFlow.cs

- 路径：`Assets/_Project/Game/StoreFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：StoreFlow

### 4.119 TelemetryRelay.cs

- 路径：`Assets/_Project/Game/TelemetryRelay.cs`
- 命名空间：`GimmeAll.Game`
- 类型：TelemetryRelay

### 4.120 UnlockFlow.cs

- 路径：`Assets/_Project/Game/UnlockFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：UnlockFlow

### 4.121 WeChatAnalyticsService.cs

- 路径：`Assets/_Project/Game/WeChatAnalyticsService.cs`
- 命名空间：`GimmeAll.Game`
- 类型：WeChatAnalyticsService

| 公开方法 |
|---|
| Report |

### 4.122 ActorDudu.cs

- 路径：`Assets/_Project/Gameplay/ActorDudu.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ActorDudu

| 公开方法 |
|---|
| Ensure |
| SetTarget |
| PlaySignatureReaction |

### 4.123 AmbushBeat.cs

- 路径：`Assets/_Project/Gameplay/AmbushBeat.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：AmbushBeat、AmbushHidden

| 公开方法 |
|---|
| EnabledFor |
| ClearForTests |
| RevealAllArmed |
| Arm |
| Reveal |

### 4.124 GameplayArt.cs

- 路径：`Assets/_Project/Gameplay/Art/GameplayArt.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GameplayArt、Slot

### 4.125 BellyWindow.cs

- 路径：`Assets/_Project/Gameplay/BellyWindow.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：BellyWindow、Chip、BellyMath、BellyTowerMath

| 公开方法 |
|---|
| Ensure |
| ApplyTowerCharge |
| FlightPos01 |
| OrbitOffset |
| Clamp01 |
| FillLocalY |
| TowerCenterY |
| ReadyPulseScale |

### 4.126 BinZone.cs

- 路径：`Assets/_Project/Gameplay/BinZone.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：BinZone

| 公开方法 |
|---|
| Ensure |
| Hit |
| TypeKeyOf |

### 4.127 CaptureBurst.cs

- 路径：`Assets/_Project/Gameplay/CaptureBurst.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：CaptureBurst、Particle

| 公开方法 |
|---|
| Spawn |
| Spawn |
| Spawn |
| ParticlesFor |
| Prewarm |

### 4.128 CarryMouth.cs

- 路径：`Assets/_Project/Gameplay/CarryMouth.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：CarryMouth、Piece、Batch

| 公开方法 |
|---|
| Ensure |
| TryIntercept |

### 4.129 ChapterEvolveFlow.cs

- 路径：`Assets/_Project/Gameplay/ChapterEvolveFlow.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ChapterEvolveFlow

| 公开方法 |
|---|
| ChapterFor |
| IsChapterFirstLevel |
| EvolveNameFor |
| RotationSlotOf |
| ChapterMaterialFor |
| SneezeRadiusFactorFor |
| SweepBeatWindowFor |
| HeavyCaptureMulFor |
| SparkleGrantFor |
| LickUnlockedFor |
| HandleLevelStarted |
| ResetForTests |

### 4.130 ChapterFinale.cs

- 路径：`Assets/_Project/Gameplay/ChapterFinale.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ChapterFinale、FinaleSequence

| 公开方法 |
|---|
| BossKeyFor |
| ClearForTests |
| Step |

### 4.131 ChapterOnlooker.cs

- 路径：`Assets/_Project/Gameplay/ChapterOnlooker.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ChapterOnlooker、EmotionFrame、EmoteBadge、BaseMood

| 公开方法 |
|---|
| ChapterOfLevel |
| Cheer |

### 4.132 ChapterOnlookerSelfTest.cs

- 路径：`Assets/_Project/Gameplay/ChapterOnlookerSelfTest.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ChapterOnlookerSelfTest

### 4.133 ClusterMilestone.cs

- 路径：`Assets/_Project/Gameplay/ClusterMilestone.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ClusterMilestone

| 公开方法 |
|---|
| Ensure |
| BuildClusters |

### 4.134 DebrisTarget.cs

- 路径：`Assets/_Project/Gameplay/DebrisTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：DebrisTarget

### 4.135 DustTarget.cs

- 路径：`Assets/_Project/Gameplay/DustTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：DustTarget

### 4.136 EscapeBrake.cs

- 路径：`Assets/_Project/Gameplay/EscapeBrake.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：EscapeBrake

| 公开方法 |
|---|
| Note |
| CountOf |

### 4.137 BubbleTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/BubbleTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：BubbleTarget

### 4.138 GhostTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/GhostTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GhostTarget

| 公开方法 |
|---|
| HiddenAt |

### 4.139 HeavyTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/HeavyTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：HeavyTarget

### 4.140 MimicTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/MimicTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：MimicTarget

| 公开方法 |
|---|
| Setup |

### 4.141 PlayBand.cs

- 路径：`Assets/_Project/Gameplay/Families/PlayBand.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：PlayBand

### 4.142 SparkleTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/SparkleTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SparkleTarget

### 4.143 SplitterTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/SplitterTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SplitterTarget、SplitKidTarget

### 4.144 StickyTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/StickyTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：StickyTarget

| 公开方法 |
|---|
| SpringPull |

### 4.145 SwarmTarget.cs

- 路径：`Assets/_Project/Gameplay/Families/SwarmTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SwarmTarget

### 4.146 Front3Fx.cs

- 路径：`Assets/_Project/Gameplay/Front3Fx.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：Front3Fx

| 公开方法 |
|---|
| Ensure |

### 4.147 Front3SuctionGrowth.cs

- 路径：`Assets/_Project/Gameplay/Front3SuctionGrowth.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：Front3SuctionGrowth

| 公开方法 |
|---|
| Ensure |

### 4.148 FullChargeCeremony.cs

- 路径：`Assets/_Project/Gameplay/FullChargeCeremony.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：FullChargeCeremony、State、FullChargePreannouncePublished、FullChargeRungPublished

| 公开方法 |
|---|
| Ensure |

### 4.149 FurTarget.cs

- 路径：`Assets/_Project/Gameplay/FurTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：FurTarget

### 4.150 GameplayDirtPalette.cs

- 路径：`Assets/_Project/Gameplay/GameplayDirtPalette.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GameplayDirtPalette

| 公开方法 |
|---|
| TintOf |

### 4.151 GameplayEscape.cs

- 路径：`Assets/_Project/Gameplay/GameplayEscape.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GameplayEscape

| 公开方法 |
|---|
| Report |

### 4.152 GameplaySelfTest.cs

- 路径：`Assets/_Project/Gameplay/GameplaySelfTest.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GameplaySelfTest

### 4.153 GameplaySpawnFactory.cs

- 路径：`Assets/_Project/Gameplay/GameplaySpawnFactory.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GameplaySpawnFactory

| 公开方法 |
|---|
| Create |

### 4.154 GrayscaleDriver.cs

- 路径：`Assets/_Project/Gameplay/GrayscaleDriver.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GrayscaleDriver

| 公开方法 |
|---|
| Ensure |
| SetGrey01 |

### 4.155 GroundShadow.cs

- 路径：`Assets/_Project/Gameplay/GroundShadow.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GroundShadow

| 公开方法 |
|---|
| Attach |

### 4.156 GuideRing.cs

- 路径：`Assets/_Project/Gameplay/GuideRing.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：GuideRing

| 公开方法 |
|---|
| Attach |

### 4.157 HitStop.cs

- 路径：`Assets/_Project/Gameplay/HitStop.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：HitStop、HitStopDriver

| 公开方法 |
|---|
| DurationFor |
| RequestCaptureStop |
| Request |
| Step |
| Reset |
| SetDeadlineForTests |

### 4.158 JuiceCurves.cs

- 路径：`Assets/_Project/Gameplay/JuiceCurves.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：JuiceCurves

| 公开方法 |
|---|
| SpawnPop01 |
| CapturePop01 |
| InflateFor |
| Breath |
| StretchOf |
| GulpRebound |

### 4.159 LandmarkBeacon.cs

- 路径：`Assets/_Project/Gameplay/LandmarkBeacon.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：LandmarkBeacon

| 公开方法 |
|---|
| Polish |
| Beckon |

### 4.160 LevelScope.cs

- 路径：`Assets/_Project/Gameplay/LevelScope.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：LevelScope

| 公开方法 |
|---|
| SetForTests |

### 4.161 PadInput.cs

- 路径：`Assets/_Project/Gameplay/PadInput.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：PadInput

| 公开方法 |
|---|
| Held |
| Down |

### 4.162 PointVacuum.cs

- 路径：`Assets/_Project/Gameplay/PointVacuum.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：PointVacuum

| 公开方法 |
|---|
| CaptureNearest |

### 4.163 ScratchTargets.cs

- 路径：`Assets/_Project/Gameplay/ScratchTargets.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ScratchTarget

| 公开方法 |
|---|
| SetupKey |
| ApplyBeatAt |
| TickDecay |

### 4.164 ScriptedPointer.cs

- 路径：`Assets/_Project/Gameplay/ScriptedPointer.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ScriptedPointer

| 公开方法 |
|---|
| Drive |
| Release |
| TryRead |

### 4.165 ScriptedSuctionPilot.cs

- 路径：`Assets/_Project/Gameplay/ScriptedSuctionPilot.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：ScriptedSuctionPilot、ProbeNote

### 4.166 SignatureArt.cs

- 路径：`Assets/_Project/Gameplay/SignatureArt.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SignatureArt

| 公开方法 |
|---|
| SpriteOf |

### 4.167 SignatureTargets.cs

- 路径：`Assets/_Project/Gameplay/SignatureTargets.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SockTarget、FurBallTarget、SnakeTarget、CoinTarget、FuzzHillTarget、FuzzPiece、FuzzFade

### 4.168 SneezeSystem.cs

- 路径：`Assets/_Project/Gameplay/SneezeSystem.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SneezeSystem

| 公开方法 |
|---|
| NeededFor |
| Ensure |
| AddCharge |
| ResetCharge |
| FillCharge |

### 4.169 SpawnSpecTable.cs

- 路径：`Assets/_Project/Gameplay/SpawnSpecTable.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SpawnKind、SpawnSpec、SpawnSpecTable

| 公开方法 |
|---|
| Attach |

### 4.170 SuctionField.cs

- 路径：`Assets/_Project/Gameplay/SuctionField.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionField

| 公开方法 |
|---|
| SetLockUpgradeEnabled |
| BoostRadius |
| SetActiveRadius |
| SetStrengthMult |
| SweepBeatReached |
| TickLickDwell |

### 4.171 SuctionField.Visual.cs

- 路径：`Assets/_Project/Gameplay/SuctionField.Visual.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionField

### 4.172 SuctionFieldConfig.cs

- 路径：`Assets/_Project/Gameplay/SuctionFieldConfig.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionFieldConfig

### 4.173 SuctionGuideWiring.cs

- 路径：`Assets/_Project/Gameplay/SuctionGuideWiring.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionGuideWiring

### 4.174 SuctionTarget.cs

- 路径：`Assets/_Project/Gameplay/SuctionTarget.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionTarget

| 公开方法 |
|---|
| BeginEscape |
| SetVertical |
| ApplySuction |
| ApplyBurst |
| ApplyPull |
| AttachGuideHalo |
| Halt |
| HaltAll |
| HaltEscaping |
| OnCaptured |
| WriteSnapshot |

### 4.175 SuctionTrail.cs

- 路径：`Assets/_Project/Gameplay/SuctionTrail.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionTrail、Dot、TrailHost

| 公开方法 |
|---|
| Emit |

### 4.176 CampaignCatalog.Ch07.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch07.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.177 CampaignCatalog.Ch08.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch08.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.178 CampaignCatalog.Ch09.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch09.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.179 CampaignCatalog.Ch10.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch10.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.180 CampaignCatalog.Ch11.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch11.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.181 CampaignCatalog.Ch12.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch12.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.182 CampaignCatalog.Ch13.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch13.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.183 CampaignCatalog.Ch14.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch14.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.184 CampaignCatalog.Ch15.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch15.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.185 CampaignCatalog.Ch16.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch16.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.186 CampaignCatalog.Ch17.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch17.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.187 CampaignCatalog.Ch18.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Ch18.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.188 CampaignCatalog.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：ClusterSpec、LevelSpec

### 4.189 CampaignCatalog.Id04_12.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Id04_12.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.190 CampaignCatalog.Id13_21.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Id13_21.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.191 CampaignCatalog.Id22_30.cs

- 路径：`Assets/_Project/Levels/Campaign/CampaignCatalog.Id22_30.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.192 ChapterLore.cs

- 路径：`Assets/_Project/Levels/ChapterLore.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：ChapterLore

| 公开方法 |
|---|
| GetChapterTitle |
| GetNextChapterName |
| GetNextChapterTitle |

### 4.193 ContentCatalog.cs

- 路径：`Assets/_Project/Levels/ContentCatalog.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：EmotionCurveRow

| 公开方法 |
|---|
| All |
| IsVarietyKey |
| IsGearKey |
| Beat5BossKey |
| IsScratchKey |
| IsStationAbKey |
| IsStationCdeKey |
| IsSpawnKey |
| CountWeightOf |
| WeightOf |
| VarietyPriceOf |
| VarietyRebateOf |
| IsSignatureKey |
| SelfCheck |
| BuildEmotionCurve |
| BuildEmotionCurve |
| ValidateEmotionCurve |
| GetTheoreticalOptimalSec |
| FamilyStation1 |
| FamilyChallenge |
| FamilyStationA |
| FamilyStationB |

### 4.194 DailyLevelPolicy.cs

- 路径：`Assets/_Project/Levels/DailyLevelPolicy.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：DailyLevelPolicy

| 公开方法 |
|---|
| ResolveDaily |

### 4.195 ContentCatalogEditor.cs

- 路径：`Assets/_Project/Levels/Editor/ContentCatalogEditor.cs`
- 命名空间：`GimmeAll.Levels.Editor`
- 类型：ContentCatalogEditor

| 公开方法 |
|---|
| Run |

### 4.196 LevelEditorWindow.cs

- 路径：`Assets/_Project/Levels/Editor/LevelEditorWindow.cs`
- 命名空间：`GimmeAll.Levels.Editor`
- 类型：LevelEditorWindow

### 4.197 BeatInjection.cs

- 路径：`Assets/_Project/Levels/Generation/BeatInjection.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.198 LevelGenerator.cs

- 路径：`Assets/_Project/Levels/Generation/LevelGenerator.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.199 SignatureInjection.cs

- 路径：`Assets/_Project/Levels/Generation/SignatureInjection.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.200 VarietyInjection.cs

- 路径：`Assets/_Project/Levels/Generation/VarietyInjection.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.201 GoalTracker.cs

- 路径：`Assets/_Project/Levels/GoalTracker.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：GoalTracker

| 公开方法 |
|---|
| StarsFor |

### 4.202 LevelCatalog.cs

- 路径：`Assets/_Project/Levels/LevelCatalog.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelCatalog

| 公开方法 |
|---|
| Get |

### 4.203 LevelDiag.cs

- 路径：`Assets/_Project/Levels/LevelDiag.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelDiag

### 4.204 LevelProgressStore.cs

- 路径：`Assets/_Project/Levels/LevelProgressStore.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelProgressStore

| 公开方法 |
|---|
| RebindForProfile |
| UsePrefsKeyForTests |
| Reset |

### 4.205 LevelRules.cs

- 路径：`Assets/_Project/Levels/LevelRules.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelRules

| 公开方法 |
|---|
| ResolveGoal |
| GoalReached |
| ShouldCountdown |
| StepCountdown |

### 4.206 LevelRunner.cs

- 路径：`Assets/_Project/Levels/LevelRunner.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelRunner

| 公开方法 |
|---|
| StartLevel |
| StopLevel |
| LevelHasSweepStains |
| SpawnWave |
| SpawnOne |

### 4.207 LevelSourceResolver.cs

- 路径：`Assets/_Project/Levels/LevelSourceResolver.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelSourceResolver

| 公开方法 |
|---|
| SourceId |
| Resolve |
| WritesCampaignProgress |

### 4.208 LevelsSelfTest.cs

- 路径：`Assets/_Project/Levels/LevelsSelfTest.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelsSelfTest

### 4.209 LevelTimer.cs

- 路径：`Assets/_Project/Levels/LevelTimer.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：LevelTimer

| 公开方法 |
|---|
| Extend |

### 4.210 ParentKeyGuide.cs

- 路径：`Assets/_Project/Levels/ParentKeyGuide.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：ParentKeyGuide、Ticker

| 公开方法 |
|---|
| ReadyFor |
| Clear |
| TryLight |
| TryPauseClock |
| TryPullTogether |
| Tick |
| ClearForTests |

### 4.211 RemainderGuide.cs

- 路径：`Assets/_Project/Levels/RemainderGuide.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：RemainderGuide

| 公开方法 |
|---|
| MarkedAt |
| Clear |
| RefreshForSpawn |
| ClearForTests |

### 4.212 StationAbLayout.cs

- 路径：`Assets/_Project/Levels/Stations/StationAbLayout.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：AbRow、AbPiece、AbSpec、StationAbLayout

### 4.213 StationCatalog_Station1.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_Station1.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_Station1、FamilySpec

| 公开方法 |
|---|
| FamilyStation1 |
| FamilyChallenge |

### 4.214 StationCatalog_StationA.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationA.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationA

| 公开方法 |
|---|
| FamilyStationA |

### 4.215 StationCatalog_StationB.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationB.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationB

| 公开方法 |
|---|
| FamilyStationB |

### 4.216 StationCatalog_StationC.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationC.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationC

| 公开方法 |
|---|
| FamilyStationC |

### 4.217 StationCatalog_StationD.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationD.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationD

| 公开方法 |
|---|
| FamilyStationD |

### 4.218 StationCatalog_StationE.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationE.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationE

| 公开方法 |
|---|
| FamilyStationE |

### 4.219 StationCatalog_StationF.cs

- 路径：`Assets/_Project/Levels/Stations/StationCatalog_StationF.cs`
- 命名空间：`GimmeAll.Levels.Stations`
- 类型：StationCatalog_StationF

| 公开方法 |
|---|
| FamilyStationF |

### 4.220 LevelReport.cs

- 路径：`Assets/_Project/Levels/Validation/LevelReport.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.221 LevelValidator.cs

- 路径：`Assets/_Project/Levels/Validation/LevelValidator.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：（无声明）

### 4.222 WaveDirector.cs

- 路径：`Assets/_Project/Levels/WaveDirector.cs`
- 命名空间：`GimmeAll.Levels`
- 类型：WaveDirector

| 公开方法 |
|---|
| KindFor |
| EnabledFor |
| PeekStaggerForTests |
| Clear |
| BeginSession |
| CountGoalPieces |
| TickStagger |
| StepStaggerForTests |
| ClearForTests |

### 4.223 GhostPlayback.cs

- 路径：`Assets/_Project/Replay/GhostPlayback.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：GhostPlayback、GhostDot

| 公开方法 |
|---|
| Bind |
| LoadClip |
| Clear |
| Play |
| Pause |
| SetSpeed |

### 4.224 PostcardComposer.cs

- 路径：`Assets/_Project/Replay/PostcardComposer.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：PostcardComposer

| 公开方法 |
|---|
| ComposePostcard |

### 4.225 PosterComposer.cs

- 路径：`Assets/_Project/Replay/PosterComposer.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：PosterComposer

| 公开方法 |
|---|
| ComposePng |

### 4.226 ReplayConfig.cs

- 路径：`Assets/_Project/Replay/ReplayConfig.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：ReplayConfig

### 4.227 ReplayRecorder.cs

- 路径：`Assets/_Project/Replay/ReplayRecorder.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：ReplayRecorder

| 公开方法 |
|---|
| StartSession |
| MarkFailMoment |
| TryBuildSharePayload |
| GetFrameTrackCount |
| GetSnapshot |
| GetFrameTime |
| PickHighlightFrameIndex |

### 4.228 ReplayRingMath.cs

- 路径：`Assets/_Project/Replay/ReplayRingMath.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：ReplayRingMath

| 公开方法 |
|---|
| ChronoOffsetOf |
| SlotOf |

### 4.229 ReplaySelfTest.cs

- 路径：`Assets/_Project/Replay/ReplaySelfTest.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：ReplaySelfTest

### 4.230 ReplayShareService.cs

- 路径：`Assets/_Project/Replay/ReplayShareService.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：ReplayShareService

| 公开方法 |
|---|
| ShareSupported |
| SharePoster |
| ShareReplay |

### 4.231 WanderDot.cs

- 路径：`Assets/_Project/Replay/WanderDot.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：WanderDot

| 公开方法 |
|---|
| SpawnAt |
| WriteSnapshot |

### 4.232 WeChatShareService.cs

- 路径：`Assets/_Project/Replay/WeChatShareService.cs`
- 命名空间：`GimmeAll.Replay`
- 类型：WeChatShareService

| 公开方法 |
|---|
| ShareSupported |
| SharePoster |
| ShareReplay |
| ShareSupported |
| SharePoster |
| ShareReplay |

### 4.233 ArenaAnchor.cs

- 路径：`Assets/_Project/Social/ArenaAnchor.cs`
- 命名空间：`GimmeAll.Social`
- 类型：ArenaAnchor

| 公开方法 |
|---|
| Open |
| ReportScore |
| Close |

### 4.234 CloudScoreParser.cs

- 路径：`Assets/_Project/Social/CloudScoreParser.cs`
- 命名空间：`GimmeAll.Social`
- 类型：CloudScoreParser、WxGameValue、WxGame

| 公开方法 |
|---|
| TryParseScore |

### 4.235 PersistentLeaderboardService.cs

- 路径：`Assets/_Project/Social/PersistentLeaderboardService.cs`
- 命名空间：`GimmeAll.Social`
- 类型：PersistentLeaderboardService

| 公开方法 |
|---|
| BestScoreKey |
| RebindKeyPrefix |
| SubmitScore |
| GetFriendScores |

### 4.236 ScoreFlow.cs

- 路径：`Assets/_Project/Social/ScoreFlow.cs`
- 命名空间：`GimmeAll.Social`
- 类型：ScoreFlow

### 4.237 SocialSelfTest.cs

- 路径：`Assets/_Project/Social/SocialSelfTest.cs`
- 命名空间：`GimmeAll.Social`
- 类型：SocialSelfTest

### 4.238 StubLeaderboardService.cs

- 路径：`Assets/_Project/Social/StubLeaderboardService.cs`
- 命名空间：`GimmeAll.Social`
- 类型：StubLeaderboardService

| 公开方法 |
|---|
| SubmitScore |
| GetFriendScores |

### 4.239 TimeService.cs

- 路径：`Assets/_Project/Social/TimeService.cs`
- 命名空间：`GimmeAll.Social`
- 类型：TimeService

| 公开方法 |
|---|
| NowUnixSeconds |

### 4.240 WeChatLeaderboardService.cs

- 路径：`Assets/_Project/Social/WeChatLeaderboardService.cs`
- 命名空间：`GimmeAll.Social`
- 类型：WeChatLeaderboardService

| 公开方法 |
|---|
| SubmitScore |
| GetFriendScores |
| ShowBoard |
| HideBoard |
| SubmitScore |
| GetFriendScores |

### 4.241 BVersionSevenShot.cs

- 路径：`Assets/_Project/Tests/Editor/BVersionSevenShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：BVersionSevenShot

| 公开方法 |
|---|
| Run |

### 4.242 ChapterTurnCapture.cs

- 路径：`Assets/_Project/Tests/Editor/ChapterTurnCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：ChapterTurnCapture

| 公开方法 |
|---|
| Run |

### 4.243 DevRigToggles.cs

- 路径：`Assets/_Project/Tests/Editor/DevRigToggles.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：DevRigToggles

### 4.244 DuduIdleShot.cs

- 路径：`Assets/_Project/Tests/Editor/DuduIdleShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：DuduIdleShot

| 公开方法 |
|---|
| Run |

### 4.245 EditModeSpawnDrive.cs

- 路径：`Assets/_Project/Tests/Editor/EditModeSpawnDrive.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：EditModeSpawnDrive

| 公开方法 |
|---|
| DriveAllSpawned |
| Drive |
| DriveAllOnDisable |

### 4.246 EntityProbeGate.cs

- 路径：`Assets/_Project/Tests/Editor/EntityProbeGate.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：EntityProbeGate

| 公开方法 |
|---|
| RunEntityProbe |

### 4.247 FxGate.cs

- 路径：`Assets/_Project/Tests/Editor/FxGate.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：FxGate

| 公开方法 |
|---|
| RunFxLoop |

### 4.248 HeadlessRunner.cs

- 路径：`Assets/_Project/Tests/Editor/HeadlessRunner.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：HeadlessRunner

| 公开方法 |
|---|
| RunAll |

### 4.249 HeadlessTestAttribute.cs

- 路径：`Assets/_Project/Tests/Editor/HeadlessTestAttribute.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：HeadlessTestAttribute

### 4.250 NewbieFlowCapture.cs

- 路径：`Assets/_Project/Tests/Editor/NewbieFlowCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：NewbieFlowCapture

| 公开方法 |
|---|
| Run |

### 4.251 O1610MenuShot.cs

- 路径：`Assets/_Project/Tests/Editor/O1610MenuShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：O1610MenuShot

| 公开方法 |
|---|
| Run |

### 4.252 PlayLoopGate.cs

- 路径：`Assets/_Project/Tests/Editor/PlayLoopGate.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：PlayLoopGate

| 公开方法 |
|---|
| RunClosedLoop |

### 4.253 SettlementCapture.cs

- 路径：`Assets/_Project/Tests/Editor/SettlementCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：SettlementCapture

| 公开方法 |
|---|
| Run |

### 4.254 SweepCapture.cs

- 路径：`Assets/_Project/Tests/Editor/SweepCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：SweepCapture、ModalPlan

| 公开方法 |
|---|
| Run |

### 4.255 TestAdCopyFamilyFace.cs

- 路径：`Assets/_Project/Tests/Editor/TestAdCopyFamilyFace.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAdCopyFamilyFace

| 公开方法 |
|---|
| Test_DefaultIsAdForm |
| Test_FamilyIsMechanicallyPlain |
| Test_OverrideRestores |

### 4.256 TestAdPolicyFaceVisible.cs

- 路径：`Assets/_Project/Tests/Editor/TestAdPolicyFaceVisible.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAdPolicyFaceVisible

| 公开方法 |
|---|
| Test_FaceVisibleTruthTable |
| Test_PropertyDelegatesToTruthTable |

### 4.257 TestAds.cs

- 路径：`Assets/_Project/Tests/Editor/TestAds.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAds、AdUnitConfigProbe

| 公开方法 |
|---|
| Test_AdConfigFrequencyConstants |
| Test_AdConfigRewardedPlacements |
| Test_RewardCatalogIntents |
| Test_AdGateResetAllowsInterstitial |
| Test_AdGateSessionCapBlocksAtThree |
| Test_AdGateCooldownBlocksIndependently |
| Test_AdGateResetRestoresAfterCap |
| Test_AdUnitConfigChannel |

### 4.258 TestAdsMetrics.cs

- 路径：`Assets/_Project/Tests/Editor/TestAdsMetrics.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAdsMetrics

| 公开方法 |
|---|
| Test_AutoBind_CountsByPlacement |
| Test_NullPlacement_CountsTotalOnly |
| Test_Reset_ZeroesTotalsAndPlacements |

### 4.259 TestArtAssets.cs

- 路径：`Assets/_Project/Tests/Editor/TestArtAssets.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestArtAssets

| 公开方法 |
|---|
| Test_ChapterOnlookerBaseFramesLoad |
| Test_ChapterOnlookerHomeExpressionFramesLoad |
| Test_ChapterOnlookerHomeSadFrameKnownGapDegrades |
| Test_ChapterOnlookerJapanExpressionFramesLoad |
| Test_ChapterOnlookerParisExpressionFramesLoad |
| Test_ChapterOnlookerEgyptExpressionFramesLoad |
| Test_ChapterOnlookerForbiddenExpressionFramesLoad |
| Test_ChapterOnlookerSpaceExpressionFramesLoad |
| Test_ChapterOnlookerEmoteBadgesLoad |
| Test_AmbientLoopBandSpritesLoad |
| Test_AmbientLoopParticleSpritesLoad |
| Test_BackgroundAnchorSpritesLoad |
| Test_TargetAnchorSpritesLoad |
| Test_EffectAnchorSpritesLoad |
| Test_SignatureSpritesDegradeAware |
| Test_DuduReactionFramesDegradeAware |
| Test_UiIconSpritesDegradeAware |
| Test_PropIconSpritesDegradeAware |
| Test_UiPadSpritesLoad |
| Test_DuduIdleFramesLoad |

### 4.260 TestAudioAssets.cs

- 路径：`Assets/_Project/Tests/Editor/TestAudioAssets.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAudioAssets

| 公开方法 |
|---|
| Test_W15AudioAssetsAllLoadable |
| Test_W19UiAndDuduClipsAllLoadable |
| Test_U320OperationsClipsAllLoadable |
| Test_BgmSeasonRouting |
| Test_CodexCryKeysComplete |

### 4.261 TestAudioPackageMatrix.cs

- 路径：`Assets/_Project/Tests/Editor/TestAudioPackageMatrix.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestAudioPackageMatrix

| 公开方法 |
|---|
| Test_U330TierClassification |
| Test_U330PackageOverridesOnDisk |
| Test_U330FullAndSfxTiersUntouched |

### 4.262 TestBellyMath.cs

- 路径：`Assets/_Project/Tests/Editor/TestBellyMath.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBellyMath

| 公开方法 |
|---|
| Test_FlightEndpointsAndLift |
| Test_FlightHorizontalApproachMonotonic |
| Test_OrbitOnCircleAndDeterministic |

### 4.263 TestBVersionChapterJourney.cs

- 路径：`Assets/_Project/Tests/Editor/TestBVersionChapterJourney.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBVersionChapterJourney

| 公开方法 |
|---|
| Test_ChapterJourneyFaceBindsLiveData |
| Test_ChapterJourneyDisplayCensusCovers |
| Test_ChapterJourneyArtAssets |

### 4.264 TestBVersionEntries.cs

- 路径：`Assets/_Project/Tests/Editor/TestBVersionEntries.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBVersionEntries

| 公开方法 |
|---|
| Test_MenuBVersionEntriesWired |

### 4.265 TestBVersionPortMap.cs

- 路径：`Assets/_Project/Tests/Editor/TestBVersionPortMap.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBVersionPortMap

| 公开方法 |
|---|
| Test_BVersionPortMapIntact |
| Test_SkeletonScreensLazyLifecycle |

### 4.266 TestBVersionStoreScreen.cs

- 路径：`Assets/_Project/Tests/Editor/TestBVersionStoreScreen.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBVersionStoreScreen

| 公开方法 |
|---|
| Test_StoreFaceBindsLiveData |
| Test_StoreDisplayCensusCovers |
| Test_StoreArtAssets |
| Test_StorePurchaseWiringAndLiveRefresh |
| Test_StoreRejectFeedback |
| Test_StoreSeat2PurchaseChain |
| Test_StoreSeat2PoorWalletGuard |

### 4.267 TestChainIntegration.cs

- 路径：`Assets/_Project/Tests/Editor/TestChainIntegration.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestChainIntegration、FakeAdService、FakeLeaderboardService、ChainEnv、ChainCounters

| 公开方法 |
|---|
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |
| SubmitScore |
| GetFriendScores |
| Test_G27Chain_StartRequest_PublishesLevelStartedAndSpawnsTargets |
| Test_G27Chain_CaptureAll_CompletesWithSingleInterstitialAndScore |
| Test_G27Chain_WithReplayRecorder_RecordsAllCaptures |

### 4.268 TestChapterChest.cs

- 路径：`Assets/_Project/Tests/Editor/TestChapterChest.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestChapterChest

| 公开方法 |
|---|
| Test_ChapterChestProgressDedupeAndClaimGuard |
| Test_ChapterChestChapterIsolationAndFocusSnapshot |
| Test_ChapterChestPersistenceAcrossRestart |

### 4.269 TestChapterChestUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestChapterChestUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestChapterChestUi

| 公开方法 |
|---|
| Test_ChapterChestUiRequestChannelAndCapsuleFaces |
| Test_ChapterChestScreenModalFlow |

### 4.270 TestChapterEvolveFlow.cs

- 路径：`Assets/_Project/Tests/Editor/TestChapterEvolveFlow.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestChapterEvolveFlow

| 公开方法 |
|---|
| Test_EvolveMomentExactlyOnChapterFirstLevels |
| Test_BuffsOnlyAddNeverReduce |
| Test_HeavyCaptureHotPathChapterMul |
| Test_SweepBeatWindowChapterSlot |
| Test_ChapterMaterialVariantTable |
| Test_EvolveComboNameIndependence |
| Test_EvolveNameBusCarriesMaterialChapters |

### 4.271 TestCheckIn.cs

- 路径：`Assets/_Project/Tests/Editor/TestCheckIn.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCheckIn

| 公开方法 |
|---|
| Test_CheckInLadderDoublingAndCap |
| Test_CheckInBreakDoesNotReset |
| Test_CheckInRequestChannelAndMenuSnapshot |

### 4.272 TestCheckInUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestCheckInUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCheckInUi

| 公开方法 |
|---|
| Test_CheckInStripStatesAndClaimChain |
| Test_CheckInStripCapFaceAcrossDays |

### 4.273 TestCodexAccel.cs

- 路径：`Assets/_Project/Tests/Editor/TestCodexAccel.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCodexAccel

| 公开方法 |
|---|
| Test_CodexAccelOneAwayGrantAndGuards |
| Test_CodexAccelRefreshAnchorsAndCrossLock |
| Test_CodexAccelPersistence |

### 4.274 TestCodexAccelUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestCodexAccelUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCodexAccelUi、AccelStubAdService

| 公开方法 |
|---|
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |
| Test_CodexAccelUiFaces |

### 4.275 TestCodexCatalog.cs

- 路径：`Assets/_Project/Tests/Editor/TestCodexCatalog.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCodexCatalog

| 公开方法 |
|---|
| Test_CodexEntriesCompleteAndNonEmpty |
| Test_CodexChapterCoverageIsExact |
| Test_CodexChapterNamesVerbatim |
| Test_CodexUnlockBoundaries |
| Test_CodexProgressLineStates |
| Test_CodexProgressLineNamesTheMissingOne |

### 4.276 TestCodexFlow.cs

- 路径：`Assets/_Project/Tests/Editor/TestCodexFlow.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCodexFlow

| 公开方法 |
|---|
| Test_CodexFlowFullHouseGrantIdempotent |
| Test_CodexFlowMenuAnchorAndRosterCrossLock |

### 4.277 TestCodexUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestCodexUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCodexUi

| 公开方法 |
|---|
| Test_CodexPreviewLineStates |
| Test_CodexScreenRevealBookkeeping |
| Test_CodexRetainMarkLitByChapterKey |
| Test_CodexRetainMarkUnlitKeepsPill |

### 4.278 TestCompanionAds.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionAds.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionAds

| 公开方法 |
|---|
| Test_PlacementCatalogTrioRegistered |
| Test_TrialArmGuardsPersistDailyCap |
| Test_TrialResolveAndConsumeChain |
| Test_RechargeFillGuardsAndRestore |

### 4.279 TestCompanionFace.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionFace.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionFace

| 公开方法 |
|---|
| Test_RosterFaceSpritesAll24Imported |
| Test_HudCompanionFaceRingAndStates |

### 4.280 TestCompanionFamilies2.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionFamilies2.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionFamilies2

| 公开方法 |
|---|
| Test_PointVacuumRespectsGhostHiddenWindow |
| Test_HaltAllFreezesBubbleAutonomousDrift |
| Test_PointVacuumChainsSplitterRupture |

### 4.281 TestCompanionQi2b.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionQi2b.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionQi2b

| 公开方法 |
|---|
| Test_HaltEscapingFreezesOnlyDrifting |
| Test_HaltAllFreezesLiveTargetsOnly |
| Test_PointVacuumNearestAndHonestShortfall |
| Test_PointVacuumEventPayloadMatchesTarget |

### 4.282 TestCompanionRoster.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionRoster.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionRoster

| 公开方法 |
|---|
| Test_RosterCompleteAndWellFormed |
| Test_VersionSplitTwelveAndTwelve |
| Test_ChapterSeatsExactlyTwoPerChapter |
| Test_AllSevenSkillKindsCoveredPerVersion |
| Test_DesignTableBindingsLocked |
| Test_SkillParamsWithinDesignEnvelope |
| Test_ProgressChargeCurve |
| Test_ProgressUpgradeAndPowerCurve |
| Test_UnlockChainChapterEndLevels |

### 4.283 TestCompanionRosterUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionRosterUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionRosterUi、Seat2StubAdService

| 公开方法 |
|---|
| Test_RosterZoneTabsAndCardCount |
| Test_SeatRequestUiRoundTrip |
| Test_UpgradeRequestUiRoundTrip |
| Test_SnapshotOpenSyncsEffectiveSeat |
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |
| Test_Seat2BannerVideoRoundTrip |
| Test_Seat2BannerReceiptAndLayoutLock |

### 4.284 TestCompanionRuntime.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionRuntime.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionRuntime

| 公开方法 |
|---|
| Test_ChargeFsmLifecycle |
| Test_ShieldLifecycleOneShot |
| Test_PrimarySeatReadyFamilyFirst |

### 4.285 TestCompanionSeat.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionSeat.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionSeat

| 公开方法 |
|---|
| Test_SeatPersistenceRoundTripAndBounds |
| Test_ResolveSeatExplicitWinsAndFallbacks |
| Test_TrySetSeatGuardsAndBroadcast |

### 4.286 TestCompanionSeat2.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionSeat2.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionSeat2

| 公开方法 |
|---|
| Test_Seat2UnlockedMatrix |
| Test_Seat2VideoGrantChain |
| Test_Seat2StardustPermanentPath |
| Test_Seat2DualSeatResolution |

### 4.287 TestCompanionUpgrade.cs

- 路径：`Assets/_Project/Tests/Editor/TestCompanionUpgrade.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCompanionUpgrade

| 公开方法 |
|---|
| Test_UpgradeTransactionGuardsAndOrdering |
| Test_CompanionLevelPersistenceAndDirtySaveClamp |
| Test_UpgradeBroadcastsBothEvents |

### 4.288 TestCopyPools.cs

- 路径：`Assets/_Project/Tests/Editor/TestCopyPools.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCopyPools

| 公开方法 |
|---|
| Test_SharePoolsCopyLocked |
| Test_SharePoolGatesAndDraws |
| Test_DailyFormDeterministic |
| Test_PostcardProgressMapping |
| Test_HarvestTopRules |
| Test_DailyFocusLines |
| Test_DailyMenuLinePick |

### 4.289 TestCoreBus.cs

- 路径：`Assets/_Project/Tests/Editor/TestCoreBus.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCoreBus

| 公开方法 |
|---|
| Test_BusSubscribePublishDelivers |
| Test_BusStructDefaultsZero |
| Test_BusReverseDispatchOrder |
| Test_BusUnsubscribeDuringPublish |
| Test_BusClearAllStopsDelivery |
| Test_BusTypeIsolation |

### 4.290 TestCoreJsonState.cs

- 路径：`Assets/_Project/Tests/Editor/TestCoreJsonState.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCoreJsonState

| 公开方法 |
|---|
| Test_LevelJsonRoundtripAllFields |
| Test_LevelJsonEmptyInputSafe |
| Test_StateMachineSetFiresEventWithPrevNext |
| Test_StateMachineSameStateSilent |
| Test_StateMachineEnumHasSixStates |
| Test_StateMachineResetToBoot |

### 4.291 TestCoreRegistry.cs

- 路径：`Assets/_Project/Tests/Editor/TestCoreRegistry.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestCoreRegistry、FakeRecordable、FakeSuctionable、FakeFactory

| 公开方法 |
|---|
| WriteSnapshot |
| ApplySuction |
| ApplyBurst |
| OnCaptured |
| Create |
| Test_ObjectRegistryRegisterUnregister |
| Test_ObjectRegistryNextIdMonotonic |
| Test_ObjectRegistryCopyActiveTruncates |
| Test_SpawnRegistryFactoryLifecycle |
| Test_ObjectPoolAcquireReleaseReuse |
| Test_PlaceholderSpriteFactoryCache |

### 4.292 TestDailyTask.cs

- 路径：`Assets/_Project/Tests/Editor/TestDailyTask.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestDailyTask

| 公开方法 |
|---|
| Test_DailyTaskProgressClaimAndHotPathGuard |
| Test_DailyTaskResetAcrossDays |
| Test_DailyTaskPersistenceAndMenuSnapshot |

### 4.293 TestDailyTaskUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestDailyTaskUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestDailyTaskUi

| 公开方法 |
|---|
| Test_DailyTaskUiRequestChannelAndCounters |
| Test_DailyTaskScreenModalFlow |

### 4.294 TestDoubleReward.cs

- 路径：`Assets/_Project/Tests/Editor/TestDoubleReward.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestDoubleReward、CaptureAnalytics

| 公开方法 |
|---|
| Test_DoubleGrantsLevelSandTwice |
| Test_DoubleRearmsOnNextSettlement |
| Test_DoubleIgnoresOtherPlacementsAndZeroSand |
| Test_ReviveAttributionFunnel |
| Report |

### 4.295 TestEmotionCurve.cs

- 路径：`Assets/_Project/Tests/Editor/TestEmotionCurve.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestEmotionCurve

| 公开方法 |
|---|
| Test_EmotionCurveCovers90Levels |
| Test_EmotionCurveChapterDoublePeak |
| Test_EmotionCurveNoTripleLowNovelty |
| Test_EmotionCurveSpecAnchorsChapterOne |
| Test_EmotionCurveValidationClean |

### 4.296 TestEvolveRitualFrame.cs

- 路径：`Assets/_Project/Tests/Editor/TestEvolveRitualFrame.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestEvolveRitualFrame

| 公开方法 |
|---|
| Test_ComposeEvolveLineFormatChapters |
| Test_RitualSharesBannerEnvelope |
| Test_EvolveNameCarriedOnBusEvent |
| Test_BannerMergesRitualBothOrders |
| Test_EvolveLineTypographyStepDown |

### 4.297 TestFeatherRevive.cs

- 路径：`Assets/_Project/Tests/Editor/TestFeatherRevive.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestFeatherRevive

| 公开方法 |
|---|
| Test_FeatherReviveConsumesAndReenters |
| Test_FeatherReviveRejectsWithoutStock |
| Test_FeatherMirrorReadsSameKey |

### 4.298 TestFiveBeats.cs

- 路径：`Assets/_Project/Tests/Editor/TestFiveBeats.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestFiveBeats

| 公开方法 |
|---|
| Test_Beat2AmbushHideAndReveal |
| Test_Beat3LandmarkPolishExactlyOnce |
| Test_Beat4DualFamilyOnLevel4 |
| Test_Beat4DualFamilyReplicatedCh2ToCh6 |
| Test_Beat5FinaleExactlyOnce |
| Test_BeatDomainS3Replication |
| Test_Beat2AmbushReplicatedCh3 |
| Test_Beat5FinaleReplicatedCh3ToCh6 |

### 4.299 TestFont.cs

- 路径：`Assets/_Project/Tests/Editor/TestFont.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestFont

| 公开方法 |
|---|
| Test_CnFontAssetLoadsFromResources |
| Test_CnFontCoversKeyGlyphs |
| Test_GlyphSetReportExists |
| Test_DisplayFontAssetLoadsFromResources |
| Test_DisplayFontCoversKeyGlyphs |
| Test_DisplayFontSubsetBudgetHeld |

### 4.300 TestGameplayCapture.cs

- 路径：`Assets/_Project/Tests/Editor/TestGameplayCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestGameplayCapture

| 公开方法 |
|---|
| Test_DustVariantIdentity |
| Test_DustRecordIdSequence |
| Test_DustApplySuctionAccumulates |
| Test_DustOnCapturedFreezesState |
| Test_DustRegistryLifecycle |
| Test_DustSnapshotContract |

### 4.301 TestInLevelChoiceFlow.cs

- 路径：`Assets/_Project/Tests/Editor/TestInLevelChoiceFlow.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestInLevelChoiceFlow

| 公开方法 |
|---|
| Test_OfferGate_LowTimeAndClearBelowGate_OncePerLevel |
| Test_OfferGate_ClearAtOrAboveGoal_NoOffer |
| Test_PickGamble_ArmsAndSettlesPlusFifteenSand |
| Test_PickGamble_FailLosesBet_NoPenalty_NoFreeRide |
| Test_PickExtend_GateMirrorRejectionAndRefund |
| Test_ApplyExtend_ActiveRunnerTimer_PlusTenSeconds |

### 4.302 TestJuiceCurves.cs

- 路径：`Assets/_Project/Tests/Editor/TestJuiceCurves.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestJuiceCurves

| 公开方法 |
|---|
| Test_SpawnPopEndpointsAndOvershoot |
| Test_CapturePopBumpThenSettle |
| Test_InflateForMonotonicAndClamped |
| Test_BreathEnvelope |
| Test_StretchOfEndpointsAndClamp |
| Test_GulpReboundEnvelope |

### 4.303 TestLevelRules.cs

- 路径：`Assets/_Project/Tests/Editor/TestLevelRules.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestLevelRules

| 公开方法 |
|---|
| Test_ResolveGoal_MinusOneFallsBackToTotal |
| Test_ResolveGoal_ZeroFallsBackToTotal |
| Test_ResolveGoal_GoalAboveTotalPassesThrough |
| Test_ResolveGoal_PlainGoalPassesThrough |
| Test_GoalReached_NonPositiveGoalAlwaysFalse |
| Test_GoalReached_AtGoalTrueBelowFalse |
| Test_ShouldCountdown_OnlyPositiveLimitCounts |
| Test_StepCountdown_DecrementsInPlaceUntilZero |

### 4.304 TestLevels.cs

- 路径：`Assets/_Project/Tests/Editor/TestLevels.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestLevels、ProbeTarget、ProbeFactory

| 公开方法 |
|---|
| Test_CatalogCountIsThree |
| Test_CatalogL1DustOnlyAllClear |
| Test_CatalogL2DustFurMix |
| Test_CatalogL3DebrisHeaviest |
| Test_CatalogGetOutOfBoundsNull |
| Test_CatalogGetReturnsDeepCopy |
| Test_CatalogAllLevelsCommonValid |
| Test_CatalogRoundtripAllLevels |
| Test_DailyPolicyDeterministicInRange |
| Test_DailyPolicyEdgeCases |
| ApplySuction |
| ApplyBurst |
| OnCaptured |
| Create |
| Test_RunnerStopLevelClearsWholeScene |

### 4.305 TestLevelSupply.cs

- 路径：`Assets/_Project/Tests/Editor/TestLevelSupply.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestLevelSupply

| 公开方法 |
|---|
| Test_SupplyArmClaimLapseGuards |
| Test_SupplyDailyCapAndRollover |
| Test_SupplyPersistenceAndSnapshotRequest |

### 4.306 TestLevelSupplyUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestLevelSupplyUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestLevelSupplyUi、SupplyStubAdService

| 公开方法 |
|---|
| RewardedReady |
| ShowRewarded |
| ShowInterstitial |
| ShowBanner |
| Test_SupplyDefeatFaceFullFlow |
| Test_SupplyMenuChipFaces |

### 4.307 TestLevelTimerRearm.cs

- 路径：`Assets/_Project/Tests/Editor/TestLevelTimerRearm.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestLevelTimerRearm

| 公开方法 |
|---|
| Test_TimeoutFail_Extend_RearmsCountdownWithBoughtSeconds |
| Test_Fail_ExtendZeroOrNegative_IsIgnored_NoRearm |
| Test_FirstPressGrace_GuidedLevels_ThenPressedAndReamed |

### 4.308 TestMetaProgress.cs

- 路径：`Assets/_Project/Tests/Editor/TestMetaProgress.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestMetaProgress

| 公开方法 |
|---|
| Test_MetaStageBoundaries |
| Test_MetaSandAccrualAndStageGrants |
| Test_MetaItemConsumeAndRefuse |
| Test_MetaChapterFlagsOnce |
| Test_WardrobeUnlockBoundaries |
| Test_MetaScaleMirrorZeroDrift |

### 4.309 TestNewbieAttraction.cs

- 路径：`Assets/_Project/Tests/Editor/TestNewbieAttraction.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestNewbieAttraction

| 公开方法 |
|---|
| Test_SneezeChargeTier_GuidedLevels |
| Test_VeilAlphaTier_ByChapter |
| Test_ClusterBuild_LinkDistance |

### 4.310 TestO1610WelcomeBand.cs

- 路径：`Assets/_Project/Tests/Editor/TestO1610WelcomeBand.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestO1610WelcomeBand

| 公开方法 |
|---|
| Test_WelcomeBandSlotGeometryAndYield |

### 4.311 TestOfflineEarnings.cs

- 路径：`Assets/_Project/Tests/Editor/TestOfflineEarnings.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestOfflineEarnings

| 公开方法 |
|---|
| Test_OfflineAccrueCapAndGuards |
| Test_OfflineClaimDoubleAndRejects |
| Test_OfflineSnapshotHeartbeatPersistence |

### 4.312 TestOfflineEarningsUi.cs

- 路径：`Assets/_Project/Tests/Editor/TestOfflineEarningsUi.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestOfflineEarningsUi

| 公开方法 |
|---|
| Test_OfflinePopupFaces |
| Test_OfflinePopupModalClaimFlow |

### 4.313 TestPaywallGate.cs

- 路径：`Assets/_Project/Tests/Editor/TestPaywallGate.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestPaywallGate

| 公开方法 |
|---|
| Test_Judge_NeedsExactlyTwoDigits |
| Test_Judge_RejectsNonDigits |
| Test_Judge_EveryLegalPairIsTwoDigitSum |
| Test_NextQuestion_InRangeAndNeverRepeats |
| Test_NextQuestion_NullRngIsSafe |
| Test_DrivingLocked_ProbeWinsAndFailsSafe |
| Test_CanOpenNow_RespectsGameStateAndDriving |
| Test_CanOpenNow_AutoEntryNeedsOptIn |
| Test_Retention_OwnedSkipsPaywall |
| Test_Retention_FirstPostcardFreeIsSingleUse |
| Test_Retention_BlockedPathNeverMarksRetained |
| Test_Retention_PaidAfterPaywallMarksRetained |
| Test_Retention_ReceiptDerivedFromKey |
| Test_GuestFace_SeesNoPaywallAndSpendsNoCredential |
| Test_Geometry_PillAndTapFloorArePinned |
| Test_Retention_ChapterKeyIsUnit |
| Test_Retention_LegacyLevelKeyMigrates |
| Test_StubCommerce_ValidateCodeRule |

### 4.314 TestPersistence.cs

- 路径：`Assets/_Project/Tests/Editor/TestPersistence.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestPersistence、FriendsOnlyInner、LowSelfInner

| 公开方法 |
|---|
| SubmitScore |
| GetFriendScores |
| SubmitScore |
| GetFriendScores |
| Test_PersistedBestNeverFalls |
| Test_MergeInjectsAndElevatesSelf |
| Test_NullInnerStillPersists |
| Test_ProgressStoreClampsAndMonotonic |
| Test_PlayerPrefsKeysStayIsolated |

### 4.315 TestPrewarmWiring.cs

- 路径：`Assets/_Project/Tests/Editor/TestPrewarmWiring.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestPrewarmWiring

| 公开方法 |
|---|
| Test_CaptureBurst_AutoBind_MenuEvent_PrewarmsHost |
| Test_SfxFlow_BindPrewarms_ResetClears_RebindPrewarmsAgain |

### 4.316 TestProductFx.cs

- 路径：`Assets/_Project/Tests/Editor/TestProductFx.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestProductFx

| 公开方法 |
|---|
| Test_ButtonPressHoldCurve |
| Test_ButtonReboundOvershootExact |
| Test_PopCurveOvershootEnvelope |
| Test_FlashEnvelope |
| Test_NumberRollEasing |
| Test_FlyBezierArcUpward |

### 4.317 TestProfileScope.cs

- 路径：`Assets/_Project/Tests/Editor/TestProfileScope.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestProfileScope

| 公开方法 |
|---|
| Test_SlotZeroIdentity |
| Test_SlotNShape |
| Test_SlotGuardRejectsOutOfRange |
| Test_NonRootKeysPassThrough |
| Test_DeviceLevelKeysAreDeclared |
| Test_ClaimGuest_MovesEveryKeyAndSwitchesSlot |
| Test_ClaimGuest_LeavesNoGuestKeysAndInventsNone |
| Test_ClaimGuest_RollsBackOnVerifyFailure |
| Test_ClaimGuest_ReportsSlotFullWithoutTouchingAnySlot |
| Test_ClaimGuest_RefusesWithoutRoster |
| Test_ClaimGuest_RecoversPendingMarker |
| Test_ProductionRosterShape |
| Test_DeleteProfile_RemovesEveryKeyInSlot |
| Test_DeleteProfile_RefusesGuestAndOutOfRange |
| Test_DeleteProfile_RefusesWithoutRoster |
| Test_DeleteProfile_FallsBackToGuestWhenActive |
| Test_DeleteProfile_ClearsStaleClaimMarker |
| Test_DeleteProfile_OccupationSharedWithClaim |
| Test_Switch_RefusesOutOfRange |
| Test_Switch_RefusesEmptyNamedSlot |
| Test_Switch_RefusesWithoutRebindHost |
| Test_Switch_SameSlotIsNoOp |
| Test_Switch_RecoversPendingClaimBeforeSwitching |
| Test_ReloadActive_AfterDeleteOfActiveSlot |
| Test_ReloadActive_RefusesWithoutRebindHost |
| Test_ReloadActive_DoesNotMoveTheSlot |

### 4.318 TestRemainderGuide.cs

- 路径：`Assets/_Project/Tests/Editor/TestRemainderGuide.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestRemainderGuide

| 公开方法 |
|---|
| Test_ActivatesAtTailAndClearsOnClose |
| Test_ZeroWeightPropHiddenFromGuide |

### 4.319 TestReplayMath.cs

- 路径：`Assets/_Project/Tests/Editor/TestReplayMath.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestReplayMath

| 公开方法 |
|---|
| Test_ChronoOffsetOf_HeadMinusValidFrames |
| Test_ChronoOffsetOf_FullRingIsZero |
| Test_ChronoOffsetOf_WrapNeverNegative |
| Test_SlotOf_WrapsAroundRing |
| Test_PickHighlightFrameIndex_Guards |
| Test_PickHighlightFrameIndex_MostSuckedWinsTieTakesLater |

### 4.320 TestReplayPoster.cs

- 路径：`Assets/_Project/Tests/Editor/TestReplayPoster.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestReplayPoster

| 公开方法 |
|---|
| Test_PosterComposeValidPng |
| Test_PosterEdgeInputsStayValid |
| Test_PosterSizeMatchesConfig |
| Test_PosterTempFileRoundtrip |

### 4.321 TestReviveRearm.cs

- 路径：`Assets/_Project/Tests/Editor/TestReviveRearm.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestReviveRearm

| 公开方法 |
|---|
| Test_ReviveRearmsGoalTracker |

### 4.322 TestSfxFamilySounds.cs

- 路径：`Assets/_Project/Tests/Editor/TestSfxFamilySounds.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSfxFamilySounds

| 公开方法 |
|---|
| Test_SfxFlow_FamilyKeys_RouteToOwnClip |

### 4.323 TestSfxSynthClips.cs

- 路径：`Assets/_Project/Tests/Editor/TestSfxSynthClips.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSfxSynthClips

| 公开方法 |
|---|
| Test_SynthClips_CreateArgOrder_ChannelsFrequency |

### 4.324 TestShareLanding.cs

- 路径：`Assets/_Project/Tests/Editor/TestShareLanding.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestShareLanding

| 公开方法 |
|---|
| Test_ParseValidLevelIds |
| Test_RejectsUntrustedInput |
| Test_RejectsZeroAndOverflow |
| Test_LandingLineVerbatimAndRedLines |

### 4.325 TestSignatureLevels.cs

- 路径：`Assets/_Project/Tests/Editor/TestSignatureLevels.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSignatureLevels

| 公开方法 |
|---|
| Test_SignatureOnePerNewbieLevel |
| Test_SignatureTimingUnfailable |
| Test_SignatureSpawnsInBounds |
| Test_SignatureInjectionDeterministic |
| Test_SignatureWhitelistExcludesFuzz |
| Test_FuzzHillBandMirrorMatchesCatalog |

### 4.326 TestSocial.cs

- 路径：`Assets/_Project/Tests/Editor/TestSocial.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSocial

| 公开方法 |
|---|
| Test_StubSubmitKeepsBestScore |
| Test_StubFriendScoresDefaultAnchor |
| Test_StubFriendScoresCenterOnSelf |
| Test_StubScoresClampAtZero |
| Test_TimeServiceUnixSecondsUtcWindow |
| Test_ArenaAnchorShapeLock |

### 4.327 TestSocialCloud.cs

- 路径：`Assets/_Project/Tests/Editor/TestSocialCloud.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSocialCloud

| 公开方法 |
|---|
| Test_TryParseScore_ValidPayloadParsesScore |
| Test_TryParseScore_ZeroScoreIsValid |
| Test_TryParseScore_MissingScoreFieldFails |
| Test_TryParseScore_NotJsonFails |
| Test_TryParseScore_NullInputFails |
| Test_TryParseScore_EmptyStringFails |

### 4.328 TestStoreAds.cs

- 路径：`Assets/_Project/Tests/Editor/TestStoreAds.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestStoreAds

| 公开方法 |
|---|
| Test_VaultAccruesToCapAndBreakGrants960 |
| Test_VaultRejectsWhenNotFull |
| Test_ShopSandDailyCap |

### 4.329 TestStoreFlow.cs

- 路径：`Assets/_Project/Tests/Editor/TestStoreFlow.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestStoreFlow

| 公开方法 |
|---|
| Test_StorePurchaseSettlesBundle |
| Test_StorePurchaseRefundsWhenShort |
| Test_StorePurchaseSingleOffersAndUnknown |
| Test_MetaMilestoneSpendsNeverShrinkStage |

### 4.330 TestSuctionFamilies.cs

- 路径：`Assets/_Project/Tests/Editor/TestSuctionFamilies.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSuctionFamilies

| 公开方法 |
|---|
| Test_VarietyKeysRegistered |
| Test_VarietyKeyConstantsMatchFactory |
| Test_CountWeightingAndPrices |
| Test_VarietyInjectionCoverage |
| Test_VarietyFrontLoadMonotonePricing |
| Test_GoldenFirstLevelContract |
| Test_VarietyRebateKeepsMargin |
| Test_ChapterTintsApplied |
| Test_DirtPaletteBoundsAndDistinct |
| Test_PlayBandMirrorMatchesCatalog |
| Test_GhostPhaseMath |
| Test_StickySpringPull |
| Test_FamilyConstantsLock |
| Test_GhostEngagedNeverBlocked |
| Test_MimicDisguiseAndReveal |
| Test_FactoryTintAndGearApplied |
| Test_SplitterTotalWeightingAndSweep |
| Test_ContentSelfCheckAllGreen |

### 4.331 TestSweepVerb.cs

- 路径：`Assets/_Project/Tests/Editor/TestSweepVerb.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSweepVerb

| 公开方法 |
|---|
| Test_SweepBeatBoundaryLocks |
| Test_ScratchThreeBeatsClear |
| Test_ScratchDecayDwelling |
| Test_ScratchZeroWeightNotInTotals |

### 4.332 TestSystemUnlocks.cs

- 路径：`Assets/_Project/Tests/Editor/TestSystemUnlocks.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestSystemUnlocks

| 公开方法 |
|---|
| Test_GateIdempotentMarkAndBits |
| Test_UnlockTableOnLevelComplete |
| Test_FirstChestOnFifteenCaptures |
| Test_DeadTaskRetargetLock |
| Test_MenuGatesNewPlayerSurface |

### 4.333 TestTutorialHint.cs

- 路径：`Assets/_Project/Tests/Editor/TestTutorialHint.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestTutorialHint

| 公开方法 |
|---|
| Test_TutorialHintKeysAndFlags |

### 4.334 TestU351BankCleanup.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351BankCleanup.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351BankCleanup

| 公开方法 |
|---|
| Test_DeadIconsRetired |
| Test_ConsumedIconPairLive |

### 4.335 TestU351BottomRhythm.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351BottomRhythm.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351BottomRhythm

| 公开方法 |
|---|
| Test_PaperEdgeExtendsBelowBanner |
| Test_RhythmSecondaryRow180Gap30 |
| Test_PaletteJsonSourcePackGate |

### 4.336 TestU351CapsuleWash.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351CapsuleWash.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351CapsuleWash

| 公开方法 |
|---|
| Test_StateWashClampsToWatercolorBand |
| Test_CapsuleStateColorRoutesThroughWash |

### 4.337 TestU351Density.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351Density.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351Density

| 公开方法 |
|---|
| Test_MenuFontSizeBandsThree |
| Test_MenuSecondaryEntriesFour |
| Test_CollectionFoldPortsWired |

### 4.338 TestU351Hitpad.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351Hitpad.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351Hitpad

| 公开方法 |
|---|
| Test_HitpadStackTilesAroundVisuals |
| Test_HitpadBuildProducesPad |

### 4.339 TestU351StardustSplit.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351StardustSplit.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351StardustSplit

| 公开方法 |
|---|
| Test_StardustPillPureCurrency |
| Test_StardustIconReshaped |

### 4.340 TestU351Stopgap.cs

- 路径：`Assets/_Project/Tests/Editor/TestU351Stopgap.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU351Stopgap

| 公开方法 |
|---|
| Test_MultiplierWindowRearmsOnLevelStart |
| Test_StormChargeFullSneezeRefusesConsume |

### 4.341 TestU360L4BWalk.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L4BWalk.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L4BWalk

| 公开方法 |
|---|
| Test_ChoiceBannerGeometryAndCopy |
| Test_DefeatReasonHumanized |

### 4.342 TestU360L4LegacyLayout.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L4LegacyLayout.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L4LegacyLayout

| 公开方法 |
|---|
| Test_JourneyScrollAndNameGeometry |
| Test_WinPostcardGeometry |

### 4.343 TestU360L4Ui.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L4Ui.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L4Ui

| 公开方法 |
|---|
| Test_CapsuleIconsAndSoftLiftWired |
| Test_WcSlicedPpuStadiumLock |
| Test_StardustLabelAlignAndIconLift |

### 4.344 TestU360L6B4Combo.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6B4Combo.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6B4Combo

| 公开方法 |
|---|
| Test_ComboTrackerChainWindowContract |
| Test_ComboOfferFiresOncePerChain |
| Test_ComboSilenceWindowGuardsReoffer |
| Test_ComboPointRewardCapturesThreeAtPointer |
| Test_ComboBoostRewardAppliesRadius |

### 4.345 TestU360L6B4Lick.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6B4Lick.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6B4Lick、LickProbe

| 公开方法 |
|---|
| ApplySuction |
| ApplyBurst |
| OnCaptured |
| WriteSnapshot |
| Test_LickContractValues |
| Test_LickDwellLocksAtThreshold |
| Test_LickDwellResetsOnMoveAway |
| Test_LickStrengthAppliesInField |

### 4.346 TestU360L6B5BellyTower.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6B5BellyTower.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6B5BellyTower

| 公开方法 |
|---|
| Test_TowerContractValues |
| Test_TowerFillAnchorMath |
| Test_TowerReadyPulseBounds |
| Test_TowerBuildAndChargeMapping |
| Test_TowerChargeClampMirror |

### 4.347 TestU360L6B5ChallengeStar.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6B5ChallengeStar.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6B5ChallengeStar

| 公开方法 |
|---|
| Test_ChallengeSegmentBandMatchesCatalog |
| Test_HudChallengeStarAndFirstHint |
| Test_HardMarkUnlockTimePoint |

### 4.348 TestU360L6B5PreLevelChoice.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6B5PreLevelChoice.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6B5PreLevelChoice

| 公开方法 |
|---|
| Test_PreLevelChoiceContractValues |
| Test_PreLevelOfferBandMapping |
| Test_PreLevelHourglassExtendsTimer |
| Test_PreLevelMagnetAppliesBoost |
| Test_PreLevelHoldFreezesAndReleases |

### 4.349 TestU360L6FullPowerStorm.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L6FullPowerStorm.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L6FullPowerStorm

| 公开方法 |
|---|
| Test_FullPowerContractValues |
| Test_FullPowerTreatAppliesRadius3 |
| Test_BelowChainKeepsBaseRadius |
| Test_TreatNeverReducesChapterBuff |

### 4.350 TestU360L7SweepTeach.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360L7SweepTeach.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360L7SweepTeach

| 公开方法 |
|---|
| Test_DataFaceSweepStainsOnlyAtStainLevels |
| Test_HudSweepTeachShowBeatHideAndDailyYield |
| Test_TutorialToastSurvivesPressHintExit |

### 4.351 TestU360S3Feel.cs

- 路径：`Assets/_Project/Tests/Editor/TestU360S3Feel.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestU360S3Feel

| 公开方法 |
|---|
| Test_HitStopTierDurations |
| Test_HitStopWatchdogRestoresOnDeadline |
| Test_AvLockThrottleWindowFastChain |
| Test_CaptureBeatPredictorContract |
| Test_CaptureBurstAudibleDowngrade |
| Test_CameraShakeTakeMaxAndDecay |
| Test_StormFlashProfileEnvelope |

### 4.352 TestWaveDirector.cs

- 路径：`Assets/_Project/Tests/Editor/TestWaveDirector.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestWaveDirector

| 公开方法 |
|---|
| Test_WavePlanSplitsAndThresholdAdvance |
| Test_WaveDisabledOutsidePilot |
| Test_CountOnlyAdvanceAndZeroWeightExcluded |
| Test_MidEventKindRotationMapping |
| Test_MidEventHiddenTreasureLiveChain |
| Test_MidEventHiddenTreasureNoTemplateNoAction |
| Test_MidEventBuddySkillLessonLiveChain |
| Test_MidEventLandmarkBeckonLiveChain |
| Test_W3PieceThresholdAcrossCatalog |
| Test_W3ChainFiresWhenGoalSitsInW3 |
| Test_W3ThresholdNegativeControl |
| Test_SignatureSpriteMovesToW3Head |
| Test_W3GoalTypeFilterSplitsPieceAccounts |

### 4.353 U360L3S3MomentShot.cs

- 路径：`Assets/_Project/Tests/Editor/U360L3S3MomentShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360L3S3MomentShot

| 公开方法 |
|---|
| Run |

### 4.354 U360L4CShot.cs

- 路径：`Assets/_Project/Tests/Editor/U360L4CShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360L4CShot

| 公开方法 |
|---|
| Run |

### 4.355 U360L4WalkShot.cs

- 路径：`Assets/_Project/Tests/Editor/U360L4WalkShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360L4WalkShot

| 公开方法 |
|---|
| Run |

### 4.356 U360L7FtueCapture.cs

- 路径：`Assets/_Project/Tests/Editor/U360L7FtueCapture.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360L7FtueCapture

| 公开方法 |
|---|
| Run |

### 4.357 U360LevelTour.cs

- 路径：`Assets/_Project/Tests/Editor/U360LevelTour.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360LevelTour

| 公开方法 |
|---|
| Run |

### 4.358 U360StageDiagnostics.cs

- 路径：`Assets/_Project/Tests/Editor/U360StageDiagnostics.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360StageDiagnostics

| 公开方法 |
|---|
| Run |

### 4.359 U360SweepShot.cs

- 路径：`Assets/_Project/Tests/Editor/U360SweepShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：U360SweepShot

| 公开方法 |
|---|
| Run |

### 4.360 X1958MenuShot.cs

- 路径：`Assets/_Project/Tests/Editor/X1958MenuShot.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：X1958MenuShot

| 公开方法 |
|---|
| Run |

### 4.361 EntityProbeDriver.cs

- 路径：`Assets/_Project/Tests/PlayGate/EntityProbeDriver.cs`
- 命名空间：`GimmeAll.PlayGate`
- 类型：EntityProbeDriver

### 4.362 FxLoopDriver.cs

- 路径：`Assets/_Project/Tests/PlayGate/FxLoopDriver.cs`
- 命名空间：`GimmeAll.PlayGate`
- 类型：FxLoopDriver

### 4.363 PlayLoopDriver.cs

- 路径：`Assets/_Project/Tests/PlayGate/PlayLoopDriver.cs`
- 命名空间：`GimmeAll.PlayGate`
- 类型：PlayLoopDriver

### 4.364 ArrivalBanner.cs

- 路径：`Assets/_Project/UI/ArrivalBanner.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ArrivalBanner

| 公开方法 |
|---|
| ComposeEvolveLine |

### 4.365 ButtonSquash.cs

- 路径：`Assets/_Project/UI/ButtonSquash.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ButtonSquash

| 公开方法 |
|---|
| PressScaleAt |
| ReboundScaleAt |
| OnPointerDown |
| OnPointerUp |

### 4.366 BVersionPortMap.cs

- 路径：`Assets/_Project/UI/BVersionPortMap.cs`
- 命名空间：`GimmeAll.UI`
- 类型：BVersionPortMap、PortState

| 公开方法 |
|---|
| AssertIntact |

### 4.367 CarLayout.Wing.cs

- 路径：`Assets/_Project/UI/Car/CarLayout.Wing.cs`
- 命名空间：`GimmeAll.UI`
- 类型：InfoPlateFitter、SlotActiveFollower、InfoVisibilityFollower、CameraViewportFitter

| 公开方法 |
|---|
| SetWingContentVisible |
| WingActionBadgeX |
| WingActionCaption |
| Bind |
| Bind |

### 4.368 CarLayout.cs

- 路径：`Assets/_Project/UI/CarLayout.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| PlayViewAspect |
| Build |
| AttachWingAction |
| AttachWingParent |
| AttachWingParentLeft |
| AttachWingParentPull |
| AttachWingInfo |
| AttachWingInfoSlot |
| AttachWingInfoBackground |
| FitWingInfoWrap |
| WingFont |
| WingInfoRowHeight |
| FitWingInfoRow |
| BindWingInfoVisibility |

### 4.369 ChapterChestScreen.cs

- 路径：`Assets/_Project/UI/ChapterChestScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Show |
| CapsuleLabel |
| CapsuleLit |
| ItemNameOf |

### 4.370 ChapterJourneyScreen.Car.cs

- 路径：`Assets/_Project/UI/ChapterJourney/ChapterJourneyScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| CarStationOf |

### 4.371 ChapterJourneyScreen.cs

- 路径：`Assets/_Project/UI/ChapterJourneyScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Show |
| Hide |
| CardNameOf |
| CardSubOf |
| CardStatOf |

### 4.372 ChapterPalette.cs

- 路径：`Assets/_Project/UI/ChapterPalette.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ChapterPalette

| 公开方法 |
|---|
| AccentOf |
| ButtonOf |
| BannerOf |
| VeilOf |

### 4.373 ChapterChestScreen.Car.cs

- 路径：`Assets/_Project/UI/Chest/ChapterChestScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.374 ChoiceBanner.cs

- 路径：`Assets/_Project/UI/ChoiceBanner.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ChoiceBanner

### 4.375 CodexCatalog.cs

- 路径：`Assets/_Project/UI/CodexCatalog.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CodexCatalog、CodexEntry

| 公开方法 |
|---|
| CryKeyOf |
| ChapterNameOf |
| RebindForProfile |
| UsePrefsKeyForTests |
| TotalCount |
| Get |
| IsUnlocked |
| LevelsDoneOf |
| LevelsDoneTotal |
| UnlockedCount |
| ProgressLine |
| ChapterDisplayName |

### 4.376 CodexRevealFx.cs

- 路径：`Assets/_Project/UI/CodexRevealFx.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CodexRevealFx

| 公开方法 |
|---|
| Play |

### 4.377 CollectionCodex.cs

- 路径：`Assets/_Project/UI/Collection/CollectionCodex.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CardView

| 公开方法 |
|---|
| PreviewLine |

### 4.378 CollectionCompanions.cs

- 路径：`Assets/_Project/UI/Collection/CollectionCompanions.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CompanionCardView

### 4.379 CollectionScreen.Car.cs

- 路径：`Assets/_Project/UI/Collection/CollectionScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.380 CollectionScreen.cs

- 路径：`Assets/_Project/UI/CollectionScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Show |
| Hide |
| AccelLabel |

### 4.381 CopyPools.cs

- 路径：`Assets/_Project/UI/CopyPools.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CopyPools、DailyFocus、ShareLanding

| 公开方法 |
|---|
| WinLineWeight |
| WinLineAt |
| DrawWinShareLine |
| FailLineWeight |
| FailLineAt |
| DrawFailShareLine |
| TryGetSignatureItem |
| DisplayNameOf |
| RarityRankOf |
| TryBuildHarvestLine |
| DailyFormOf |
| BuildFormLine |
| VisitedChaptersOf |
| BuildPostcardCountLine |
| ReadProgressRaw |
| BuildDailyMenuSubtitle |
| BuildDailyHudLine |
| TryBuildDailySignatureLine |
| PickDailyMenuLine |
| BuildLandingLine |

### 4.382 DailyTaskScreen.Car.cs

- 路径：`Assets/_Project/UI/DailyTask/DailyTaskScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.383 DailyTaskScreen.cs

- 路径：`Assets/_Project/UI/DailyTaskScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Show |
| DoneCount |
| ClaimableCount |

### 4.384 DuduIdlePlayer.cs

- 路径：`Assets/_Project/UI/DuduIdlePlayer.cs`
- 命名空间：`GimmeAll.UI`
- 类型：DuduIdlePlayer

### 4.385 FamilyNamePrompt.cs

- 路径：`Assets/_Project/UI/FamilyNamePrompt.cs`
- 命名空间：`GimmeAll.UI`
- 类型：FamilyNamePrompt

| 公开方法 |
|---|
| RebindForProfile |
| PromptSeen |
| MarkPromptSeen |

### 4.386 FlyToTarget.cs

- 路径：`Assets/_Project/UI/FlyToTarget.cs`
- 命名空间：`GimmeAll.UI`
- 类型：FlyToTarget、FlyRunner

| 公开方法 |
|---|
| WorldToCanvas |
| CanvasCenterOf |
| Bezier01 |
| Fly |

### 4.387 FrameGeometryProbe.cs

- 路径：`Assets/_Project/UI/FrameGeometryProbe.cs`
- 命名空间：`GimmeAll.UI`
- 类型：FrameGeometryProbe

| 公开方法 |
|---|
| Install |

### 4.388 FullChargeOverlay.cs

- 路径：`Assets/_Project/UI/FullChargeOverlay.cs`
- 命名空间：`GimmeAll.UI`
- 类型：FullChargeOverlay

| 公开方法 |
|---|
| RebindForProfile |
| Ensure |

### 4.389 FxEvents.cs

- 路径：`Assets/_Project/UI/FxEvents.cs`
- 命名空间：`GimmeAll.UI`
- 类型：HealthNoticeClosed、LevelStartRequested、DailyLevelRequested、ContinueRequested、ReturnMenuRequested、ReviveRequested

### 4.390 HealthNoticeScreen.cs

- 路径：`Assets/_Project/UI/HealthNoticeScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：HealthNoticeScreen、AutopilotLandingDriver

| 公开方法 |
|---|
| Begin |
| Show |
| Hide |

### 4.391 CompanionChargeRing.cs

- 路径：`Assets/_Project/UI/Hud/CompanionChargeRing.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CompanionChargeRing

### 4.392 CompanionRecharge.cs

- 路径：`Assets/_Project/UI/Hud/CompanionRecharge.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CompanionRecharge

### 4.393 Front3HudPanel.cs

- 路径：`Assets/_Project/UI/Hud/Front3HudPanel.cs`
- 命名空间：`GimmeAll.UI`
- 类型：Front3HudPanel

| 公开方法 |
|---|
| Build |
| SetVisible |
| HudLine |
| Tick |

### 4.394 InGameHud.Boosters.cs

- 路径：`Assets/_Project/UI/Hud/InGameHud.Boosters.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.395 ParentKeyHudPanel.cs

- 路径：`Assets/_Project/UI/Hud/ParentKeyHudPanel.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ParentKeyHudPanel

| 公开方法 |
|---|
| Build |
| ResetForLevel |
| TickCooldown |
| RefreshLabels |

### 4.396 ICommerceService.cs

- 路径：`Assets/_Project/UI/ICommerceService.cs`
- 命名空间：`GimmeAll.UI`
- 类型：CommerceChannel、PurchaseStatus、PurchaseReceipt、ICommerceService

| 公开方法 |
|---|
| Ok |
| Fail |
| Cancel |

### 4.397 InGameHud.cs

- 路径：`Assets/_Project/UI/InGameHud.cs`
- 命名空间：`GimmeAll.UI`
- 类型：InfoRowSeat

| 公开方法 |
|---|
| RebindForProfile |
| AddInfoRow |
| GetInfoRow |
| SetInfoRow |
| SetInfoRow |

### 4.398 LeaderboardScreen.Car.cs

- 路径：`Assets/_Project/UI/Leaderboard/LeaderboardScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.399 LeaderboardScreen.cs

- 路径：`Assets/_Project/UI/LeaderboardScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Open |
| Show |
| Hide |

### 4.400 MainMenuScreen.cs

- 路径：`Assets/_Project/UI/MainMenuScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| SetDuduPose |
| Show |
| Hide |

### 4.401 MenuChromeKit.cs

- 路径：`Assets/_Project/UI/Menu/MenuChromeKit.cs`
- 命名空间：`GimmeAll.UI`
- 类型：HitpadSpec

### 4.402 MenuEntryBar.cs

- 路径：`Assets/_Project/UI/Menu/MenuEntryBar.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| InvokeLandingForAutopilot |

### 4.403 MenuProgressBadges.cs

- 路径：`Assets/_Project/UI/Menu/MenuProgressBadges.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.404 NumberRoll.cs

- 路径：`Assets/_Project/UI/NumberRoll.cs`
- 命名空间：`GimmeAll.UI`
- 类型：NumberRoll、FloatUpDriver

| 公开方法 |
|---|
| Attach |
| Set |
| FloatUp |

### 4.405 OfflineEarningsPopup.cs

- 路径：`Assets/_Project/UI/OfflineEarningsPopup.cs`
- 命名空间：`GimmeAll.UI`
- 类型：OfflineEarningsPopup

| 公开方法 |
|---|
| Show |
| AwayText |
| AmountText |

### 4.406 ParentGatePanel.cs

- 路径：`Assets/_Project/UI/ParentGatePanel.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ParentGatePanel

| 公开方法 |
|---|
| Judge |
| NextQuestion |
| Build |
| Begin |
| Show |
| SetInteractable |
| OnKey |

### 4.407 PaywallScreen.Car.cs

- 路径：`Assets/_Project/UI/Paywall/PaywallScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.408 PaywallScreen.Flow.cs

- 路径：`Assets/_Project/UI/Paywall/PaywallScreen.Flow.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.409 PaywallScreen.Helpers.cs

- 路径：`Assets/_Project/UI/Paywall/PaywallScreen.Helpers.cs`
- 命名空间：`GimmeAll.UI`
- 类型：PostcardRetainKeys

| 公开方法 |
|---|
| IsRetained |
| FlushPendingRetention |
| ChapterOf |
| HasCard |
| FullCharge |
| DuelRope |
| Of |
| MigrateLegacyLevelKeys |
| LegacyLevelKey |

### 4.410 PaywallScreen.cs

- 路径：`Assets/_Project/UI/PaywallScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：PaywallEntry、Stage

| 公开方法 |
|---|
| DrivingLocked |
| RequestRetention |
| Show |
| CanOpenNow |
| ResetSessionSuppression |

### 4.411 ProfileManagerPanel.cs

- 路径：`Assets/_Project/UI/ProfileManagerPanel.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ProfileManagerPanel

| 公开方法 |
|---|
| Open |
| Refresh |
| OnSwitchClicked |
| OnDeleteClicked |
| Close |
| ShowPanel |

### 4.412 ProfileScreen.cs

- 路径：`Assets/_Project/UI/ProfileScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ProfileScreen

| 公开方法 |
|---|
| Show |
| Hide |

### 4.413 ResultScreen.Car.cs

- 路径：`Assets/_Project/UI/Result/ResultScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.414 ResultScreen.Postcard.cs

- 路径：`Assets/_Project/UI/Result/ResultScreen.Postcard.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.415 ResultScreen.cs

- 路径：`Assets/_Project/UI/ResultScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| SupplyLabel |
| Show |
| Hide |

### 4.416 SafeAreaFitter.cs

- 路径：`Assets/_Project/UI/SafeAreaFitter.cs`
- 命名空间：`GimmeAll.UI`
- 类型：SafeAreaFitter

### 4.417 ScreenRouter.cs

- 路径：`Assets/_Project/UI/ScreenRouter.cs`
- 命名空间：`GimmeAll.UI`
- 类型：ScreenRouter

### 4.418 SneezeButton.cs

- 路径：`Assets/_Project/UI/SneezeButton.cs`
- 命名空间：`GimmeAll.UI`
- 类型：SneezeButton

### 4.419 StoreScreen.Car.cs

- 路径：`Assets/_Project/UI/Store/StoreScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.420 StoreCatalog.cs

- 路径：`Assets/_Project/UI/StoreCatalog.cs`
- 命名空间：`GimmeAll.UI`
- 类型：StoreCatalog

| 公开方法 |
|---|
| UsePrefsKeyForTests |
| ReadSand |
| ReadItemCount |
| ReadVaultBalance |
| ReadShopSandCappedToday |
| ReadSeat2Mode |

### 4.421 StoreScreen.cs

- 路径：`Assets/_Project/UI/StoreScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiNudge

| 公开方法 |
|---|
| Show |
| Hide |
| SandLabelOf |
| OwnedLabelOf |
| Kick |

### 4.422 StubCommerceService.cs

- 路径：`Assets/_Project/UI/StubCommerceService.cs`
- 命名空间：`GimmeAll.UI`
- 类型：StubCommerceService

| 公开方法 |
|---|
| ValidateCode |
| SubmitCode |
| Purchase |
| Restore |
| ReadBuyout |
| WriteBuyout |

### 4.423 TutorialHint.cs

- 路径：`Assets/_Project/UI/TutorialHint.cs`
- 命名空间：`GimmeAll.UI`
- 类型：TutorialHint

| 公开方法 |
|---|
| RebindForProfile |
| PressSeen |
| MarkPressSeen |
| SneezeSeen |
| MarkSneezeSeen |
| ReleaseSeen |
| MarkReleaseSeen |

### 4.424 UIArt.cs

- 路径：`Assets/_Project/UI/UIArt.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UIArt

| 公开方法 |
|---|
| Icon |
| Plain |

### 4.425 UiBob.cs

- 路径：`Assets/_Project/UI/UiBob.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiBob

### 4.426 UiDrift.cs

- 路径：`Assets/_Project/UI/UiDrift.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiDrift

### 4.427 UiEasing.cs

- 路径：`Assets/_Project/UI/UiEasing.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiEasing

| 公开方法 |
|---|
| EaseOut01 |
| EaseOutCubic01 |
| EaseIn01 |
| Pop01 |
| FlashAlphaAt |

### 4.428 UiFade.cs

- 路径：`Assets/_Project/UI/UiFade.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiFade

| 公开方法 |
|---|
| Ensure |
| PlayIn |
| PlayOut |

### 4.429 UiFlash.cs

- 路径：`Assets/_Project/UI/UiFlash.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiFlash

| 公开方法 |
|---|
| ResetProbe |
| Flash |
| Flash |

### 4.430 UiKeySubmit.cs

- 路径：`Assets/_Project/UI/UiKeySubmit.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiKeySubmit

| 公开方法 |
|---|
| Attach |
| Listen |
| Ignore |

### 4.431 UIRoot.cs

- 路径：`Assets/_Project/UI/UIRoot.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UIRoot、ButtonShadowPad

| 公开方法 |
|---|
| EnsureRoot |
| CreateText |
| CreateButton |
| CreatePanel |
| AnchorStretch |
| AnchorCenter |
| AnchorTop |
| AnchorBottom |
| Hitpad |
| Hitpad |

### 4.432 WardrobeScreen.Car.cs

- 路径：`Assets/_Project/UI/Wardrobe/WardrobeScreen.Car.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

### 4.433 WardrobeScreen.cs

- 路径：`Assets/_Project/UI/WardrobeScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：（无声明）

| 公开方法 |
|---|
| Show |
| OutfitNameOf |
| IsUnlocked |
| UseEquipKeyForTests |
| UseProgressKeyForTests |
| RebindForProfile |

### 4.434 BellyWindow.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/BellyWindow.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：BellyWindow、Chip、BellyMath

| 公开方法 |
|---|
| Ensure |
| FlightPos01 |
| OrbitOffset |

### 4.435 HapticPulse.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/HapticPulse.cs`
- 命名空间：`GimmeAll.Game`
- 类型：HapticPulse

### 4.436 JuiceCurves.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/JuiceCurves.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：JuiceCurves

| 公开方法 |
|---|
| SpawnPop01 |
| CapturePop01 |
| InflateFor |
| Breath |

### 4.437 MetaFlow.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/MetaFlow.cs`
- 命名空间：`GimmeAll.Game`
- 类型：MetaFlow

### 4.438 MetaStore.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/MetaStore.cs`
- 命名空间：`GimmeAll.Game`
- 类型：MetaStore

| 公开方法 |
|---|
| StageOf |
| AddSand |
| ItemCount |
| GrantItem |
| TryConsume |
| ChapterClearedOnce |
| MarkChapterCleared |
| UsePrefsKeyForTests |

### 4.439 ShareLandingGate.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/ShareLandingGate.cs`
- 命名空间：`GimmeAll.Game`
- 类型：ShareLandingGate、LandingQuery

| 公开方法 |
|---|
| ResolveFromLaunch |
| TryParseLevelId |

### 4.440 SignatureArt.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/SignatureArt.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SignatureArt

| 公开方法 |
|---|
| SpriteOf |

### 4.441 SuctionTrail.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/SuctionTrail.cs`
- 命名空间：`GimmeAll.Gameplay`
- 类型：SuctionTrail、Dot、TrailHost

| 公开方法 |
|---|
| Emit |

### 4.442 TestBellyMath.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/TestBellyMath.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestBellyMath

| 公开方法 |
|---|
| Test_FlightEndpointsAndLift |
| Test_FlightHorizontalApproachMonotonic |
| Test_OrbitOnCircleAndDeterministic |

### 4.443 TestJuiceCurves.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/TestJuiceCurves.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestJuiceCurves

| 公开方法 |
|---|
| Test_SpawnPopEndpointsAndOvershoot |
| Test_CapturePopBumpThenSettle |
| Test_InflateForMonotonicAndClamped |
| Test_BreathEnvelope |

### 4.444 TestMetaProgress.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/TestMetaProgress.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestMetaProgress

| 公开方法 |
|---|
| Test_MetaStageBoundaries |
| Test_MetaSandAccrualAndStageGrants |
| Test_MetaItemConsumeAndRefuse |
| Test_MetaChapterFlagsOnce |
| Test_WardrobeUnlockBoundaries |
| Test_MetaScaleMirrorZeroDrift |

### 4.445 TestShareLanding.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/TestShareLanding.cs`
- 命名空间：`GimmeAll.Tests`
- 类型：TestShareLanding

| 公开方法 |
|---|
| Test_ParseValidLevelIds |
| Test_RejectsUntrustedInput |
| Test_RejectsZeroAndOverflow |
| Test_LandingLineVerbatimAndRedLines |

### 4.446 UiBob.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/UiBob.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiBob

### 4.447 UiFade.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/UiFade.cs`
- 命名空间：`GimmeAll.UI`
- 类型：UiFade

| 公开方法 |
|---|
| Ensure |
| PlayIn |
| PlayOut |

### 4.448 WardrobeScreen.cs

- 路径：`production/reports/p0-quarantine-2026-09-17/WardrobeScreen.cs`
- 命名空间：`GimmeAll.UI`
- 类型：WardrobeScreen

| 公开方法 |
|---|
| Show |
| IsUnlocked |
| UseProgressKeyForTests |

## 5 数据结构与模块协作

各模块通过 Core 层的事件总线与注册表通信，禁止跨模块直接引用；对象池复用高频实例，状态机驱动界面流程。

## 6 异常与容错

关键路径对空引用与资源缺失做显式判空；存档写入采用原子替换，中断后回退到上一份可用存档。

## 7 性能与资源

目标 60fps；纹理按规格压缩，图集按屏分组加载；高频对象走对象池，避免运行时 GC 峰值。

## 8 部署与运行

构建产物为 Android APK 与 Windows 可执行文件；启动后进入主场景，按引导流程进入首个关卡。

## 9 附录：源文件清单

| # | 文件 |
|---:|---|
| 1 | .codely-cli/mod/mm-committed.cs |
| 2 | .codely-cli/mod/MOD-12-orig-MetaStore.cs |
| 3 | Assets/_Project/Ads/AdConfig.cs |
| 4 | Assets/_Project/Ads/AdsSelfTest.cs |
| 5 | Assets/_Project/Ads/RewardCatalog.cs |
| 6 | Assets/_Project/Ads/StubAdRunner.cs |
| 7 | Assets/_Project/Ads/StubAdService.cs |
| 8 | Assets/_Project/Ads/WeChatAdBootstrap.cs |
| 9 | Assets/_Project/Ads/WeChatAdService.cs |
| 10 | Assets/_Project/Audio/AudioSelfTest.cs |
| 11 | Assets/_Project/Audio/BgmBus.cs |
| 12 | Assets/_Project/Audio/SfxBus.cs |
| 13 | Assets/_Project/Audio/SfxFlow.cs |
| 14 | Assets/_Project/Audio/SfxSynth.Base.cs |
| 15 | Assets/_Project/Audio/SfxSynth.cs |
| 16 | Assets/_Project/Audio/SfxSynth.Families.cs |
| 17 | Assets/_Project/Audio/SfxSynth.Signature.cs |
| 18 | Assets/_Project/Car/CarCabinBridge.cs |
| 19 | Assets/_Project/Car/CarCabinMock.cs |
| 20 | Assets/_Project/Core/AdCopy.cs |
| 21 | Assets/_Project/Core/AdFrequencyGate.cs |
| 22 | Assets/_Project/Core/AdServiceSeam.cs |
| 23 | Assets/_Project/Core/AdsPolicy.cs |
| 24 | Assets/_Project/Core/CaptureBeat.cs |
| 25 | Assets/_Project/Core/ComboTracker.cs |
| 26 | Assets/_Project/Core/Companions/CompanionDef.cs |
| 27 | Assets/_Project/Core/Companions/CompanionProgress.cs |
| 28 | Assets/_Project/Core/Companions/CompanionRuntime.cs |
| 29 | Assets/_Project/Core/Events/AdMetrics.cs |
| 30 | Assets/_Project/Core/Events/AdsEvents.cs |
| 31 | Assets/_Project/Core/Events/AudioEvents.cs |
| 32 | Assets/_Project/Core/Events/LevelEvents.cs |
| 33 | Assets/_Project/Core/Events/MetaEvents.cs |
| 34 | Assets/_Project/Core/Events/ProfileEvents.cs |
| 35 | Assets/_Project/Core/Events/UIEvents.cs |
| 36 | Assets/_Project/Core/GameEventBus.cs |
| 37 | Assets/_Project/Core/GameEvents.cs |
| 38 | Assets/_Project/Core/GameStateMachine.cs |
| 39 | Assets/_Project/Core/IAnalyticsService.cs |
| 40 | Assets/_Project/Core/ICanvasBoard.cs |
| 41 | Assets/_Project/Core/ICarCabinSignalSource.cs |
| 42 | Assets/_Project/Core/IMetaService.cs |
| 43 | Assets/_Project/Core/InterstitialPolicy.cs |
| 44 | Assets/_Project/Core/IRecordable.cs |
| 45 | Assets/_Project/Core/IServices.cs |
| 46 | Assets/_Project/Core/ISuctionable.cs |
| 47 | Assets/_Project/Core/ISuctionGuide.cs |
| 48 | Assets/_Project/Core/LevelData.cs |
| 49 | Assets/_Project/Core/ObjectPool.cs |
| 50 | Assets/_Project/Core/ObjectRegistry.cs |
| 51 | Assets/_Project/Core/PlaceholderSpriteFactory.cs |
| 52 | Assets/_Project/Core/PrefsFlush.cs |
| 53 | Assets/_Project/Core/ProfileClaim.cs |
| 54 | Assets/_Project/Core/ProfileDelete.cs |
| 55 | Assets/_Project/Core/ProfileReloadContract.cs |
| 56 | Assets/_Project/Core/ProfileRosterContract.cs |
| 57 | Assets/_Project/Core/ProfileScope.cs |
| 58 | Assets/_Project/Core/ProfileSwitch.cs |
| 59 | Assets/_Project/Core/ServiceRegistry.cs |
| 60 | Assets/_Project/Core/SpawnRegistry.cs |
| 61 | Assets/_Project/Core/SystemUnlockGate.cs |
| 62 | Assets/_Project/Editor/BuildAndroid.cs |
| 63 | Assets/_Project/Game/AmbientLoopLayer.cs |
| 64 | Assets/_Project/Game/AutoPilotMenuStart.cs |
| 65 | Assets/_Project/Game/AutoPilotStationAdvance.cs |
| 66 | Assets/_Project/Game/BackdropBoard.cs |
| 67 | Assets/_Project/Game/Bootstrap.cs |
| 68 | Assets/_Project/Game/CameraRig.cs |
| 69 | Assets/_Project/Game/CarAppLifecycle.cs |
| 70 | Assets/_Project/Game/ChapterArt.cs |
| 71 | Assets/_Project/Game/ChapterChestFlow.cs |
| 72 | Assets/_Project/Game/CheckInFlow.cs |
| 73 | Assets/_Project/Game/CodexAccelFlow.cs |
| 74 | Assets/_Project/Game/CodexFlow.cs |
| 75 | Assets/_Project/Game/ComboChoiceFlow.cs |
| 76 | Assets/_Project/Game/CompanionAdFlow.cs |
| 77 | Assets/_Project/Game/CompanionCoordinator.cs |
| 78 | Assets/_Project/Game/CompanionRosterFlow.cs |
| 79 | Assets/_Project/Game/CompanionSeatFlow.cs |
| 80 | Assets/_Project/Game/CompanionUpgradeFlow.cs |
| 81 | Assets/_Project/Game/DailyTaskFlow.cs |
| 82 | Assets/_Project/Game/DevLevelBoot.cs |
| 83 | Assets/_Project/Game/DuelRope.cs |
| 84 | Assets/_Project/Game/Editor/ArtImportRules.cs |
| 85 | Assets/_Project/Game/Editor/AudioPackageMatrix.cs |
| 86 | Assets/_Project/Game/Editor/NewbieRunSetup.cs |
| 87 | Assets/_Project/Game/Editor/O1610BorderBake.cs |
| 88 | Assets/_Project/Game/Editor/ProjectBuild.cs |
| 89 | Assets/_Project/Game/Editor/StoreAssetGen.cs |
| 90 | Assets/_Project/Game/FeelPulse.cs |
| 91 | Assets/_Project/Game/FileAnalyticsService.cs |
| 92 | Assets/_Project/Game/HapticPulse.cs |
| 93 | Assets/_Project/Game/HapticsRelay.cs |
| 94 | Assets/_Project/Game/HiddenTreasureFlow.cs |
| 95 | Assets/_Project/Game/InLevelChoiceFlow.cs |
| 96 | Assets/_Project/Game/LevelSupplyFlow.cs |
| 97 | Assets/_Project/Game/Meta/MetaService.Companion.cs |
| 98 | Assets/_Project/Game/Meta/MetaService.Daily.cs |
| 99 | Assets/_Project/Game/Meta/MetaService.Offline.cs |
| 100 | Assets/_Project/Game/Meta/MetaService.Profile.cs |
| 101 | Assets/_Project/Game/Meta/MetaService.Sand.cs |
| 102 | Assets/_Project/Game/Meta/MetaService.Supply.cs |
| 103 | Assets/_Project/Game/Meta/MetaService.TestKeys.cs |
| 104 | Assets/_Project/Game/MetaFlow.cs |
| 105 | Assets/_Project/Game/MetaService.cs |
| 106 | Assets/_Project/Game/MetaStore.cs |
| 107 | Assets/_Project/Game/OfflineEarningsFlow.cs |
| 108 | Assets/_Project/Game/PadLevelSwitch.cs |
| 109 | Assets/_Project/Game/PreLevelChoiceFlow.cs |
| 110 | Assets/_Project/Game/ProfileReload.cs |
| 111 | Assets/_Project/Game/ProfileRoster.cs |
| 112 | Assets/_Project/Game/QuitTrace.cs |
| 113 | Assets/_Project/Game/RevealVeil.cs |
| 114 | Assets/_Project/Game/ScreenshotKey.cs |
| 115 | Assets/_Project/Game/ShareLandingGate.cs |
| 116 | Assets/_Project/Game/StationArt.cs |
| 117 | Assets/_Project/Game/StoreAdFlow.cs |
| 118 | Assets/_Project/Game/StoreFlow.cs |
| 119 | Assets/_Project/Game/TelemetryRelay.cs |
| 120 | Assets/_Project/Game/UnlockFlow.cs |
| 121 | Assets/_Project/Game/WeChatAnalyticsService.cs |
| 122 | Assets/_Project/Gameplay/ActorDudu.cs |
| 123 | Assets/_Project/Gameplay/AmbushBeat.cs |
| 124 | Assets/_Project/Gameplay/Art/GameplayArt.cs |
| 125 | Assets/_Project/Gameplay/BellyWindow.cs |
| 126 | Assets/_Project/Gameplay/BinZone.cs |
| 127 | Assets/_Project/Gameplay/CaptureBurst.cs |
| 128 | Assets/_Project/Gameplay/CarryMouth.cs |
| 129 | Assets/_Project/Gameplay/ChapterEvolveFlow.cs |
| 130 | Assets/_Project/Gameplay/ChapterFinale.cs |
| 131 | Assets/_Project/Gameplay/ChapterOnlooker.cs |
| 132 | Assets/_Project/Gameplay/ChapterOnlookerSelfTest.cs |
| 133 | Assets/_Project/Gameplay/ClusterMilestone.cs |
| 134 | Assets/_Project/Gameplay/DebrisTarget.cs |
| 135 | Assets/_Project/Gameplay/DustTarget.cs |
| 136 | Assets/_Project/Gameplay/EscapeBrake.cs |
| 137 | Assets/_Project/Gameplay/Families/BubbleTarget.cs |
| 138 | Assets/_Project/Gameplay/Families/GhostTarget.cs |
| 139 | Assets/_Project/Gameplay/Families/HeavyTarget.cs |
| 140 | Assets/_Project/Gameplay/Families/MimicTarget.cs |
| 141 | Assets/_Project/Gameplay/Families/PlayBand.cs |
| 142 | Assets/_Project/Gameplay/Families/SparkleTarget.cs |
| 143 | Assets/_Project/Gameplay/Families/SplitterTarget.cs |
| 144 | Assets/_Project/Gameplay/Families/StickyTarget.cs |
| 145 | Assets/_Project/Gameplay/Families/SwarmTarget.cs |
| 146 | Assets/_Project/Gameplay/Front3Fx.cs |
| 147 | Assets/_Project/Gameplay/Front3SuctionGrowth.cs |
| 148 | Assets/_Project/Gameplay/FullChargeCeremony.cs |
| 149 | Assets/_Project/Gameplay/FurTarget.cs |
| 150 | Assets/_Project/Gameplay/GameplayDirtPalette.cs |
| 151 | Assets/_Project/Gameplay/GameplayEscape.cs |
| 152 | Assets/_Project/Gameplay/GameplaySelfTest.cs |
| 153 | Assets/_Project/Gameplay/GameplaySpawnFactory.cs |
| 154 | Assets/_Project/Gameplay/GrayscaleDriver.cs |
| 155 | Assets/_Project/Gameplay/GroundShadow.cs |
| 156 | Assets/_Project/Gameplay/GuideRing.cs |
| 157 | Assets/_Project/Gameplay/HitStop.cs |
| 158 | Assets/_Project/Gameplay/JuiceCurves.cs |
| 159 | Assets/_Project/Gameplay/LandmarkBeacon.cs |
| 160 | Assets/_Project/Gameplay/LevelScope.cs |
| 161 | Assets/_Project/Gameplay/PadInput.cs |
| 162 | Assets/_Project/Gameplay/PointVacuum.cs |
| 163 | Assets/_Project/Gameplay/ScratchTargets.cs |
| 164 | Assets/_Project/Gameplay/ScriptedPointer.cs |
| 165 | Assets/_Project/Gameplay/ScriptedSuctionPilot.cs |
| 166 | Assets/_Project/Gameplay/SignatureArt.cs |
| 167 | Assets/_Project/Gameplay/SignatureTargets.cs |
| 168 | Assets/_Project/Gameplay/SneezeSystem.cs |
| 169 | Assets/_Project/Gameplay/SpawnSpecTable.cs |
| 170 | Assets/_Project/Gameplay/SuctionField.cs |
| 171 | Assets/_Project/Gameplay/SuctionField.Visual.cs |
| 172 | Assets/_Project/Gameplay/SuctionFieldConfig.cs |
| 173 | Assets/_Project/Gameplay/SuctionGuideWiring.cs |
| 174 | Assets/_Project/Gameplay/SuctionTarget.cs |
| 175 | Assets/_Project/Gameplay/SuctionTrail.cs |
| 176 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch07.cs |
| 177 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch08.cs |
| 178 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch09.cs |
| 179 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch10.cs |
| 180 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch11.cs |
| 181 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch12.cs |
| 182 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch13.cs |
| 183 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch14.cs |
| 184 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch15.cs |
| 185 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch16.cs |
| 186 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch17.cs |
| 187 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch18.cs |
| 188 | Assets/_Project/Levels/Campaign/CampaignCatalog.cs |
| 189 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id04_12.cs |
| 190 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id13_21.cs |
| 191 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id22_30.cs |
| 192 | Assets/_Project/Levels/ChapterLore.cs |
| 193 | Assets/_Project/Levels/ContentCatalog.cs |
| 194 | Assets/_Project/Levels/DailyLevelPolicy.cs |
| 195 | Assets/_Project/Levels/Editor/ContentCatalogEditor.cs |
| 196 | Assets/_Project/Levels/Editor/LevelEditorWindow.cs |
| 197 | Assets/_Project/Levels/Generation/BeatInjection.cs |
| 198 | Assets/_Project/Levels/Generation/LevelGenerator.cs |
| 199 | Assets/_Project/Levels/Generation/SignatureInjection.cs |
| 200 | Assets/_Project/Levels/Generation/VarietyInjection.cs |
| 201 | Assets/_Project/Levels/GoalTracker.cs |
| 202 | Assets/_Project/Levels/LevelCatalog.cs |
| 203 | Assets/_Project/Levels/LevelDiag.cs |
| 204 | Assets/_Project/Levels/LevelProgressStore.cs |
| 205 | Assets/_Project/Levels/LevelRules.cs |
| 206 | Assets/_Project/Levels/LevelRunner.cs |
| 207 | Assets/_Project/Levels/LevelSourceResolver.cs |
| 208 | Assets/_Project/Levels/LevelsSelfTest.cs |
| 209 | Assets/_Project/Levels/LevelTimer.cs |
| 210 | Assets/_Project/Levels/ParentKeyGuide.cs |
| 211 | Assets/_Project/Levels/RemainderGuide.cs |
| 212 | Assets/_Project/Levels/Stations/StationAbLayout.cs |
| 213 | Assets/_Project/Levels/Stations/StationCatalog_Station1.cs |
| 214 | Assets/_Project/Levels/Stations/StationCatalog_StationA.cs |
| 215 | Assets/_Project/Levels/Stations/StationCatalog_StationB.cs |
| 216 | Assets/_Project/Levels/Stations/StationCatalog_StationC.cs |
| 217 | Assets/_Project/Levels/Stations/StationCatalog_StationD.cs |
| 218 | Assets/_Project/Levels/Stations/StationCatalog_StationE.cs |
| 219 | Assets/_Project/Levels/Stations/StationCatalog_StationF.cs |
| 220 | Assets/_Project/Levels/Validation/LevelReport.cs |
| 221 | Assets/_Project/Levels/Validation/LevelValidator.cs |
| 222 | Assets/_Project/Levels/WaveDirector.cs |
| 223 | Assets/_Project/Replay/GhostPlayback.cs |
| 224 | Assets/_Project/Replay/PostcardComposer.cs |
| 225 | Assets/_Project/Replay/PosterComposer.cs |
| 226 | Assets/_Project/Replay/ReplayConfig.cs |
| 227 | Assets/_Project/Replay/ReplayRecorder.cs |
| 228 | Assets/_Project/Replay/ReplayRingMath.cs |
| 229 | Assets/_Project/Replay/ReplaySelfTest.cs |
| 230 | Assets/_Project/Replay/ReplayShareService.cs |
| 231 | Assets/_Project/Replay/WanderDot.cs |
| 232 | Assets/_Project/Replay/WeChatShareService.cs |
| 233 | Assets/_Project/Social/ArenaAnchor.cs |
| 234 | Assets/_Project/Social/CloudScoreParser.cs |
| 235 | Assets/_Project/Social/PersistentLeaderboardService.cs |
| 236 | Assets/_Project/Social/ScoreFlow.cs |
| 237 | Assets/_Project/Social/SocialSelfTest.cs |
| 238 | Assets/_Project/Social/StubLeaderboardService.cs |
| 239 | Assets/_Project/Social/TimeService.cs |
| 240 | Assets/_Project/Social/WeChatLeaderboardService.cs |
| 241 | Assets/_Project/Tests/Editor/BVersionSevenShot.cs |
| 242 | Assets/_Project/Tests/Editor/ChapterTurnCapture.cs |
| 243 | Assets/_Project/Tests/Editor/DevRigToggles.cs |
| 244 | Assets/_Project/Tests/Editor/DuduIdleShot.cs |
| 245 | Assets/_Project/Tests/Editor/EditModeSpawnDrive.cs |
| 246 | Assets/_Project/Tests/Editor/EntityProbeGate.cs |
| 247 | Assets/_Project/Tests/Editor/FxGate.cs |
| 248 | Assets/_Project/Tests/Editor/HeadlessRunner.cs |
| 249 | Assets/_Project/Tests/Editor/HeadlessTestAttribute.cs |
| 250 | Assets/_Project/Tests/Editor/NewbieFlowCapture.cs |
| 251 | Assets/_Project/Tests/Editor/O1610MenuShot.cs |
| 252 | Assets/_Project/Tests/Editor/PlayLoopGate.cs |
| 253 | Assets/_Project/Tests/Editor/SettlementCapture.cs |
| 254 | Assets/_Project/Tests/Editor/SweepCapture.cs |
| 255 | Assets/_Project/Tests/Editor/TestAdCopyFamilyFace.cs |
| 256 | Assets/_Project/Tests/Editor/TestAdPolicyFaceVisible.cs |
| 257 | Assets/_Project/Tests/Editor/TestAds.cs |
| 258 | Assets/_Project/Tests/Editor/TestAdsMetrics.cs |
| 259 | Assets/_Project/Tests/Editor/TestArtAssets.cs |
| 260 | Assets/_Project/Tests/Editor/TestAudioAssets.cs |
| 261 | Assets/_Project/Tests/Editor/TestAudioPackageMatrix.cs |
| 262 | Assets/_Project/Tests/Editor/TestBellyMath.cs |
| 263 | Assets/_Project/Tests/Editor/TestBVersionChapterJourney.cs |
| 264 | Assets/_Project/Tests/Editor/TestBVersionEntries.cs |
| 265 | Assets/_Project/Tests/Editor/TestBVersionPortMap.cs |
| 266 | Assets/_Project/Tests/Editor/TestBVersionStoreScreen.cs |
| 267 | Assets/_Project/Tests/Editor/TestChainIntegration.cs |
| 268 | Assets/_Project/Tests/Editor/TestChapterChest.cs |
| 269 | Assets/_Project/Tests/Editor/TestChapterChestUi.cs |
| 270 | Assets/_Project/Tests/Editor/TestChapterEvolveFlow.cs |
| 271 | Assets/_Project/Tests/Editor/TestCheckIn.cs |
| 272 | Assets/_Project/Tests/Editor/TestCheckInUi.cs |
| 273 | Assets/_Project/Tests/Editor/TestCodexAccel.cs |
| 274 | Assets/_Project/Tests/Editor/TestCodexAccelUi.cs |
| 275 | Assets/_Project/Tests/Editor/TestCodexCatalog.cs |
| 276 | Assets/_Project/Tests/Editor/TestCodexFlow.cs |
| 277 | Assets/_Project/Tests/Editor/TestCodexUi.cs |
| 278 | Assets/_Project/Tests/Editor/TestCompanionAds.cs |
| 279 | Assets/_Project/Tests/Editor/TestCompanionFace.cs |
| 280 | Assets/_Project/Tests/Editor/TestCompanionFamilies2.cs |
| 281 | Assets/_Project/Tests/Editor/TestCompanionQi2b.cs |
| 282 | Assets/_Project/Tests/Editor/TestCompanionRoster.cs |
| 283 | Assets/_Project/Tests/Editor/TestCompanionRosterUi.cs |
| 284 | Assets/_Project/Tests/Editor/TestCompanionRuntime.cs |
| 285 | Assets/_Project/Tests/Editor/TestCompanionSeat.cs |
| 286 | Assets/_Project/Tests/Editor/TestCompanionSeat2.cs |
| 287 | Assets/_Project/Tests/Editor/TestCompanionUpgrade.cs |
| 288 | Assets/_Project/Tests/Editor/TestCopyPools.cs |
| 289 | Assets/_Project/Tests/Editor/TestCoreBus.cs |
| 290 | Assets/_Project/Tests/Editor/TestCoreJsonState.cs |
| 291 | Assets/_Project/Tests/Editor/TestCoreRegistry.cs |
| 292 | Assets/_Project/Tests/Editor/TestDailyTask.cs |
| 293 | Assets/_Project/Tests/Editor/TestDailyTaskUi.cs |
| 294 | Assets/_Project/Tests/Editor/TestDoubleReward.cs |
| 295 | Assets/_Project/Tests/Editor/TestEmotionCurve.cs |
| 296 | Assets/_Project/Tests/Editor/TestEvolveRitualFrame.cs |
| 297 | Assets/_Project/Tests/Editor/TestFeatherRevive.cs |
| 298 | Assets/_Project/Tests/Editor/TestFiveBeats.cs |
| 299 | Assets/_Project/Tests/Editor/TestFont.cs |
| 300 | Assets/_Project/Tests/Editor/TestGameplayCapture.cs |
| 301 | Assets/_Project/Tests/Editor/TestInLevelChoiceFlow.cs |
| 302 | Assets/_Project/Tests/Editor/TestJuiceCurves.cs |
| 303 | Assets/_Project/Tests/Editor/TestLevelRules.cs |
| 304 | Assets/_Project/Tests/Editor/TestLevels.cs |
| 305 | Assets/_Project/Tests/Editor/TestLevelSupply.cs |
| 306 | Assets/_Project/Tests/Editor/TestLevelSupplyUi.cs |
| 307 | Assets/_Project/Tests/Editor/TestLevelTimerRearm.cs |
| 308 | Assets/_Project/Tests/Editor/TestMetaProgress.cs |
| 309 | Assets/_Project/Tests/Editor/TestNewbieAttraction.cs |
| 310 | Assets/_Project/Tests/Editor/TestO1610WelcomeBand.cs |
| 311 | Assets/_Project/Tests/Editor/TestOfflineEarnings.cs |
| 312 | Assets/_Project/Tests/Editor/TestOfflineEarningsUi.cs |
| 313 | Assets/_Project/Tests/Editor/TestPaywallGate.cs |
| 314 | Assets/_Project/Tests/Editor/TestPersistence.cs |
| 315 | Assets/_Project/Tests/Editor/TestPrewarmWiring.cs |
| 316 | Assets/_Project/Tests/Editor/TestProductFx.cs |
| 317 | Assets/_Project/Tests/Editor/TestProfileScope.cs |
| 318 | Assets/_Project/Tests/Editor/TestRemainderGuide.cs |
| 319 | Assets/_Project/Tests/Editor/TestReplayMath.cs |
| 320 | Assets/_Project/Tests/Editor/TestReplayPoster.cs |
| 321 | Assets/_Project/Tests/Editor/TestReviveRearm.cs |
| 322 | Assets/_Project/Tests/Editor/TestSfxFamilySounds.cs |
| 323 | Assets/_Project/Tests/Editor/TestSfxSynthClips.cs |
| 324 | Assets/_Project/Tests/Editor/TestShareLanding.cs |
| 325 | Assets/_Project/Tests/Editor/TestSignatureLevels.cs |
| 326 | Assets/_Project/Tests/Editor/TestSocial.cs |
| 327 | Assets/_Project/Tests/Editor/TestSocialCloud.cs |
| 328 | Assets/_Project/Tests/Editor/TestStoreAds.cs |
| 329 | Assets/_Project/Tests/Editor/TestStoreFlow.cs |
| 330 | Assets/_Project/Tests/Editor/TestSuctionFamilies.cs |
| 331 | Assets/_Project/Tests/Editor/TestSweepVerb.cs |
| 332 | Assets/_Project/Tests/Editor/TestSystemUnlocks.cs |
| 333 | Assets/_Project/Tests/Editor/TestTutorialHint.cs |
| 334 | Assets/_Project/Tests/Editor/TestU351BankCleanup.cs |
| 335 | Assets/_Project/Tests/Editor/TestU351BottomRhythm.cs |
| 336 | Assets/_Project/Tests/Editor/TestU351CapsuleWash.cs |
| 337 | Assets/_Project/Tests/Editor/TestU351Density.cs |
| 338 | Assets/_Project/Tests/Editor/TestU351Hitpad.cs |
| 339 | Assets/_Project/Tests/Editor/TestU351StardustSplit.cs |
| 340 | Assets/_Project/Tests/Editor/TestU351Stopgap.cs |
| 341 | Assets/_Project/Tests/Editor/TestU360L4BWalk.cs |
| 342 | Assets/_Project/Tests/Editor/TestU360L4LegacyLayout.cs |
| 343 | Assets/_Project/Tests/Editor/TestU360L4Ui.cs |
| 344 | Assets/_Project/Tests/Editor/TestU360L6B4Combo.cs |
| 345 | Assets/_Project/Tests/Editor/TestU360L6B4Lick.cs |
| 346 | Assets/_Project/Tests/Editor/TestU360L6B5BellyTower.cs |
| 347 | Assets/_Project/Tests/Editor/TestU360L6B5ChallengeStar.cs |
| 348 | Assets/_Project/Tests/Editor/TestU360L6B5PreLevelChoice.cs |
| 349 | Assets/_Project/Tests/Editor/TestU360L6FullPowerStorm.cs |
| 350 | Assets/_Project/Tests/Editor/TestU360L7SweepTeach.cs |
| 351 | Assets/_Project/Tests/Editor/TestU360S3Feel.cs |
| 352 | Assets/_Project/Tests/Editor/TestWaveDirector.cs |
| 353 | Assets/_Project/Tests/Editor/U360L3S3MomentShot.cs |
| 354 | Assets/_Project/Tests/Editor/U360L4CShot.cs |
| 355 | Assets/_Project/Tests/Editor/U360L4WalkShot.cs |
| 356 | Assets/_Project/Tests/Editor/U360L7FtueCapture.cs |
| 357 | Assets/_Project/Tests/Editor/U360LevelTour.cs |
| 358 | Assets/_Project/Tests/Editor/U360StageDiagnostics.cs |
| 359 | Assets/_Project/Tests/Editor/U360SweepShot.cs |
| 360 | Assets/_Project/Tests/Editor/X1958MenuShot.cs |
| 361 | Assets/_Project/Tests/PlayGate/EntityProbeDriver.cs |
| 362 | Assets/_Project/Tests/PlayGate/FxLoopDriver.cs |
| 363 | Assets/_Project/Tests/PlayGate/PlayLoopDriver.cs |
| 364 | Assets/_Project/UI/ArrivalBanner.cs |
| 365 | Assets/_Project/UI/ButtonSquash.cs |
| 366 | Assets/_Project/UI/BVersionPortMap.cs |
| 367 | Assets/_Project/UI/Car/CarLayout.Wing.cs |
| 368 | Assets/_Project/UI/CarLayout.cs |
| 369 | Assets/_Project/UI/ChapterChestScreen.cs |
| 370 | Assets/_Project/UI/ChapterJourney/ChapterJourneyScreen.Car.cs |
| 371 | Assets/_Project/UI/ChapterJourneyScreen.cs |
| 372 | Assets/_Project/UI/ChapterPalette.cs |
| 373 | Assets/_Project/UI/Chest/ChapterChestScreen.Car.cs |
| 374 | Assets/_Project/UI/ChoiceBanner.cs |
| 375 | Assets/_Project/UI/CodexCatalog.cs |
| 376 | Assets/_Project/UI/CodexRevealFx.cs |
| 377 | Assets/_Project/UI/Collection/CollectionCodex.cs |
| 378 | Assets/_Project/UI/Collection/CollectionCompanions.cs |
| 379 | Assets/_Project/UI/Collection/CollectionScreen.Car.cs |
| 380 | Assets/_Project/UI/CollectionScreen.cs |
| 381 | Assets/_Project/UI/CopyPools.cs |
| 382 | Assets/_Project/UI/DailyTask/DailyTaskScreen.Car.cs |
| 383 | Assets/_Project/UI/DailyTaskScreen.cs |
| 384 | Assets/_Project/UI/DuduIdlePlayer.cs |
| 385 | Assets/_Project/UI/FamilyNamePrompt.cs |
| 386 | Assets/_Project/UI/FlyToTarget.cs |
| 387 | Assets/_Project/UI/FrameGeometryProbe.cs |
| 388 | Assets/_Project/UI/FullChargeOverlay.cs |
| 389 | Assets/_Project/UI/FxEvents.cs |
| 390 | Assets/_Project/UI/HealthNoticeScreen.cs |
| 391 | Assets/_Project/UI/Hud/CompanionChargeRing.cs |
| 392 | Assets/_Project/UI/Hud/CompanionRecharge.cs |
| 393 | Assets/_Project/UI/Hud/Front3HudPanel.cs |
| 394 | Assets/_Project/UI/Hud/InGameHud.Boosters.cs |
| 395 | Assets/_Project/UI/Hud/ParentKeyHudPanel.cs |
| 396 | Assets/_Project/UI/ICommerceService.cs |
| 397 | Assets/_Project/UI/InGameHud.cs |
| 398 | Assets/_Project/UI/Leaderboard/LeaderboardScreen.Car.cs |
| 399 | Assets/_Project/UI/LeaderboardScreen.cs |
| 400 | Assets/_Project/UI/MainMenuScreen.cs |
| 401 | Assets/_Project/UI/Menu/MenuChromeKit.cs |
| 402 | Assets/_Project/UI/Menu/MenuEntryBar.cs |
| 403 | Assets/_Project/UI/Menu/MenuProgressBadges.cs |
| 404 | Assets/_Project/UI/NumberRoll.cs |
| 405 | Assets/_Project/UI/OfflineEarningsPopup.cs |
| 406 | Assets/_Project/UI/ParentGatePanel.cs |
| 407 | Assets/_Project/UI/Paywall/PaywallScreen.Car.cs |
| 408 | Assets/_Project/UI/Paywall/PaywallScreen.Flow.cs |
| 409 | Assets/_Project/UI/Paywall/PaywallScreen.Helpers.cs |
| 410 | Assets/_Project/UI/PaywallScreen.cs |
| 411 | Assets/_Project/UI/ProfileManagerPanel.cs |
| 412 | Assets/_Project/UI/ProfileScreen.cs |
| 413 | Assets/_Project/UI/Result/ResultScreen.Car.cs |
| 414 | Assets/_Project/UI/Result/ResultScreen.Postcard.cs |
| 415 | Assets/_Project/UI/ResultScreen.cs |
| 416 | Assets/_Project/UI/SafeAreaFitter.cs |
| 417 | Assets/_Project/UI/ScreenRouter.cs |
| 418 | Assets/_Project/UI/SneezeButton.cs |
| 419 | Assets/_Project/UI/Store/StoreScreen.Car.cs |
| 420 | Assets/_Project/UI/StoreCatalog.cs |
| 421 | Assets/_Project/UI/StoreScreen.cs |
| 422 | Assets/_Project/UI/StubCommerceService.cs |
| 423 | Assets/_Project/UI/TutorialHint.cs |
| 424 | Assets/_Project/UI/UIArt.cs |
| 425 | Assets/_Project/UI/UiBob.cs |
| 426 | Assets/_Project/UI/UiDrift.cs |
| 427 | Assets/_Project/UI/UiEasing.cs |
| 428 | Assets/_Project/UI/UiFade.cs |
| 429 | Assets/_Project/UI/UiFlash.cs |
| 430 | Assets/_Project/UI/UiKeySubmit.cs |
| 431 | Assets/_Project/UI/UIRoot.cs |
| 432 | Assets/_Project/UI/Wardrobe/WardrobeScreen.Car.cs |
| 433 | Assets/_Project/UI/WardrobeScreen.cs |
| 434 | production/reports/p0-quarantine-2026-09-17/BellyWindow.cs |
| 435 | production/reports/p0-quarantine-2026-09-17/HapticPulse.cs |
| 436 | production/reports/p0-quarantine-2026-09-17/JuiceCurves.cs |
| 437 | production/reports/p0-quarantine-2026-09-17/MetaFlow.cs |
| 438 | production/reports/p0-quarantine-2026-09-17/MetaStore.cs |
| 439 | production/reports/p0-quarantine-2026-09-17/ShareLandingGate.cs |
| 440 | production/reports/p0-quarantine-2026-09-17/SignatureArt.cs |
| 441 | production/reports/p0-quarantine-2026-09-17/SuctionTrail.cs |
| 442 | production/reports/p0-quarantine-2026-09-17/TestBellyMath.cs |
| 443 | production/reports/p0-quarantine-2026-09-17/TestJuiceCurves.cs |
| 444 | production/reports/p0-quarantine-2026-09-17/TestMetaProgress.cs |
| 445 | production/reports/p0-quarantine-2026-09-17/TestShareLanding.cs |
| 446 | production/reports/p0-quarantine-2026-09-17/UiBob.cs |
| 447 | production/reports/p0-quarantine-2026-09-17/UiFade.cs |
| 448 | production/reports/p0-quarantine-2026-09-17/WardrobeScreen.cs |
