{
 "ts": "2026-11-12T03:08:32",
 "line": "fluxverse",
 "faces_total": 12,
 "tally": {
  "在役": 6,
  "受阻": 4,
  "待裁": 1,
  "空白": 1
 },
 "blocked": [
  {
   "id": "owners",
   "name": "主体责任",
   "status": "受阻",
   "next": "至少让 BLUEPRINT 有可读投影（摘要件）进总控仓"
  },
  {
   "id": "space",
   "name": "空间与美术正典",
   "status": "受阻",
   "next": "48 包授权=CEO 物理件；本机看不到仓，需投影"
  },
  {
   "id": "residents",
   "name": "居民（脑在、身缺）",
   "status": "受阻",
   "next": "接入链路必须先出 20 居民的端到端回执，再谈规模"
  },
  {
   "id": "product-gate",
   "name": "产品闸链（最薄的一环）",
   "status": "空白",
   "next": "先定义四闸的可执行判据（每条一句话+一个命令），再谈 build"
  },
  {
   "id": "observability",
   "name": "主控可见性（治理盲区）",
   "status": "受阻",
   "next": "城市每日投影（指标快照+包体成熟度+体征变化）写入总控仓，主控只读这一份"
  }
 ],
 "faces": [
  {
   "id": "strategy",
   "name": "定位与正身",
   "status": "在役",
   "owner": "中枢",
   "claim": "硅基城=集团唯一战略主线；元宙(FluxVerse)=集团直属独立载体，Biggame 受托承建",
   "evidence_missing": [],
   "trigger": "AI.md 里 FluxVerse 段被改，或出现第二个'城市'立案",
   "next": "无",
   "gaps": []
  },
  {
   "id": "boundary",
   "name": "2D/3D 边界（最容易误读的一条）",
   "status": "在役",
   "owner": "中枢",
   "claim": "游戏线（Biggame）硬约束=全 2D、无 3D 场景相机；城市线=lowpoly 3D polygon。两者是不同载体，不互相推翻",
   "evidence_missing": [],
   "trigger": "任何人拿「CEO 说全部 2D」去否决城市 3D，或反过来把 3D 塞进小游戏",
   "next": "任何涉维度争论，先引 AI.md 对应行，不许凭记忆转述",
   "gaps": []
  },
  {
   "id": "owners",
   "name": "主体责任",
   "status": "受阻",
   "owner": "CPH4 × BigLife",
   "claim": "CPH4=城市规划+技术/架构底层唯一问责；Biggame=主建；BigLife=生命/人口；BigHouse=安家；BigDomain=商业化",
   "evidence_missing": [],
   "trigger": "任一 BLUEPRINT 在本机不可读时，主控不得对该面下结论",
   "next": "至少让 BLUEPRINT 有可读投影（摘要件）进总控仓",
   "gaps": []
  },
  {
   "id": "space",
   "name": "空间与美术正典",
   "status": "受阻",
   "owner": "Biggame（受托）",
   "claim": "lowpoly 3D polygon + Synty 48 包 + SiliconToon 卡通渲染 + URP 三档；日夜=真实北京时间、真天气",
   "evidence_missing": [],
   "trigger": "48 包商用授权未采购时，任何对外演示都不得使用这些资产",
   "next": "48 包授权=CEO 物理件；本机看不到仓，需投影",
   "gaps": []
  },
  {
   "id": "vitals",
   "name": "生命体征 12 条",
   "status": "在役",
   "owner": "CPH4 × BigLife",
   "claim": "城=硅基超个体、居民=智能细胞；12 条体征=器官是否在役（机制可回放），不是完成度宣称",
   "evidence_missing": [],
   "trigger": "任一体征从✓掉到✗，或有人用'有生命'替代体征表作结论",
   "next": "体征表需按月复核，不能一次通过就长期引用",
   "gaps": []
  },
  {
   "id": "residents",
   "name": "居民（脑在、身缺）",
   "status": "受阻",
   "owner": "BigLife",
   "claim": "人口 census 万台级在 BigLife（脑）；3D 接入为零（身），T-FV-147 长期 open",
   "evidence_missing": [],
   "trigger": "出现'居民已进城'的宣称但拿不出接入回执",
   "next": "接入链路必须先出 20 居民的端到端回执，再谈规模",
   "gaps": []
  },
  {
   "id": "bus",
   "name": "事件与状态总线",
   "status": "在役",
   "owner": "CPH4",
   "claim": "world-events.jsonl 为总线、events-registry 唯一仲裁；外部只读轮询 10s，禁直写引擎态",
   "evidence_missing": [],
   "trigger": "有人为了'快'直接写引擎状态文件",
   "next": "无",
   "gaps": []
  },
  {
   "id": "workflow",
   "name": "工作流四环与载体",
   "status": "待裁",
   "owner": "中枢",
   "claim": "规划轮→施工轮→活性轮→产品轮；载体=DevLoop(施工)+BigLife-OSLoop(生命)，禁建第三条循环",
   "evidence_missing": [],
   "trigger": "出现新的常驻循环/新台账体系",
   "next": "DevLoop 长期 keepdown 状态下，施工轮由谁推进需 CEO 一句话定",
   "gaps": []
  },
  {
   "id": "product-gate",
   "name": "产品闸链（最薄的一环）",
   "status": "空白",
   "owner": "Biggame",
   "claim": "真包实跑/首启 30 秒/性能档/可玩性盲评=四项全空白；设计智力不缺，缺完成度",
   "evidence_missing": [],
   "trigger": "任何'城市可玩'的说法，必须先过这四闸",
   "next": "先定义四闸的可执行判据（每条一句话+一个命令），再谈 build",
   "gaps": []
  },
  {
   "id": "cockpit",
   "name": "观景舱/驾驶舱",
   "status": "在役",
   "owner": "CPH4",
   "claim": "看(L0全景)→查(L1内景)→令(L2台账)；可视化三件套法；每个动画必须对应一次真实 AI 行为（禁装饰性动画）",
   "evidence_missing": [],
   "trigger": "出现好看但不对应真实行为的动画",
   "next": "无",
   "gaps": []
  },
  {
   "id": "compliance",
   "name": "合规与红线",
   "status": "在役",
   "owner": "合规席",
   "claim": "AIGC 标识（参观端开门帧）、T0 禁语（意识/感受/灵魂/数字永生/意识上传/电子人格）、真金永禁全自动、密钥不入 git、城市 UI 禁金融行情视觉",
   "evidence_missing": [],
   "trigger": "任何对外参观内容上线前",
   "next": "无",
   "gaps": []
  },
  {
   "id": "observability",
   "name": "主控可见性（治理盲区）",
   "status": "受阻",
   "owner": "中枢",
   "claim": "城市是唯一战略主线，但其载体仓（FluxVerse）与人口库（BigLife）都是独立仓且不在主控机上——主控无法实测任何城市成果，只能引用台账",
   "evidence_missing": [],
   "trigger": "每次汇报城市进度时",
   "next": "城市每日投影（指标快照+包体成熟度+体征变化）写入总控仓，主控只读这一份",
   "gaps": []
  }
 ],
 "verdict": "GAPS"
}