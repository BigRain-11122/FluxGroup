#!/usr/bin/env bash
# flux-server bootstrap v1.1 — 自建商业后端一键部署（IaC）
# 溯源：ledger P-2026-09-24-47 实验室件①·建造书=cph4/research/R-20260924-infra-6-selfhost.md
# v1.1 (2026-09-24)：城市运行适配扩展（CEO 令「适配硅基生命体城市运行」·架构件=cph4/research/R-20260924-server-city.md §6）
#   ——城市公开数据 :ro 挂载（结构性禁写=三律①）+ citysync 只读拉取通道（三律②）。
# 治理：cph4/server-governance.md（最小攻击面/密钥律/备份/监控）
# 用法：在全新 Ubuntu 22.04/24.04 LTS（腾讯云轻量）以 root 运行：
#   bash bootstrap-server.sh            # 全量：基线+docker+栈+探针客户端
#   bash bootstrap-server.sh --baseline-only   # 仅安全基线（备案期最小态）
# 幂等：可重复运行（每步自检已有则跳过）；失败即停（set -e）并输出行号。
# 密钥律：本脚本永不含密钥——所有密钥经 /etc/fluxvault/（见 server-governance §二）。

set -euo pipefail
MODE="${1:-full}"
FLUXDIR=/opt/fluxstack
VAULT=/etc/fluxvault
log(){ echo "[flux-bootstrap] $(date '+%H:%M:%S') $*"; }

# ---------- §一 最小攻击面基线（server-governance §一）----------
baseline(){
  log "安全基线开始"
  # 系统更新（安全补丁）
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq && apt-get -yqq upgrade >/dev/null
  # SSH 加固：禁 root 直登+禁密码（若 /etc/ssh/sshd_config.d 可用）
  cat > /etc/ssh/sshd_config.d/99-flux-hardening.conf <<'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
X11Forwarding no
MaxAuthTries 3
EOF
  systemctl reload sshd || systemctl reload ssh || true
  # 防火墙：默认拒绝入站，仅放行 443 + 有限 SSH
  if command -v ufw >/dev/null; then
    ufw --force reset >/dev/null
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 443/tcp comment 'https only'
    ufw allow OpenSSH comment 'ssh keyed'
    ufw --force enable >/dev/null
  else
    log "WARN: ufw 不存在，跳过防火墙（记录待证项）"
  fi
  # fail2ban（SSH 暴破防护）
  apt-get -yqq install fail2ban >/dev/null 2>&1 || log "WARN: fail2ban 安装失败（非致命）"
  systemctl enable --now fail2ban 2>/dev/null || true
  # 时区+时间同步（日志审计前提）
  timedatectl set-timezone Asia/Shanghai 2>/dev/null || true
  apt-get -yqq install chrony >/dev/null 2>&1 && systemctl enable --now chrony 2>/dev/null || true
  # 密钥目录（600·root）
  mkdir -p "$VAULT" && chmod 700 "$VAULT"
  log "安全基线完成：443-only + SSH 加固 + fail2ban + Asia/Shanghai"
}

# ---------- docker + 栈 ----------
stack(){
  log "docker 安装"
  if ! command -v docker >/dev/null; then
    apt-get -yqq install ca-certificates curl >/dev/null
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq && apt-get -yqq install docker-ce docker-compose-plugin >/dev/null
  fi
  systemctl enable --now docker
  mkdir -p "$FLUXDIR" && cd "$FLUXDIR"
  # compose 骨架（业务镜像由 BigDomain 后续替换占位名 flux-api）
  if [ ! -f docker-compose.yml ]; then
    cat > docker-compose.yml <<'EOF'
# fluxstack v1 — 建造书 infra-6 §2（占位镜像：BigDomain 业务 API 到位后替换）
services:
  nginx:
    image: nginx:stable-alpine
    restart: unless-stopped
    ports: ["443:443"]
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on: [api]
  api:
    image: ghcr.io/fluxgroup/flux-api:placeholder   # TODO(BigDomain): 业务镜像
    restart: unless-stopped
    env_file: ["/etc/fluxvault/api.env"]
    volumes:
      - /var/lib/fluxstack/data:/data               # SQLite WAL + jsonl 导出
      - /opt/fluxcity:/data/city:ro                 # 城市公开数据只读挂载（server-city 三律①：结构性禁写）
  danmaku:
    image: ghcr.io/fluxgroup/flux-danmaku:placeholder # TODO(BigStream/DevLoop): 弹幕回流 worker
    restart: unless-stopped
    env_file: ["/etc/fluxvault/danmaku.env"]
EOF
    mkdir -p nginx/conf.d /var/lib/fluxstack/data
    cat > nginx/conf.d/flux.conf <<'EOF'
# TLS 由 certbot 首跑后填充（备案过+域名解析后执行 certbot --nginx）
server {
  listen 443 ssl;
  server_name _;                                   # TODO: 域名就位后替换
  # ssl_certificate /etc/letsencrypt/live/DOMAIN/fullchain.pem;
  # ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;
  location / { proxy_pass http://api:8000; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
  location /ws { proxy_pass http://api:8000; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }
}
EOF
  fi
  # 快照与备份 cron：每日 03:20 数据导出打包 + docker prune
  cat > /etc/cron.d/flux-maint <<'EOF'
20 3 * * * root cd /var/lib/fluxstack/data && tar czf flux-data-$(date +\%u).tgz *.jsonl *.db 2>/dev/null; docker system prune -f >/dev/null
EOF
  log "栈骨架就位（镜像占位待业务接入）"
}

# ---------- citysync：城市公开数据只读拉取通道（R-20260924-server-city §2/§6·三律②） ----------
# 数据流=单向：bm-a 生成（快照包/日档案/census/pools）→ git push → 本机 10min pull → /data/city 只读投喂。
# 本机永不回写城市仓（禁写 world/ = P-43 案 2 单写者律；回城走 api 的 inbox 摘要通道）。
citysync(){
  log "城市只读通道：目录+cron 骨架（首次 clone=runbook 手动段·deploy key 物理件就位后）"
  mkdir -p /opt/fluxcity/fluxverse /opt/fluxcity/biglife
  # 首次 clone runbook（密钥永禁入 git·走 /etc/fluxvault）：
  #   1) 双仓 deploy key 各一枚（GitHub 同一 deploy key 不可跨仓）→ /etc/fluxvault/id_fluxverse / id_biglife
  #   2) /root/.ssh/config 配 Host 别名（github-fluxverse / github-biglife）指 IdentityFile
  #   3) git clone git@github-fluxverse:BigRain-11122/FluxVerse.git /opt/fluxcity/fluxverse
  #      git clone git@github-biglife:BigRain-11122/Biglife.git /opt/fluxcity/biglife
  # clone 完成前 cron 空转无害（[ -d .git ] 守卫跳过）
  cat > /etc/cron.d/flux-citysync <<'EOF'
# city read-only sync (server-city §2): 10min guarded pull, never writes back
*/10 * * * * root for d in /opt/fluxcity/fluxverse /opt/fluxcity/biglife; do [ -d "$d/.git" ] && git -C "$d" pull --ff-only -q; done
EOF
  log "citysync 就位（/opt/fluxcity 双仓目录 + cron */10 只读拉取）"
}

# ---------- 探针客户端（monitoring：外部探针打点回 bm-a 的通道留位） ----------
monitor(){
  log "监控留位（外部探针由 bm-a 侧配置 5min 打点——本机只保健康检查端点）"
  mkdir -p "$FLUXDIR/health" || true
}

case "$MODE" in
  --baseline-only) baseline ;;
  *) baseline; stack; citysync; monitor ;;
esac
log "完成。验收清单：1) ufw status 应只有 443/SSH  2) sshd -T | grep -E 'permitrootlogin|passwordauth'  3) ls $VAULT  4) ls /opt/fluxcity（clone 后 city 面启用）"
