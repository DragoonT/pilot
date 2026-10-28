ui#262 fix(dashboard): header Pool / org / Last shipped from real sources; StatCard variants; Delivered = allowance t
   Post-merge review of PR #252 (epic #240, U2 stat cards) found the header bound to dashboard fields no backend sends. `httpAdapter.toDashboard` reads `orgName`, 
ui#263 fix(usage): platform-key tenants — USD fields are absent on the wire after console#427; hide cost tiles, type 
   
ui#264 fix(dashboard): one activity chart; calendar-aligned 1D/7D/30D buckets with dates in the tooltip; request limi
   Post-merge review of PR #254 (U3 activity chart) found three defects. Review: https://github.com/qf-studio/pilot-console-ui/pull/254#issuecomment-6343528680
ui#265 fix(chat): ChatView renders confirmation events again — mobile Chat tab lost approve/decline cards in #246
   PR #246 (U9 Research page) replaced the `/chat` view. `/chat` is also the mobile Chat tab (`MobileTabBar.vue` → `{ name: 'chat' }`), which `ChatWindow` served w
ui#266 chat: the RESEARCH / DOCS mode pills send a mode nothing reads — hide them or forward mode end to end (decisio
   PR #246 added `ChatMode` (`research` | `docs`) and two mode pills in `ResearchComposer.vue`. `httpAdapter.sendChatMessage` posts `mode`, but the console's `send
ui#271 fix(context): Memory card reads the docs-tree counts; Graph card stays — until the daemon summary read; Contex
   Post-merge review of PR #255 (ui#243) is REQUEST CHANGES: https://github.com/qf-studio/pilot-console-ui/pull/255#issuecomment-6345261735. The Memory card render
ui#272 fix(queue): no fabricated Board group and no per-card execution fetch until the console serves project, parent
   Post-merge review of the U4 epic (PR #259 + PR #261, ui#242) is REQUEST CHANGES: https://github.com/qf-studio/pilot-console-ui/pull/261#issuecomment-6345262343.
