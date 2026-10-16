### Project
- [2026-10-16 16:00:21] [2026-10-16 15:5x] [C-02 wave-F] 工作树批量回退族（多窗脏树 stash 回灌·mtime 同秒=指纹）对账正法：①分诊器=git hash-object vs rev-list --objects 历史集比对——命中历史 blob=纯陈旧→checkout 归位；无命中=本地独有新稿→采纳上链；双向各缺=逐 hunk 并集手术；②禁整树 checkout/提交（bc34c07 实证：41 归位+81 采纳+3 并集）；③B/C 机与本机产物竞速时以各线最新交付批定新旧。How to apply：遇「多件 M 且 mtime 同秒」先按回退覆写分诊，勿按内容盲判。
